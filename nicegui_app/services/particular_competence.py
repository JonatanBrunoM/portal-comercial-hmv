from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from nicegui import ui

from nicegui_app.data.supabase_client import rest_select
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


_STORAGE_KEY = "particular_active_competence"


@dataclass(frozen=True, slots=True)
class ParticularCompetence:
    id: str
    reference_date: str
    year: int
    month: int
    status: str

    @property
    def label(self) -> str:
        names = (
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        )
        return f"{names[self.month - 1]}/{self.year}"

    @property
    def status_label(self) -> str:
        return {
            "OPEN": "Aberta",
            "IN_CLOSING": "Em fechamento",
            "CLOSED": "Fechada",
            "NOT_CONFIGURED": "Sem dados cadastrados",
        }.get(self.status, self.status.replace("_", " ").title())


def _check_access(access: ParticularAccess) -> None:
    if not access.can_read or not access.profile_id:
        raise ParticularAccessDenied("Sem autorização para consultar competências do Particular.")


def list_particular_competences(access: ParticularAccess) -> list[ParticularCompetence]:
    _check_access(access)
    rows = rest_select(
        "particular_competencies",
        select="id,competence_year,competence_month,status",
        params={"order": "competence_year.desc,competence_month.desc", "limit": "120"},
        timeout=20.0,
    )
    result: list[ParticularCompetence] = []
    for row in rows:
        try:
            year = int(row.get("competence_year"))
            month = int(row.get("competence_month"))
            reference = date(year, month, 1).isoformat()
        except (TypeError, ValueError):
            continue
        result.append(
            ParticularCompetence(
                id=str(row.get("id") or ""),
                reference_date=reference,
                year=year,
                month=month,
                status=str(row.get("status") or "OPEN").strip().upper(),
            )
        )
    # Disponibiliza o calendário completo de 2026 sem criar linhas artificiais
    # no banco. Meses não cadastrados ficam vazios e não são considerados fechados.
    existing = {(item.year, item.month) for item in result}
    for month in range(1, 13):
        if (2026, month) not in existing:
            result.append(ParticularCompetence(
                id="", reference_date=date(2026, month, 1).isoformat(),
                year=2026, month=month, status="NOT_CONFIGURED",
            ))
    return sorted(result, key=lambda item: item.reference_date, reverse=True)


def resolve_active_competence(access: ParticularAccess) -> tuple[ParticularCompetence, list[ParticularCompetence]]:
    competences = list_particular_competences(access)
    if not competences:
        raise RuntimeError("Nenhuma competência do Particular foi cadastrada.")

    stored = str(ui.context.client.storage.get(_STORAGE_KEY) or "").strip()
    active = next((item for item in competences if item.reference_date == stored), None)
    if active is None:
        active = next((item for item in competences if item.status == "IN_CLOSING"), next((item for item in competences if item.id), competences[0]))
        ui.context.client.storage[_STORAGE_KEY] = active.reference_date
    return active, competences


def set_active_competence(reference_date: str, competences: list[ParticularCompetence]) -> ParticularCompetence:
    normalized = str(reference_date or "").strip()
    active = next((item for item in competences if item.reference_date == normalized), None)
    if active is None:
        raise ValueError("Competência selecionada não está disponível.")
    ui.context.client.storage[_STORAGE_KEY] = active.reference_date
    return active


@dataclass(frozen=True, slots=True)
class ParticularSourceHealth:
    source: str
    label: str
    status: str
    filename: str | None
    processed_at: str | None
    records_processed: int
    records_error: int
    detail: str
    metadata: dict[str, Any]


def _completed_rows(table_name: str, *, select: str, order_field: str) -> list[dict[str, Any]]:
    return rest_select(
        table_name,
        select=select,
        params={"status": "eq.COMPLETED", "order": f"{order_field}.desc", "limit": "100"},
        timeout=20.0,
    )


def get_particular_competence_sources(
    access: ParticularAccess,
    competence: ParticularCompetence,
) -> list[ParticularSourceHealth]:
    """Consolida as fontes existentes que sustentam a competência ativa."""
    _check_access(access)
    reference = competence.reference_date[:7]

    xml_rows = _completed_rows(
        "particular_import_batches",
        select="id,source_type,source_filename,status,records_processed,records_error,completed_at,metadata",
        order_field="completed_at",
    )
    xml = next((
        row for row in xml_rows
        if str(row.get("source_type") or "").strip().upper() == "XML"
        and str((row.get("metadata") or {}).get("competence") or "")[:7] == reference
    ), None)

    grade_rows = _completed_rows(
        "particular_sheet_syncs",
        select="id,spreadsheet_id,status,rows_total,errors_count,finished_at,metadata",
        order_field="finished_at",
    )
    grade = next(
        (
            row
            for row in grade_rows
            if str(
                (row.get("metadata") or {}).get("competence") or ""
            )[:7] == reference
        ),
        None,
    )

    evolution_rows = _completed_rows(
        "particular_admin_evolution_imports",
        select="id,source_filename,reference_month,status,records_processed,records_error,completed_at,metadata",
        order_field="completed_at",
    )
    # Meses encontrados nas linhas não comprovam a competência do arquivo.
    # Exigimos a competência declarada para evitar associação indevida.
    evolution = next((
        row for row in evolution_rows
        if str(row.get("reference_month") or "")[:7] == reference
    ), None)

    # O relatório MV não possui coluna própria de competência.
    # Só o vinculamos ao mês quando o metadado o declara explicitamente.
    mv_rows = _completed_rows(
        "particular_mv_account_imports",
        select="id,source_filename,status,records_processed,records_error,completed_at,metadata",
        order_field="completed_at",
    )
    mv_accounts = next((
        row for row in mv_rows
        if str((row.get("metadata") or {}).get("competence") or "")[:7] == reference
    ), None)

    def health(*, source: str, label: str, row: dict[str, Any] | None,
               processed_key: str, error_key: str, date_key: str, detail: str) -> ParticularSourceHealth:
        if row is None:
            return ParticularSourceHealth(
                source=source, label=label, status="MISSING", filename=None,
                processed_at=None, records_processed=0, records_error=0,
                detail="Fonte concluída ainda não identificada para esta leitura.", metadata={},
            )
        return ParticularSourceHealth(
            source=source, label=label, status="AVAILABLE",
            filename=str(row.get("source_filename") or "").strip() or None,
            processed_at=str(row.get(date_key) or "").strip() or None,
            records_processed=int(row.get(processed_key) or 0),
            records_error=int(row.get(error_key) or 0),
            detail=detail, metadata=dict(row.get("metadata") or {}),
        )

    xml_metadata = dict((xml or {}).get("metadata") or {})
    xml_end = str(xml_metadata.get("end_date") or "").strip()
    evolution_metadata = dict((evolution or {}).get("metadata") or {})
    months_found = [str(value) for value in evolution_metadata.get("months_found") or []]

    return [
        health(
            source="XML", label="XML dos orçamentos", row=xml,
            processed_key="records_processed", error_key="records_error", date_key="completed_at",
            detail=f"Cobertura informada até {xml_end}" if xml_end else f"Competência {reference}",
        ),
        health(
            source="GRADES", label="Grades operacionais", row=grade,
            processed_key="rows_total", error_key="errors_count", date_key="finished_at",
            detail="Última sincronização operacional concluída",
        ),
        health(
            source="MV_ACCOUNTS", label="Relatório de Contas MV", row=mv_accounts,
            processed_key="records_processed", error_key="records_error", date_key="completed_at",
            detail=f"Competência declarada {reference}",
        ),
        health(
            source="EVOLUTION", label="Relatório de evolução", row=evolution,
            processed_key="records_processed", error_key="records_error", date_key="completed_at",
            detail=f"Cobertura identificada até {max(months_found)}" if months_found else f"Competência {reference}",
        ),
    ]


@dataclass(frozen=True, slots=True)
class ParticularClosingSnapshot:
    competence: str
    budgets_total: int
    operational_resolved: int
    future_maturation: int
    human_action: int
    financially_closed: int
    financially_closed_with_value: int
    financially_open: int
    financially_unknown: int
    original_value_total: float
    realized_value_total: float
    comparable_original_value: float
    comparable_difference: float


def get_particular_closing_snapshot(
    access: ParticularAccess,
    competence: ParticularCompetence,
) -> ParticularClosingSnapshot:
    """Raio-X factual da maturidade da coorte, sem persistir nem reclassificar casos."""
    _check_access(access)
    from nicegui_app.services.particular_work_queue import list_particular_work_queue

    rows = list_particular_work_queue(competence=competence.reference_date)
    next_reference = date(
        competence.year + (1 if competence.month == 12 else 0),
        1 if competence.month == 12 else competence.month + 1,
        1,
    ).isoformat()

    operational_resolved = 0
    future_maturation = 0
    human_action = 0
    financially_closed = 0
    financially_closed_with_value = 0
    financially_open = 0
    financially_unknown = 0
    original_value_total = 0.0
    realized_value_total = 0.0
    comparable_original_value = 0.0

    closed_statuses = {"CLOSED", "FECHADA", "FECHADO"}
    open_statuses = {"OPEN", "ABERTA", "ABERTO", "IN_PROGRESS", "PROCESSING"}

    for row in rows:
        original = float(row.get("original_value") or 0)
        original_value_total += original

        operational_date = str(
            row.get("first_operational_date")
            or row.get("last_observed_operational_date")
            or ""
        )[:10]
        group = str(row.get("work_group") or "").strip().upper()
        action = str(row.get("work_action") or "").strip().upper()

        if operational_date and operational_date >= next_reference:
            future_maturation += 1
        elif action in {"RESOLVIDO", "RESOLVED"} or group in {
            "RESOLVIDO", "INVESTIGACAO_CONCLUIDA"
        }:
            operational_resolved += 1
        else:
            human_action += 1

        account_status = str(row.get("account_status") or "").strip().upper()
        final_raw = row.get("confirmed_final_value")
        if final_raw is None:
            final_raw = row.get("mv_account_value")
        has_final = final_raw not in (None, "")

        if account_status in closed_statuses:
            financially_closed += 1
            if has_final:
                final_value = float(final_raw)
                financially_closed_with_value += 1
                realized_value_total += final_value
                comparable_original_value += original
        elif account_status in open_statuses:
            financially_open += 1
        else:
            financially_unknown += 1

    return ParticularClosingSnapshot(
        competence=competence.reference_date,
        budgets_total=len(rows),
        operational_resolved=operational_resolved,
        future_maturation=future_maturation,
        human_action=human_action,
        financially_closed=financially_closed,
        financially_closed_with_value=financially_closed_with_value,
        financially_open=financially_open,
        financially_unknown=financially_unknown,
        original_value_total=original_value_total,
        realized_value_total=realized_value_total,
        comparable_original_value=comparable_original_value,
        comparable_difference=realized_value_total - comparable_original_value,
    )


@dataclass(frozen=True, slots=True)
class ParticularClosingBreakdown:
    work_groups: list[dict[str, Any]]
    financial_by_operational_stage: list[dict[str, Any]]
    group_financial_matrix: list[dict[str, Any]]
    closed_with_value: int
    closed_without_value: int
    future_without_financial_state: int
    human_action_without_financial_state: int


def get_particular_closing_breakdown(
    access: ParticularAccess,
    competence: ParticularCompetence,
) -> ParticularClosingBreakdown:
    """Decompõe o diagnóstico mensal para validar as regras antes do fechamento definitivo."""
    _check_access(access)
    from nicegui_app.services.particular_work_queue import list_particular_work_queue

    rows = list_particular_work_queue(competence=competence.reference_date)
    next_reference = date(
        competence.year + (1 if competence.month == 12 else 0),
        1 if competence.month == 12 else competence.month + 1,
        1,
    ).isoformat()
    closed_statuses = {"CLOSED", "FECHADA", "FECHADO"}

    def stage(row: dict[str, Any]) -> str:
        operational_date = str(
            row.get("first_operational_date")
            or row.get("last_observed_operational_date")
            or ""
        )[:10]
        group = str(row.get("work_group") or "").strip().upper()
        action = str(row.get("work_action") or "").strip().upper()
        if operational_date and operational_date >= next_reference:
            return "FUTURE"
        if action in {"RESOLVIDO", "RESOLVED"} or group in {
            "RESOLVIDO", "INVESTIGACAO_CONCLUIDA"
        }:
            return "RESOLVED"
        return "HUMAN_ACTION"

    group_counts: dict[tuple[str, str, str], int] = {}
    cross_counts: dict[tuple[str, str], int] = {}
    group_financial_counts: dict[tuple[str, str, str, str], int] = {}
    closed_with_value = 0
    closed_without_value = 0
    future_without_financial_state = 0
    human_action_without_financial_state = 0

    for row in rows:
        current_stage = stage(row)
        group = str(row.get("work_group") or "SEM_GRUPO").strip().upper()
        action = str(row.get("work_action") or "SEM_ACAO").strip().upper()
        reason = str(row.get("work_reason") or "").strip()
        group_key = (current_stage, group, action)
        group_counts[group_key] = group_counts.get(group_key, 0) + 1

        account_status = str(row.get("account_status") or "").strip().upper()
        final_raw = row.get("confirmed_final_value")
        if final_raw is None:
            final_raw = row.get("mv_account_value")
        if account_status in closed_statuses:
            financial_state = "CLOSED_WITH_VALUE" if final_raw not in (None, "") else "CLOSED_WITHOUT_VALUE"
            if final_raw not in (None, ""):
                closed_with_value += 1
            else:
                closed_without_value += 1
        elif account_status:
            financial_state = account_status
        else:
            financial_state = "UNKNOWN"

        cross_key = (current_stage, financial_state)
        cross_counts[cross_key] = cross_counts.get(cross_key, 0) + 1
        matrix_key = (current_stage, group, action, financial_state)
        group_financial_counts[matrix_key] = group_financial_counts.get(matrix_key, 0) + 1
        if current_stage == "FUTURE" and financial_state == "UNKNOWN":
            future_without_financial_state += 1
        if current_stage == "HUMAN_ACTION" and financial_state == "UNKNOWN":
            human_action_without_financial_state += 1

    work_groups = [
        {"stage": stage_name, "work_group": group, "work_action": action, "count": count}
        for (stage_name, group, action), count in sorted(
            group_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    financial_by_operational_stage = [
        {"stage": stage_name, "financial_state": financial_state, "count": count}
        for (stage_name, financial_state), count in sorted(
            cross_counts.items(), key=lambda item: (item[0][0], -item[1], item[0][1])
        )
    ]
    group_financial_matrix = [
        {
            "stage": stage_name,
            "work_group": group,
            "work_action": action,
            "financial_state": financial_state,
            "count": count,
        }
        for (stage_name, group, action, financial_state), count in sorted(
            group_financial_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    return ParticularClosingBreakdown(
        work_groups=work_groups,
        financial_by_operational_stage=financial_by_operational_stage,
        group_financial_matrix=group_financial_matrix,
        closed_with_value=closed_with_value,
        closed_without_value=closed_without_value,
        future_without_financial_state=future_without_financial_state,
        human_action_without_financial_state=human_action_without_financial_state,
    )


@dataclass(frozen=True, slots=True)
class ParticularOccurrenceSignalInventory:
    total_occurrences: int
    budgets_with_occurrences: int
    signals: list[dict[str, Any]]
    by_work_group: list[dict[str, Any]]
    evidence_combinations: list[dict[str, Any]]


def get_particular_occurrence_signal_inventory(
    access: ParticularAccess,
    competence: ParticularCompetence,
) -> ParticularOccurrenceSignalInventory:
    """Inventaria sinais textuais das grades sem inferir conclusão de negócio."""
    _check_access(access)
    from nicegui_app.services.particular_work_queue import list_particular_work_queue

    queue_rows = list_particular_work_queue(competence=competence.reference_date)
    budget_ids = sorted({
        str(row.get("budget_id"))
        for row in queue_rows
        if row.get("budget_id")
    })
    if not budget_ids:
        return ParticularOccurrenceSignalInventory(0, 0, [], [], [])

    occurrences: list[dict[str, Any]] = []
    for start in range(0, len(budget_ids), 80):
        chunk = budget_ids[start:start + 80]
        occurrences.extend(rest_select(
            "particular_occurrences",
            select="budget_id,contact_status,patient_confirmation,evolution_status,occurrence_status,negative_type_value,notes_original",
            params={"budget_id": "in.(" + ",".join(chunk) + ")", "limit": "10000"},
            timeout=30.0,
        ))

    budget_groups = {str(row.get('budget_id')): str(row.get('work_group') or 'SEM_GRUPO') for row in queue_rows if row.get('budget_id')}
    group_budgets: dict[tuple[str, str, str], set[str]] = {}
    combinations: dict[tuple[str, str], set[str]] = {}
    occurrence_counts: dict[tuple[str, str], int] = {}
    budget_sets: dict[tuple[str, str], set[str]] = {}
    signal_fields = (
        "contact_status", "patient_confirmation", "evolution_status",
        "occurrence_status", "negative_type_value", "notes_original",
    )
    for occurrence in occurrences:
        budget_id = str(occurrence.get("budget_id") or "")
        flags = [field for field in ('contact_status', 'patient_confirmation', 'evolution_status') if str(occurrence.get(field) or '').strip().lower() == 'ok']
        combo = ' + '.join(flags) if flags else 'SEM_OK_REGISTRADO'
        combinations.setdefault((budget_groups.get(budget_id, 'SEM_GRUPO'), combo), set()).add(budget_id)
        for field in signal_fields:
            value = str(occurrence.get(field) or "").strip()
            if not value:
                continue
            key = (field, value)
            occurrence_counts[key] = occurrence_counts.get(key, 0) + 1
            budget_sets.setdefault(key, set()).add(budget_id)
            if field != 'notes_original':
                group_budgets.setdefault((budget_groups.get(budget_id, 'SEM_GRUPO'), field, value), set()).add(budget_id)

    signals = [
        {
            "field": field,
            "value": value,
            "occurrences": occurrence_counts[(field, value)],
            "budgets": len(budget_set),
        }
        for (field, value), budget_set in sorted(
            budget_sets.items(),
            key=lambda item: (-len(item[1]), item[0][0], item[0][1]),
        )
    ]
    return ParticularOccurrenceSignalInventory(
        total_occurrences=len(occurrences),
        budgets_with_occurrences=len({
            str(row.get("budget_id"))
            for row in occurrences
            if row.get("budget_id")
        }),
        signals=signals,
        evidence_combinations=[
            {'work_group': group, 'combination': combo, 'budgets': len(ids)}
            for (group, combo), ids in sorted(combinations.items(), key=lambda item: (-len(item[1]), item[0]))
        ],
        by_work_group=[
            {'work_group': group, 'field': field, 'value': value, 'budgets': len(ids)}
            for (group, field, value), ids in sorted(group_budgets.items(), key=lambda item: (-len(item[1]), item[0]))
        ],
    )


@dataclass(frozen=True, slots=True)
class ParticularFinancialEvidenceLevels:
    closed_confirmed_value: int
    closed_without_confirmed_value: int
    special_or_inconclusive: int
    no_financial_evidence: int
    other_financial_state: int
    review_required: int
    auto_resolved: int
    manually_resolved: int


def get_particular_financial_evidence_levels(
    access: ParticularAccess,
    competence: ParticularCompetence,
) -> ParticularFinancialEvidenceLevels:
    """Classificação financeira diagnóstica da coorte; não infere realização assistencial."""
    _check_access(access)
    from nicegui_app.services.particular_work_queue import list_particular_work_queue

    counts = {
        "closed_confirmed_value": 0,
        "closed_without_confirmed_value": 0,
        "special_or_inconclusive": 0,
        "no_financial_evidence": 0,
        "other_financial_state": 0,
        "review_required": 0,
        "auto_resolved": 0,
        "manually_resolved": 0,
    }
    for row in list_particular_work_queue(competence=competence.reference_date):
        status = str(row.get("account_status") or "").strip().upper()
        automation = str(row.get("account_automation_status") or "").strip().upper()
        confirmed = row.get("confirmed_final_value")
        if status == "CLOSED":
            key = "closed_confirmed_value" if confirmed is not None else "closed_without_confirmed_value"
        elif status in {"SPECIAL_OUTCOME", "INCONCLUSIVE"}:
            key = "special_or_inconclusive"
        elif not status:
            key = "no_financial_evidence"
        else:
            key = "other_financial_state"
        counts[key] += 1
        if automation == "REVIEW_REQUIRED":
            counts["review_required"] += 1
        elif automation == "AUTO_RESOLVED":
            counts["auto_resolved"] += 1
        elif automation == "MANUALLY_RESOLVED":
            counts["manually_resolved"] += 1
    return ParticularFinancialEvidenceLevels(**counts)


@dataclass(frozen=True, slots=True)
class ParticularFinancialOperationalCross:
    closed_budgets: int
    with_operational_evidence: int
    without_operational_evidence: int
    with_attendance_number: int
    without_attendance_number: int
    trajectory_review: int
    by_group: list[dict[str, Any]]


def get_particular_financial_operational_cross(
    access: ParticularAccess,
    competence: ParticularCompetence,
) -> ParticularFinancialOperationalCross:
    """Cruza conta fechada com sinais operacionais já consolidados na fila.

    Evidência operacional não equivale a procedimento realizado. Não grava dados.
    """
    _check_access(access)
    from nicegui_app.services.particular_work_queue import list_particular_work_queue

    closed = [
        row for row in list_particular_work_queue(competence=competence.reference_date)
        if str(row.get("account_status") or "").strip().upper() == "CLOSED"
    ]
    with_evidence = sum(1 for row in closed if row.get("has_operational_evidence") is True)
    with_attendance = sum(1 for row in closed if row.get("attendance_number") is not None)
    review = sum(1 for row in closed if row.get("trajectory_requires_review") is True)
    groups: dict[tuple[str, str], int] = {}
    for row in closed:
        key = (
            str(row.get("work_group") or "SEM_GRUPO"),
            str(row.get("operational_state") or "SEM_ESTADO_OPERACIONAL"),
        )
        groups[key] = groups.get(key, 0) + 1
    return ParticularFinancialOperationalCross(
        closed_budgets=len(closed),
        with_operational_evidence=with_evidence,
        without_operational_evidence=len(closed) - with_evidence,
        with_attendance_number=with_attendance,
        without_attendance_number=len(closed) - with_attendance,
        trajectory_review=review,
        by_group=[
            {"work_group": group, "operational_state": state, "budgets": count}
            for (group, state), count in sorted(groups.items(), key=lambda item: (-item[1], item[0]))
        ],
    )

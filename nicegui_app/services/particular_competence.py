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
    return result


def resolve_active_competence(access: ParticularAccess) -> tuple[ParticularCompetence, list[ParticularCompetence]]:
    competences = list_particular_competences(access)
    if not competences:
        raise RuntimeError("Nenhuma competência do Particular foi cadastrada.")

    stored = str(ui.context.client.storage.get(_STORAGE_KEY) or "").strip()
    active = next((item for item in competences if item.reference_date == stored), None)
    if active is None:
        active = next((item for item in competences if item.status == "IN_CLOSING"), competences[0])
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
    grade = grade_rows[0] if grade_rows else None

    evolution_rows = _completed_rows(
        "particular_admin_evolution_imports",
        select="id,source_filename,reference_month,status,records_processed,records_error,completed_at,metadata",
        order_field="completed_at",
    )
    evolution = next((
        row for row in evolution_rows
        if (
            str(row.get("reference_month") or "")[:7] == reference
            or reference in {
                str(value)[:7]
                for value in ((row.get("metadata") or {}).get("months_found") or [])
            }
        )
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

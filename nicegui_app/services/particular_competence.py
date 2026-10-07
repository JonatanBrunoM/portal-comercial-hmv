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

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

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.contatos_repository import (
    get_contato,
    list_contatos,
    list_operadoras_for_contatos,
    list_planos_for_contatos,
)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@dataclass(frozen=True, slots=True)
class ContatoPreview:
    contact_id: str
    code: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    sector: str
    purpose: str
    contact_type: str
    contact: str
    responsible: str
    schedule: str
    observations: str
    status: str


def _maps() -> tuple[dict[str, str], dict[str, str]]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto", "nome")
        for row in list_operadoras_for_contatos()
        if _text(row, "id")
    }
    plans = {
        _text(row, "id"): _text(row, "nome_padronizado", "nome")
        for row in list_planos_for_contatos()
        if _text(row, "id")
    }
    return operators, plans


def _from_record(
    row: dict[str, Any],
    operators: dict[str, str],
    plans: dict[str, str],
) -> ContatoPreview:
    operator_id = _text(row, "operadora_id")
    plan_id = _text(row, "plano_id")

    return ContatoPreview(
        contact_id=_text(row, "id"),
        code=_text(row, "codigo"),
        operator_id=operator_id,
        operator_name=operators.get(operator_id, "Operadora não informada"),
        plan_id=plan_id,
        plan_name=plans.get(plan_id, ""),
        sector=_text(row, "nome_setor"),
        purpose=_text(row, "finalidade"),
        contact_type=_text(row, "tipo"),
        contact=_text(row, "contato"),
        responsible=_text(row, "responsavel"),
        schedule=_text(row, "horario_atendimento"),
        observations=_text(row, "observacoes"),
        status=_text(row, "status") or "Não informado",
    )


def get_contatos_preview() -> list[ContatoPreview]:
    operators, plans = _maps()
    return [
        _from_record(row, operators, plans)
        for row in list_contatos()
    ]


def get_contato_detail(contact_id: str) -> ContatoPreview | None:
    record = get_contato(contact_id)
    if record is None:
        return None

    operators, plans = _maps()
    return _from_record(record, operators, plans)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.operadoras_repository import (
    get_operadora,
    list_operadoras,
    list_planos_by_operadora,
)


def _text(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@dataclass(frozen=True, slots=True)
class OperadoraPreview:
    operator_id: str
    code: str
    name: str
    short_name: str
    status: str
    observations: str
    logo_url: str
    site_url: str


@dataclass(frozen=True, slots=True)
class PlanoPreview:
    plan_id: str
    code: str
    name: str
    standardized_name: str
    plan_type: str
    summary: str
    status: str


@dataclass(frozen=True, slots=True)
class OperadoraDetail:
    operator: OperadoraPreview
    plans: tuple[PlanoPreview, ...]


def _operator_from_record(record: dict[str, Any]) -> OperadoraPreview:
    name = _text(record, "nome") or "Operadora sem nome"
    return OperadoraPreview(
        operator_id=_text(record, "id"),
        code=_text(record, "codigo"),
        name=name,
        short_name=_text(record, "nome_curto") or name,
        status=_text(record, "status") or "Não informado",
        observations=_text(record, "observacoes"),
        logo_url=_text(record, "logo_url"),
        site_url=_text(record, "site_url"),
    )


def get_operadoras_preview() -> list[OperadoraPreview]:
    return [
        _operator_from_record(record)
        for record in list_operadoras()
    ]


def get_operadora_detail(
    operator_id: str,
) -> OperadoraDetail | None:
    record = get_operadora(operator_id)
    if record is None:
        return None

    plans = tuple(
        PlanoPreview(
            plan_id=_text(row, "id"),
            code=_text(row, "codigo"),
            name=_text(row, "nome") or "Plano sem nome",
            standardized_name=_text(row, "nome_padronizado"),
            plan_type=_text(row, "tipo_plano"),
            summary=_text(row, "observacao_resumida"),
            status=_text(row, "status") or "Não informado",
        )
        for row in list_planos_by_operadora(operator_id)
    )

    return OperadoraDetail(
        operator=_operator_from_record(record),
        plans=plans,
    )

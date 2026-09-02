from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.operadoras_repository import (
    get_operadora,
    list_autorizacoes_by_operadora,
    list_carteiras_by_operadora,
    list_coberturas_by_operadora,
    list_comunicados_by_operadora,
    list_contatos_by_operadora,
    list_contingencias_by_operadora,
    list_dicas_by_operadora,
    list_documentos_by_operadora,
    list_elegibilidade_by_operadora,
    list_operadoras,
    list_planos_by_operadora,
    list_portais_by_operadora,
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
class OperadoraDetail:
    operator: OperadoraPreview
    planos: tuple[dict[str, Any], ...]
    portais: tuple[dict[str, Any], ...]
    elegibilidade: tuple[dict[str, Any], ...]
    documentos: tuple[dict[str, Any], ...]
    autorizacoes: tuple[dict[str, Any], ...]
    coberturas: tuple[dict[str, Any], ...]
    contatos: tuple[dict[str, Any], ...]
    contingencias: tuple[dict[str, Any], ...]
    dicas: tuple[dict[str, Any], ...]
    comunicados: tuple[dict[str, Any], ...]
    carteiras: tuple[dict[str, Any], ...]


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
    return [_operator_from_record(row) for row in list_operadoras()]


def get_operadora_detail(operator_id: str) -> OperadoraDetail | None:
    record = get_operadora(operator_id)
    if record is None:
        return None

    return OperadoraDetail(
        operator=_operator_from_record(record),
        planos=tuple(list_planos_by_operadora(operator_id)),
        portais=tuple(list_portais_by_operadora(operator_id)),
        elegibilidade=tuple(list_elegibilidade_by_operadora(operator_id)),
        documentos=tuple(list_documentos_by_operadora(operator_id)),
        autorizacoes=tuple(list_autorizacoes_by_operadora(operator_id)),
        coberturas=tuple(list_coberturas_by_operadora(operator_id)),
        contatos=tuple(list_contatos_by_operadora(operator_id)),
        contingencias=tuple(list_contingencias_by_operadora(operator_id)),
        dicas=tuple(list_dicas_by_operadora(operator_id)),
        comunicados=tuple(list_comunicados_by_operadora(operator_id)),
        carteiras=tuple(list_carteiras_by_operadora(operator_id)),
    )

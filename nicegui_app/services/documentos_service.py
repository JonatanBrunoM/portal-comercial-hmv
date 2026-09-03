from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.documentos_repository import (
    get_documento,
    list_documentos,
    list_locais_for_documentos,
    list_operadoras_for_documentos,
    list_planos_for_documentos,
    list_tipos_atendimento_for_documentos,
)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@dataclass(frozen=True, slots=True)
class DocumentoPreview:
    document_id: str
    code: str
    name: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    local_id: str
    local_name: str
    attendance_type: str
    required: bool
    file_format: str
    validity_days: int | None
    guidance: str
    observations: str
    file_url: str
    status: str


def _maps() -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto", "nome")
        for row in list_operadoras_for_documentos()
        if _text(row, "id")
    }
    plans = {
        _text(row, "id"): _text(row, "nome_padronizado", "nome")
        for row in list_planos_for_documentos()
        if _text(row, "id")
    }
    locals_map = {
        _text(row, "id"): _text(row, "nome")
        for row in list_locais_for_documentos()
        if _text(row, "id")
    }
    attendance_types = {
        _text(row, "id"): _text(row, "nome")
        for row in list_tipos_atendimento_for_documentos()
        if _text(row, "id")
    }
    return operators, plans, locals_map, attendance_types


def _validity(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _from_record(
    row: dict[str, Any],
    operators: dict[str, str],
    plans: dict[str, str],
    locals_map: dict[str, str],
    attendance_types: dict[str, str],
) -> DocumentoPreview:
    operator_id = _text(row, "operadora_id")
    plan_id = _text(row, "plano_id")
    local_id = _text(row, "local_id")
    attendance_type_id = _text(row, "tipo_atendimento_id")

    return DocumentoPreview(
        document_id=_text(row, "id"),
        code=_text(row, "codigo"),
        name=_text(row, "nome") or "Documento sem nome",
        operator_id=operator_id,
        operator_name=operators.get(operator_id, "Operadora não informada"),
        plan_id=plan_id,
        plan_name=plans.get(plan_id, ""),
        local_id=local_id,
        local_name=locals_map.get(local_id, ""),
        attendance_type=attendance_types.get(attendance_type_id, _text(row, "tipo_atendimento")),
        required=bool(row.get("obrigatorio")),
        file_format=_text(row, "formato"),
        validity_days=_validity(row.get("validade_dias")),
        guidance=_text(row, "orientacao"),
        observations=_text(row, "observacoes"),
        file_url=_text(row, "arquivo_url"),
        status=_text(row, "status") or "Não informado",
    )


def get_documentos_preview() -> list[DocumentoPreview]:
    operators, plans, locals_map, attendance_types = _maps()
    return [
        _from_record(row, operators, plans, locals_map, attendance_types)
        for row in list_documentos()
    ]


def get_documento_detail(document_id: str) -> DocumentoPreview | None:
    record = get_documento(document_id)
    if record is None:
        return None

    operators, plans, locals_map, attendance_types = _maps()
    return _from_record(record, operators, plans, locals_map, attendance_types)

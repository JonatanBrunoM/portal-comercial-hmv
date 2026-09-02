from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from nicegui_app.repositories.documentos_admin_repository import (
    append_documento_audit,
    create_documento,
    get_documento_admin,
    list_documentos_admin,
    list_locais_admin,
    list_operadoras_admin,
    list_planos_admin,
    list_tipos_atendimento_admin,
    update_documento,
)


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "sim", "yes"}


def _int_or_none(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None

    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError("Validade deve ser informada em dias, usando um número inteiro.")

    if number < 0:
        raise ValueError("Validade em dias não pode ser negativa.")

    return number


@dataclass(frozen=True, slots=True)
class AdminDocumento:
    record_id: str
    code: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    location_id: str
    location_name: str
    attendance_type_id: str
    attendance_type_name: str
    name: str
    required: bool
    file_format: str
    validity_days: int | None
    guidance: str
    notes: str
    file_url: str
    status: str


def get_document_reference_data() -> tuple[
    dict[str, str],
    dict[str, tuple[str, str]],
    dict[str, str],
    dict[str, str],
]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto") or _text(row, "nome")
        for row in list_operadoras_admin()
    }
    plans = {
        _text(row, "id"): (
            _text(row, "operadora_id"),
            _text(row, "nome_padronizado") or _text(row, "nome"),
        )
        for row in list_planos_admin()
    }
    locations = {
        _text(row, "id"): _text(row, "nome")
        for row in list_locais_admin()
    }
    attendance_types = {
        _text(row, "id"): _text(row, "nome")
        for row in list_tipos_atendimento_admin()
    }

    return operators, plans, locations, attendance_types


def get_admin_documentos() -> list[AdminDocumento]:
    operators, plans, locations, attendance_types = get_document_reference_data()

    documents: list[AdminDocumento] = []
    for row in list_documentos_admin():
        plan_id = _text(row, "plano_id")
        plan_data = plans.get(plan_id, ("", ""))

        validity_value = row.get("validade_dias")
        try:
            validity_days = int(validity_value) if validity_value is not None else None
        except (TypeError, ValueError):
            validity_days = None

        documents.append(
            AdminDocumento(
                record_id=_text(row, "id"),
                code=_text(row, "codigo"),
                operator_id=_text(row, "operadora_id"),
                operator_name=operators.get(
                    _text(row, "operadora_id"),
                    "Operadora não informada",
                ),
                plan_id=plan_id,
                plan_name=plan_data[1],
                location_id=_text(row, "local_id"),
                location_name=locations.get(_text(row, "local_id"), ""),
                attendance_type_id=_text(row, "tipo_atendimento_id"),
                attendance_type_name=attendance_types.get(
                    _text(row, "tipo_atendimento_id"),
                    "",
                ),
                name=_text(row, "nome"),
                required=_bool(row.get("obrigatorio")),
                file_format=_text(row, "formato"),
                validity_days=validity_days,
                guidance=_text(row, "orientacao"),
                notes=_text(row, "observacoes"),
                file_url=_text(row, "arquivo_url"),
                status=_text(row, "status") or "Ativo",
            )
        )

    return documents


def _validate_url(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "Informe um link de arquivo válido iniciando com http:// ou https://."
        )

    return value


def save_documento(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str,
    location_id: str,
    attendance_type_id: str,
    name: str,
    required: bool,
    file_format: str,
    validity_days: Any,
    guidance: str,
    notes: str,
    file_url: str,
    status: str,
    actor: dict,
) -> None:
    operator_id = operator_id.strip()
    name = name.strip()
    status = status.strip()

    if not operator_id:
        raise ValueError("Selecione a operadora.")

    if not name:
        raise ValueError("Informe o nome do documento.")

    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    operators, plans, locations, attendance_types = get_document_reference_data()

    if operator_id not in operators:
        raise ValueError("Operadora inválida.")

    if plan_id:
        plan = plans.get(plan_id)
        if not plan:
            raise ValueError("Plano inválido.")
        if plan[0] and plan[0] != operator_id:
            raise ValueError(
                "O plano selecionado não pertence à operadora informada."
            )

    if location_id and location_id not in locations:
        raise ValueError("Local de atendimento inválido.")

    if attendance_type_id and attendance_type_id not in attendance_types:
        raise ValueError("Tipo de atendimento inválido.")

    payload = {
        "codigo": code.strip() or None,
        "operadora_id": operator_id,
        "plano_id": plan_id.strip() or None,
        "local_id": location_id.strip() or None,
        "tipo_atendimento_id": attendance_type_id.strip() or None,
        "nome": name,
        "obrigatorio": bool(required),
        "formato": file_format.strip() or None,
        "validade_dias": _int_or_none(validity_days),
        "orientacao": guidance.strip() or None,
        "observacoes": notes.strip() or None,
        "arquivo_url": _validate_url(file_url),
        "status": status,
    }

    previous = get_documento_admin(record_id) if record_id else None
    saved = (
        update_documento(record_id, payload)
        if record_id
        else create_documento(payload)
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento do documento.")

    try:
        append_documento_audit(
            actor_id=str(actor.get("id") or "") or None,
            action=(
                "Atualização de documento"
                if record_id
                else "Cadastro de documento"
            ),
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        pass

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from nicegui_app.auth.admin_access import require_current_admin

from nicegui_app.repositories.cadastros_admin_repository import (
    append_admin_audit,
    create_operadora,
    create_plano,
    get_operadora_admin,
    get_plano_admin,
    list_operadoras_admin,
    list_planos_admin,
    update_operadora,
    update_plano,
)



logger = logging.getLogger(__name__)

def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()



def _validate_url(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "Informe uma URL válida iniciando com http:// ou https://."
        )

    return value

@dataclass(frozen=True, slots=True)
class AdminOperadora:
    record_id: str
    code: str
    name: str
    short_name: str
    status: str
    site_url: str
    notes: str


@dataclass(frozen=True, slots=True)
class AdminPlano:
    record_id: str
    code: str
    operator_id: str
    operator_name: str
    name: str
    standardized_name: str
    plan_type: str
    status: str
    summary: str


def get_admin_operadoras() -> list[AdminOperadora]:
    return [
        AdminOperadora(
            record_id=_text(row, "id"),
            code=_text(row, "codigo"),
            name=_text(row, "nome"),
            short_name=_text(row, "nome_curto"),
            status=_text(row, "status") or "Ativo",
            site_url=_text(row, "site_url"),
            notes=_text(row, "observacoes"),
        )
        for row in list_operadoras_admin()
    ]


def get_admin_planos() -> list[AdminPlano]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto") or _text(row, "nome")
        for row in list_operadoras_admin()
    }
    return [
        AdminPlano(
            record_id=_text(row, "id"),
            code=_text(row, "codigo"),
            operator_id=_text(row, "operadora_id"),
            operator_name=operators.get(_text(row, "operadora_id"), "Operadora não informada"),
            name=_text(row, "nome"),
            standardized_name=_text(row, "nome_padronizado"),
            plan_type=_text(row, "tipo_plano"),
            status=_text(row, "status") or "Ativo",
            summary=_text(row, "observacao_resumida"),
        )
        for row in list_planos_admin()
    ]


def save_operadora(
    *,
    record_id: str | None,
    code: str,
    name: str,
    short_name: str,
    status: str,
    site_url: str,
    notes: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)

    name = name.strip()
    short_name = short_name.strip()
    code = code.strip()
    status = status.strip()

    if not name:
        raise ValueError("Informe o nome da operadora.")
    if not short_name:
        raise ValueError("Informe o nome curto da operadora.")
    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    payload = {
        "codigo": code or None,
        "nome": name,
        "nome_curto": short_name,
        "status": status,
        "site_url": _validate_url(site_url),
        "observacoes": notes.strip() or None,
    }

    previous = get_operadora_admin(record_id) if record_id else None
    saved = update_operadora(record_id, payload) if record_id else create_operadora(payload)
    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento da operadora.")

    try:
        append_admin_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action="Atualização de operadora" if record_id else "Cadastro de operadora",
            entity="operadoras",
            entity_id=str(saved.get("id") or record_id or ""),
            description="Cadastro de operadora alterado pela Administração.",
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")


def save_plano(
    *,
    record_id: str | None,
    operator_id: str,
    code: str,
    name: str,
    standardized_name: str,
    plan_type: str,
    status: str,
    summary: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)

    operator_id = operator_id.strip()
    name = name.strip()
    standardized_name = standardized_name.strip()

    if not operator_id:
        raise ValueError("Selecione a operadora.")
    if not name:
        raise ValueError("Informe o nome do plano.")
    if not standardized_name:
        raise ValueError("Informe o nome padronizado.")
    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    payload = {
        "operadora_id": operator_id,
        "codigo": code.strip() or None,
        "nome": name,
        "nome_padronizado": standardized_name,
        "tipo_plano": plan_type.strip() or None,
        "observacao_resumida": summary.strip() or None,
        "status": status,
    }

    previous = get_plano_admin(record_id) if record_id else None
    saved = update_plano(record_id, payload) if record_id else create_plano(payload)
    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento do plano.")

    try:
        append_admin_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action="Atualização de plano" if record_id else "Cadastro de plano",
            entity="planos",
            entity_id=str(saved.get("id") or record_id or ""),
            description="Cadastro de plano alterado pela Administração.",
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from nicegui_app.auth.admin_access import require_current_admin

from nicegui_app.repositories.portais_admin_repository import (
    append_portal_audit, create_portal, get_portal_admin,
    list_locais_admin, list_operadoras_admin, list_planos_admin,
    list_portais_admin, update_portal,
)


logger = logging.getLogger(__name__)

def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()

def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "sim", "yes"}

@dataclass(frozen=True, slots=True)
class AdminPortal:
    record_id: str
    code: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    location_id: str
    location_name: str
    name: str
    portal_type: str
    url: str
    requires_login: bool
    access_instruction: str
    general_tip: str
    notes: str
    status: str

def get_portal_reference_data() -> tuple[dict[str, str], dict[str, tuple[str, str]], dict[str, str]]:
    operators = {
        _text(r, "id"): _text(r, "nome_curto") or _text(r, "nome")
        for r in list_operadoras_admin()
    }
    plans = {
        _text(r, "id"): (_text(r, "operadora_id"), _text(r, "nome_padronizado") or _text(r, "nome"))
        for r in list_planos_admin()
    }
    locations = {_text(r, "id"): _text(r, "nome") for r in list_locais_admin()}
    return operators, plans, locations

def get_admin_portais() -> list[AdminPortal]:
    operators, plans, locations = get_portal_reference_data()
    result = []
    for row in list_portais_admin():
        pid = _text(row, "plano_id")
        plan_data = plans.get(pid, ("", ""))
        result.append(AdminPortal(
            record_id=_text(row, "id"),
            code=_text(row, "codigo"),
            operator_id=_text(row, "operadora_id"),
            operator_name=operators.get(_text(row, "operadora_id"), "Operadora não informada"),
            plan_id=pid,
            plan_name=plan_data[1],
            location_id=_text(row, "local_id"),
            location_name=locations.get(_text(row, "local_id"), ""),
            name=_text(row, "nome"),
            portal_type=_text(row, "tipo"),
            url=_text(row, "url"),
            requires_login=_bool(row.get("exige_login")),
            access_instruction=_text(row, "instrucao_acesso"),
            general_tip=_text(row, "dica_geral_acesso"),
            notes=_text(row, "observacoes"),
            status=_text(row, "status") or "Ativo",
        ))
    return result

def _validate_url(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Informe uma URL válida iniciando com http:// ou https://.")
    return value

def save_portal(*, record_id: str | None, code: str, operator_id: str,
                plan_id: str, location_id: str, name: str, portal_type: str,
                url: str, requires_login: bool, access_instruction: str,
                general_tip: str, notes: str, status: str, actor: dict) -> None:
    actor = require_current_admin(actor)

    operator_id = operator_id.strip()
    name = name.strip()
    if not operator_id:
        raise ValueError("Selecione a operadora.")
    if not name:
        raise ValueError("Informe o nome do portal.")
    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    operators, plans, _ = get_portal_reference_data()
    if operator_id not in operators:
        raise ValueError("Operadora inválida.")
    if plan_id:
        plan = plans.get(plan_id)
        if not plan:
            raise ValueError("Plano inválido.")
        if plan[0] and plan[0] != operator_id:
            raise ValueError("O plano selecionado não pertence à operadora informada.")

    payload = {
        "codigo": code.strip() or None,
        "operadora_id": operator_id,
        "plano_id": plan_id.strip() or None,
        "local_id": location_id.strip() or None,
        "nome": name,
        "tipo": portal_type.strip() or None,
        "url": _validate_url(url),
        "exige_login": bool(requires_login),
        "instrucao_acesso": access_instruction.strip() or None,
        "dica_geral_acesso": general_tip.strip() or None,
        "observacoes": notes.strip() or None,
        "status": status,
    }
    previous = get_portal_admin(record_id) if record_id else None
    saved = update_portal(record_id, payload) if record_id else create_portal(payload)
    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento do portal.")
    try:
        append_portal_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action="Atualização de portal" if record_id else "Cadastro de portal",
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")

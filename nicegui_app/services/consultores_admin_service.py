from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Any

from nicegui_app.auth.admin_access import require_current_admin

from nicegui_app.repositories.consultores_admin_repository import (
    append_admin_audit,
    create_carteira,
    create_consultor,
    get_carteira_admin,
    get_consultor_admin,
    list_carteiras_admin,
    list_consultores_admin,
    list_operadoras_admin,
    list_planos_admin,
    update_carteira,
    update_consultor,
)



logger = logging.getLogger(__name__)

def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


@dataclass(frozen=True, slots=True)
class AdminConsultor:
    record_id: str
    code: str
    name: str
    job_title: str
    email: str
    phone: str
    notes: str
    status: str


@dataclass(frozen=True, slots=True)
class AdminCarteira:
    record_id: str
    consultant_id: str
    consultant_name: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    role: str
    notes: str
    status: str


def get_consultant_reference_data() -> tuple[
    dict[str, str],
    dict[str, tuple[str, str]],
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

    return operators, plans


def get_admin_consultores() -> list[AdminConsultor]:
    return [
        AdminConsultor(
            record_id=_text(row, "id"),
            code=_text(row, "codigo"),
            name=_text(row, "nome"),
            job_title=_text(row, "cargo"),
            email=_text(row, "email"),
            phone=_text(row, "telefone"),
            notes=_text(row, "observacoes"),
            status=_text(row, "status") or "Ativo",
        )
        for row in list_consultores_admin()
    ]


def get_admin_carteiras(
    consultants: list[AdminConsultor] | None = None,
) -> list[AdminCarteira]:
    consultants = consultants or get_admin_consultores()
    consultant_names = {
        item.record_id: item.name
        for item in consultants
    }
    operators, plans = get_consultant_reference_data()

    wallets: list[AdminCarteira] = []
    for row in list_carteiras_admin():
        plan_id = _text(row, "plano_id")
        plan_data = plans.get(plan_id, ("", ""))

        wallets.append(
            AdminCarteira(
                record_id=_text(row, "id"),
                consultant_id=_text(row, "consultor_id"),
                consultant_name=consultant_names.get(
                    _text(row, "consultor_id"),
                    "Consultor não informado",
                ),
                operator_id=_text(row, "operadora_id"),
                operator_name=operators.get(
                    _text(row, "operadora_id"),
                    "Operadora não informada",
                ),
                plan_id=plan_id,
                plan_name=plan_data[1],
                role=_text(row, "papel"),
                notes=_text(row, "observacoes"),
                status=_text(row, "status") or "Ativo",
            )
        )

    return wallets


def save_consultor(
    *,
    record_id: str | None,
    code: str,
    name: str,
    job_title: str,
    email: str,
    phone: str,
    notes: str,
    status: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)

    name = name.strip()
    email = email.strip()
    status = status.strip()

    if not name:
        raise ValueError("Informe o nome do consultor.")

    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    if email and ("@" not in email or email.startswith("@") or email.endswith("@")):
        raise ValueError("Informe um e-mail válido.")

    payload = {
        "codigo": code.strip() or None,
        "nome": name,
        "cargo": job_title.strip() or None,
        "email": email or None,
        "telefone": phone.strip() or None,
        "observacoes": notes.strip() or None,
        "status": status,
    }

    previous = get_consultor_admin(record_id) if record_id else None
    saved = (
        update_consultor(record_id, payload)
        if record_id
        else create_consultor(payload)
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento do consultor.")

    try:
        append_admin_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action=(
                "Atualização de consultor"
                if record_id
                else "Cadastro de consultor"
            ),
            entity="consultores",
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")


def save_carteira(
    *,
    record_id: str | None,
    consultant_id: str,
    operator_id: str,
    plan_id: str,
    role: str,
    notes: str,
    status: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)

    consultant_id = consultant_id.strip()
    operator_id = operator_id.strip()
    status = status.strip()

    if not consultant_id:
        raise ValueError("Selecione o consultor.")

    if not operator_id:
        raise ValueError("Selecione a operadora.")

    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    consultants = {
        item.record_id: item
        for item in get_admin_consultores()
    }
    operators, plans = get_consultant_reference_data()

    if consultant_id not in consultants:
        raise ValueError("Consultor inválido.")

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

    payload = {
        "consultor_id": consultant_id,
        "operadora_id": operator_id,
        "plano_id": plan_id.strip() or None,
        "papel": role.strip() or None,
        "observacoes": notes.strip() or None,
        "status": status,
    }

    previous = get_carteira_admin(record_id) if record_id else None
    saved = (
        update_carteira(record_id, payload)
        if record_id
        else create_carteira(payload)
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento da carteira.")

    try:
        append_admin_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action=(
                "Atualização de carteira"
                if record_id
                else "Cadastro de carteira"
            ),
            entity="carteiras",
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")

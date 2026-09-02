from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.contatos_admin_repository import (
    append_contato_audit,
    create_contato,
    get_contato_admin,
    list_contatos_admin,
    list_operadoras_admin,
    list_planos_admin,
    update_contato,
)


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


@dataclass(frozen=True, slots=True)
class AdminContato:
    record_id: str
    code: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    department: str
    purpose: str
    contact_type: str
    contact: str
    responsible: str
    service_hours: str
    notes: str
    status: str


def get_contact_reference_data() -> tuple[
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


def get_admin_contatos() -> list[AdminContato]:
    operators, plans = get_contact_reference_data()
    contacts: list[AdminContato] = []

    for row in list_contatos_admin():
        plan_id = _text(row, "plano_id")
        plan_data = plans.get(plan_id, ("", ""))

        contacts.append(
            AdminContato(
                record_id=_text(row, "id"),
                code=_text(row, "codigo"),
                operator_id=_text(row, "operadora_id"),
                operator_name=operators.get(
                    _text(row, "operadora_id"),
                    "Operadora não informada",
                ),
                plan_id=plan_id,
                plan_name=plan_data[1],
                department=_text(row, "nome_setor"),
                purpose=_text(row, "finalidade"),
                contact_type=_text(row, "tipo"),
                contact=_text(row, "contato"),
                responsible=_text(row, "responsavel"),
                service_hours=_text(row, "horario_atendimento"),
                notes=_text(row, "observacoes"),
                status=_text(row, "status") or "Ativo",
            )
        )

    return contacts


def save_contato(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str,
    department: str,
    purpose: str,
    contact_type: str,
    contact: str,
    responsible: str,
    service_hours: str,
    notes: str,
    status: str,
    actor: dict,
) -> None:
    operator_id = operator_id.strip()
    department = department.strip()
    purpose = purpose.strip()
    contact = contact.strip()
    status = status.strip()

    if not operator_id:
        raise ValueError("Selecione a operadora.")

    if not department:
        raise ValueError("Informe o setor ou área do contato.")

    if not purpose:
        raise ValueError("Informe a finalidade do contato.")

    if not contact:
        raise ValueError("Informe o contato.")

    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")

    operators, plans = get_contact_reference_data()

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
        "codigo": code.strip() or None,
        "operadora_id": operator_id,
        "plano_id": plan_id.strip() or None,
        "nome_setor": department,
        "finalidade": purpose,
        "tipo": contact_type.strip() or None,
        "contato": contact,
        "responsavel": responsible.strip() or None,
        "horario_atendimento": service_hours.strip() or None,
        "observacoes": notes.strip() or None,
        "status": status,
    }

    previous = get_contato_admin(record_id) if record_id else None
    saved = (
        update_contato(record_id, payload)
        if record_id
        else create_contato(payload)
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento do contato.")

    try:
        append_contato_audit(
            actor_id=str(actor.get("profile_id") or actor.get("id") or "") or None,
            action=(
                "Atualização de contato"
                if record_id
                else "Cadastro de contato"
            ),
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception as error:
        print(f"[AUDIT] Falha ao registrar alteração de contato: {error}")

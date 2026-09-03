from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from nicegui_app.auth.admin_access import require_current_admin
from nicegui_app.repositories.contingencias_admin_repository import (
    append_contingencia_audit,
    create_contingencia,
    get_contingencia_admin,
    list_contingencias_admin,
    list_locais_admin,
    list_operadoras_admin,
    list_planos_admin,
    update_contingencia,
)

logger = logging.getLogger(__name__)


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _date_value(value: Any) -> str:
    return str(value or "")[:10] if value else ""


@dataclass(frozen=True, slots=True)
class AdminContingencia:
    record_id: str
    code: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    location_id: str
    location_name: str
    title: str
    description: str
    alternative_guidance: str
    alternative_contact: str
    priority: str
    start_date: str
    end_date: str
    status: str


def get_contingency_reference_data() -> dict[str, Any]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto") or _text(row, "nome")
        for row in list_operadoras_admin()
    }

    plans: dict[str, dict[str, str]] = {}
    for row in list_planos_admin():
        plans[_text(row, "id")] = {
            "name": _text(row, "nome_padronizado") or _text(row, "nome"),
            "operator_id": _text(row, "operadora_id"),
        }

    locations = {
        _text(row, "id"): _text(row, "nome")
        for row in list_locais_admin()
    }

    return {
        "operators": operators,
        "plans": plans,
        "locations": locations,
    }


def get_admin_contingencias() -> list[AdminContingencia]:
    refs = get_contingency_reference_data()
    operators = refs["operators"]
    plans = refs["plans"]
    locations = refs["locations"]

    result: list[AdminContingencia] = []
    for row in list_contingencias_admin():
        operator_id = _text(row, "operadora_id")
        plan_id = _text(row, "plano_id")
        location_id = _text(row, "local_id")

        result.append(
            AdminContingencia(
                record_id=_text(row, "id"),
                code=_text(row, "codigo"),
                operator_id=operator_id,
                operator_name=operators.get(operator_id, "Operadora não identificada"),
                plan_id=plan_id,
                plan_name=plans.get(plan_id, {}).get("name", "") if plan_id else "",
                location_id=location_id,
                location_name=locations.get(location_id, "") if location_id else "",
                title=_text(row, "titulo"),
                description=_text(row, "descricao"),
                alternative_guidance=_text(row, "orientacao_alternativa"),
                alternative_contact=_text(row, "contato_alternativo"),
                priority=_text(row, "prioridade") or "Normal",
                start_date=_date_value(row.get("inicio_em")),
                end_date=_date_value(row.get("fim_em")),
                status=_text(row, "status") or "Programada",
            )
        )

    return result


def is_current(item: AdminContingencia) -> bool:
    if item.status.strip().lower() not in {"programada", "ativa"}:
        return False

    today = date.today().isoformat()
    if item.start_date and today < item.start_date:
        return False
    if item.end_date and today > item.end_date:
        return False
    return True


def save_contingencia(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str,
    location_id: str,
    title: str,
    description: str,
    alternative_guidance: str,
    alternative_contact: str,
    priority: str,
    start_date: str,
    end_date: str,
    status: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)

    operator_id = operator_id.strip()
    plan_id = plan_id.strip()
    location_id = location_id.strip()
    title = title.strip()
    description = description.strip()
    priority = priority.strip() or "Normal"
    status = status.strip()

    if not operator_id:
        raise ValueError("Selecione a operadora.")

    if not title:
        raise ValueError("Informe o título da contingência.")

    if not description:
        raise ValueError("Informe a descrição da contingência.")

    if priority not in {"Baixa", "Normal", "Alta", "Crítica"}:
        raise ValueError("Prioridade inválida.")

    if status not in {"Programada", "Ativa", "Encerrada", "Cancelada"}:
        raise ValueError("Status inválido.")

    refs = get_contingency_reference_data()
    if operator_id not in refs["operators"]:
        raise ValueError("Operadora inválida.")

    if plan_id:
        plan = refs["plans"].get(plan_id)
        if not plan:
            raise ValueError("Plano inválido.")
        if plan.get("operator_id") != operator_id:
            raise ValueError("O plano selecionado não pertence à operadora.")

    if location_id and location_id not in refs["locations"]:
        raise ValueError("Local de atendimento inválido.")

    start_date = start_date.strip()
    end_date = end_date.strip()
    if start_date and end_date and end_date < start_date:
        raise ValueError("A data final não pode ser anterior à data inicial.")

    payload = {
        "codigo": code.strip() or None,
        "operadora_id": operator_id,
        "plano_id": plan_id or None,
        "local_id": location_id or None,
        "titulo": title,
        "descricao": description,
        "orientacao_alternativa": alternative_guidance.strip() or None,
        "contato_alternativo": alternative_contact.strip() or None,
        "prioridade": priority,
        "inicio_em": start_date or None,
        "fim_em": end_date or None,
        "status": status,
    }

    previous = get_contingencia_admin(record_id) if record_id else None
    saved = (
        update_contingencia(record_id, payload)
        if record_id
        else create_contingencia(payload)
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento da contingência.")

    try:
        append_contingencia_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action=(
                "Atualização de contingência"
                if record_id
                else "Cadastro de contingência"
            ),
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")

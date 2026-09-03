from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from nicegui_app.auth.admin_access import require_current_admin
from nicegui_app.repositories.comunicados_admin_repository import (
    append_comunicado_audit,
    create_comunicado,
    get_comunicado_admin,
    list_comunicados_admin,
    list_operadoras_admin,
    update_comunicado,
)

logger = logging.getLogger(__name__)


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "sim", "yes"}


def _date_value(value: Any) -> str:
    if not value:
        return ""
    return str(value)[:10]


@dataclass(frozen=True, slots=True)
class AdminComunicado:
    record_id: str
    code: str
    operator_id: str
    operator_name: str
    title: str
    summary: str
    content: str
    category: str
    priority: str
    target_audience: str
    start_date: str
    end_date: str
    featured: bool
    status: str
    responsible: str


def get_communication_reference_data() -> dict[str, str]:
    return {
        _text(row, "id"): _text(row, "nome_curto") or _text(row, "nome")
        for row in list_operadoras_admin()
    }


def get_admin_comunicados() -> list[AdminComunicado]:
    operators = get_communication_reference_data()
    result: list[AdminComunicado] = []

    for row in list_comunicados_admin():
        operator_id = _text(row, "operadora_id")
        result.append(
            AdminComunicado(
                record_id=_text(row, "id"),
                code=_text(row, "codigo"),
                operator_id=operator_id,
                operator_name=(
                    operators.get(operator_id, "Geral / institucional")
                    if operator_id
                    else "Geral / institucional"
                ),
                title=_text(row, "titulo"),
                summary=_text(row, "resumo"),
                content=_text(row, "conteudo"),
                category=_text(row, "categoria"),
                priority=_text(row, "prioridade") or "Normal",
                target_audience=_text(row, "publico_alvo"),
                start_date=_date_value(row.get("inicio_em")),
                end_date=_date_value(row.get("fim_em")),
                featured=_bool(row.get("destaque")),
                status=_text(row, "status") or "Rascunho",
                responsible=_text(row, "responsavel"),
            )
        )

    return result


def is_current(item: AdminComunicado) -> bool:
    if item.status.lower() != "publicado":
        return False

    today = date.today().isoformat()
    if item.start_date and today < item.start_date:
        return False
    if item.end_date and today > item.end_date:
        return False
    return True


def save_comunicado(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    title: str,
    summary: str,
    content: str,
    category: str,
    priority: str,
    target_audience: str,
    start_date: str,
    end_date: str,
    featured: bool,
    status: str,
    responsible: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)

    title = title.strip()
    summary = summary.strip()
    content = content.strip()
    status = status.strip()
    priority = priority.strip() or "Normal"

    if not title:
        raise ValueError("Informe o título do comunicado.")

    if not summary:
        raise ValueError("Informe o resumo do comunicado.")

    if not content:
        raise ValueError("Informe o conteúdo do comunicado.")

    if status not in {"Rascunho", "Publicado", "Inativo"}:
        raise ValueError("Status inválido.")

    if priority not in {"Baixa", "Normal", "Alta", "Crítica"}:
        raise ValueError("Prioridade inválida.")

    operators = get_communication_reference_data()
    if operator_id and operator_id not in operators:
        raise ValueError("Operadora inválida.")

    start_date = start_date.strip()
    end_date = end_date.strip()
    if start_date and end_date and end_date < start_date:
        raise ValueError("A data final não pode ser anterior à data inicial.")

    payload = {
        "codigo": code.strip() or None,
        "operadora_id": operator_id.strip() or None,
        "titulo": title,
        "resumo": summary,
        "conteudo": content,
        "categoria": category.strip() or None,
        "prioridade": priority,
        "publico_alvo": target_audience.strip() or None,
        "inicio_em": start_date or None,
        "fim_em": end_date or None,
        "destaque": bool(featured),
        "status": status,
        "responsavel": responsible.strip() or None,
    }

    previous = get_comunicado_admin(record_id) if record_id else None
    saved = (
        update_comunicado(record_id, payload)
        if record_id
        else create_comunicado(payload)
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento do comunicado.")

    try:
        append_comunicado_audit(
            actor_id=str(actor.get("profile_id") or "") or None,
            action=(
                "Atualização de comunicado"
                if record_id
                else "Cadastro de comunicado"
            ),
            entity_id=str(saved.get("id") or record_id or ""),
            previous_data=previous,
            new_data=payload,
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria administrativa.")

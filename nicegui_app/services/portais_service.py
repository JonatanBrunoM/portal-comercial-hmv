from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.portais_repository import (
    get_portal,
    list_locais_for_portais,
    list_operadoras_for_portais,
    list_planos_for_portais,
    list_portais,
)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@dataclass(frozen=True, slots=True)
class PortalPreview:
    portal_id: str
    code: str
    name: str
    portal_type: str
    url: str
    requires_login: bool
    instruction: str
    observations: str
    status: str
    general_tip: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    local_id: str
    local_name: str


def _maps() -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto", "nome")
        for row in list_operadoras_for_portais()
        if _text(row, "id")
    }
    plans = {
        _text(row, "id"): _text(row, "nome_padronizado", "nome")
        for row in list_planos_for_portais()
        if _text(row, "id")
    }
    locals_map = {
        _text(row, "id"): _text(row, "nome")
        for row in list_locais_for_portais()
        if _text(row, "id")
    }
    return operators, plans, locals_map


def _from_record(
    row: dict[str, Any],
    operators: dict[str, str],
    plans: dict[str, str],
    locals_map: dict[str, str],
) -> PortalPreview:
    operator_id = _text(row, "operadora_id")
    plan_id = _text(row, "plano_id")
    local_id = _text(row, "local_id")

    return PortalPreview(
        portal_id=_text(row, "id"),
        code=_text(row, "codigo"),
        name=_text(row, "nome") or "Portal sem nome",
        portal_type=_text(row, "tipo"),
        url=_text(row, "url"),
        requires_login=bool(row.get("exige_login")),
        instruction=_text(row, "instrucao_acesso"),
        observations=_text(row, "observacoes"),
        status=_text(row, "status") or "Não informado",
        general_tip=_text(row, "dica_geral_acesso"),
        operator_id=operator_id,
        operator_name=operators.get(operator_id, "Operadora não informada"),
        plan_id=plan_id,
        plan_name=plans.get(plan_id, ""),
        local_id=local_id,
        local_name=locals_map.get(local_id, ""),
    )


def get_portais_preview() -> list[PortalPreview]:
    operators, plans, locals_map = _maps()
    return [
        _from_record(row, operators, plans, locals_map)
        for row in list_portais()
    ]


def get_portal_detail(portal_id: str) -> PortalPreview | None:
    record = get_portal(portal_id)
    if record is None:
        return None

    operators, plans, locals_map = _maps()
    return _from_record(record, operators, plans, locals_map)

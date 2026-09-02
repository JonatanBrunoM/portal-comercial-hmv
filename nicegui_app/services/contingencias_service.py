from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from nicegui_app.repositories.contingencias_repository import (
    get_contingencia,
    list_contingencias,
    list_locais_for_contingencias,
    list_operadoras_for_contingencias,
    list_planos_for_contingencias,
)

def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def _date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

@dataclass(frozen=True, slots=True)
class ContingenciaPreview:
    contingency_id: str
    code: str
    operator_name: str
    plan_name: str
    local_name: str
    title: str
    description: str
    alternative_guidance: str
    alternative_contact: str
    priority: str
    start_date: date | None
    end_date: date | None
    status: str

    @property
    def period_active(self) -> bool:
        today = date.today()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

def _maps() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    ops = {
        _text(r, "id"): _text(r, "nome_curto", "nome")
        for r in list_operadoras_for_contingencias()
        if _text(r, "id")
    }
    plans = {
        _text(r, "id"): _text(r, "nome_padronizado", "nome")
        for r in list_planos_for_contingencias()
        if _text(r, "id")
    }
    locals_map = {
        _text(r, "id"): _text(r, "nome")
        for r in list_locais_for_contingencias()
        if _text(r, "id")
    }
    return ops, plans, locals_map

def _from(row: dict[str, Any], ops: dict[str, str], plans: dict[str, str], locals_map: dict[str, str]) -> ContingenciaPreview:
    oid = _text(row, "operadora_id")
    pid = _text(row, "plano_id")
    lid = _text(row, "local_id")
    return ContingenciaPreview(
        contingency_id=_text(row, "id"),
        code=_text(row, "codigo"),
        operator_name=ops.get(oid, "Operadora não informada"),
        plan_name=plans.get(pid, ""),
        local_name=locals_map.get(lid, ""),
        title=_text(row, "titulo") or "Contingência sem título",
        description=_text(row, "descricao"),
        alternative_guidance=_text(row, "orientacao_alternativa"),
        alternative_contact=_text(row, "contato_alternativo"),
        priority=_text(row, "prioridade") or "Normal",
        start_date=_date(row.get("inicio_em")),
        end_date=_date(row.get("fim_em")),
        status=_text(row, "status") or "Não informado",
    )

def get_contingencias_preview() -> list[ContingenciaPreview]:
    ops, plans, locals_map = _maps()
    return [_from(r, ops, plans, locals_map) for r in list_contingencias()]

def get_contingencia_detail(contingency_id: str) -> ContingenciaPreview | None:
    row = get_contingencia(contingency_id)
    if not row:
        return None
    ops, plans, locals_map = _maps()
    return _from(row, ops, plans, locals_map)

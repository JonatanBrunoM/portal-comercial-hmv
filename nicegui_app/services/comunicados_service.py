from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from nicegui_app.repositories.comunicados_repository import get_comunicado, list_comunicados, list_operadoras_for_comunicados

def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def _bool(value: Any) -> bool:
    return isinstance(value, bool) and value or str(value or "").strip().lower() in {"1","true","sim","yes"}

def _date(value: Any) -> date | None:
    if not value: return None
    try: return datetime.fromisoformat(str(value).replace("Z","+00:00")).date()
    except ValueError:
        try: return date.fromisoformat(str(value)[:10])
        except ValueError: return None

@dataclass(frozen=True, slots=True)
class ComunicadoPreview:
    communication_id: str; code: str; operator_name: str; title: str; summary: str
    content: str; category: str; priority: str; audience: str
    start_date: date | None; end_date: date | None; featured: bool; status: str; responsible: str
    @property
    def period_active(self) -> bool:
        if self.status.strip().lower() != "publicado":
            return False
        today=date.today()
        return not ((self.start_date and today < self.start_date) or (self.end_date and today > self.end_date))

def _map() -> dict[str,str]:
    return {_text(r,"id"):_text(r,"nome_curto","nome") for r in list_operadoras_for_comunicados() if _text(r,"id")}

def _from(row: dict[str,Any], ops: dict[str,str]) -> ComunicadoPreview:
    oid=_text(row,"operadora_id")
    return ComunicadoPreview(_text(row,"id"),_text(row,"codigo"),ops.get(oid,"Geral / institucional"),
        _text(row,"titulo") or "Comunicado sem título",_text(row,"resumo"),_text(row,"conteudo"),
        _text(row,"categoria"),_text(row,"prioridade") or "Normal",_text(row,"publico_alvo"),
        _date(row.get("inicio_em")),_date(row.get("fim_em")),_bool(row.get("destaque")),
        _text(row,"status") or "Não informado",_text(row,"responsavel"))

def get_comunicados_preview() -> list[ComunicadoPreview]:
    ops=_map(); return [_from(r,ops) for r in list_comunicados()]

def get_comunicado_detail(communication_id: str) -> ComunicadoPreview | None:
    row=get_comunicado(communication_id)
    return _from(row,_map()) if row else None

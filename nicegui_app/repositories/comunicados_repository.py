from __future__ import annotations
from typing import Any
from nicegui_app.data.supabase_client import rest_select

def list_comunicados() -> list[dict[str, Any]]:
    return rest_select("comunicados", select="*", params={"order": "created_at.desc"})

def get_comunicado(communication_id: str) -> dict[str, Any] | None:
    rows = rest_select("comunicados", select="*", params={"id": f"eq.{communication_id}", "limit": "1"})
    return rows[0] if rows else None

def list_operadoras_for_comunicados() -> list[dict[str, Any]]:
    return rest_select("operadoras", select="id,nome,nome_curto,codigo,status", params={"order": "nome.asc"})

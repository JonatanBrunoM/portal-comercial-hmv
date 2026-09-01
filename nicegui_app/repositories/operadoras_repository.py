from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import get_supabase_client


def list_operadoras() -> list[dict[str, Any]]:
    """Lista as operadoras diretamente da base atual do Portal Comercial."""
    response = (
        get_supabase_client()
        .table("operadoras")
        .select("*")
        .order("nome")
        .execute()
    )
    return list(response.data or [])

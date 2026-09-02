from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def list_operadoras() -> list[dict[str, Any]]:
    """Lista operadoras usando o endpoint REST server-side do Supabase."""
    return rest_select(
        "operadoras",
        select="id,codigo,nome,status",
        params={"order": "nome.asc"},
    )

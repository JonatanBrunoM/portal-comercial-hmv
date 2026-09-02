from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def list_contatos() -> list[dict[str, Any]]:
    return rest_select(
        "contatos",
        select="*",
        params={"order": "nome_setor.asc"},
    )


def get_contato(contact_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "contatos",
        select="*",
        params={
            "id": f"eq.{contact_id}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def list_operadoras_for_contatos() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,codigo,status",
        params={"order": "nome.asc"},
    )


def list_planos_for_contatos() -> list[dict[str, Any]]:
    return rest_select(
        "planos",
        select="id,operadora_id,nome,nome_padronizado,codigo,status",
        params={"order": "nome.asc"},
    )

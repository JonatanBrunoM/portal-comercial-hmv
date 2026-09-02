from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def list_consultores() -> list[dict[str, Any]]:
    return rest_select(
        "consultores",
        select="*",
        params={"order": "nome.asc"},
    )


def get_consultor(consultant_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "consultores",
        select="*",
        params={
            "id": f"eq.{consultant_id}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def list_carteiras() -> list[dict[str, Any]]:
    return rest_select(
        "carteiras",
        select="*",
        params={"order": "created_at.asc"},
    )


def list_operadoras_for_consultores() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,codigo,status",
        params={"order": "nome.asc"},
    )


def list_planos_for_consultores() -> list[dict[str, Any]]:
    return rest_select(
        "planos",
        select="id,operadora_id,nome,nome_padronizado,codigo,status",
        params={"order": "nome.asc"},
    )

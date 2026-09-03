from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def list_documentos() -> list[dict[str, Any]]:
    return rest_select(
        "documentos",
        select="*",
        params={"order": "nome.asc"},
    )


def get_documento(document_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "documentos",
        select="*",
        params={
            "id": f"eq.{document_id}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def list_operadoras_for_documentos() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,codigo,status",
        params={"order": "nome.asc"},
    )


def list_planos_for_documentos() -> list[dict[str, Any]]:
    return rest_select(
        "planos",
        select="id,operadora_id,nome,nome_padronizado,codigo,status",
        params={"order": "nome.asc"},
    )


def list_locais_for_documentos() -> list[dict[str, Any]]:
    return rest_select(
        "locais_atendimento",
        select="id,codigo,nome,status",
        params={"order": "nome.asc"},
    )


def list_tipos_atendimento_for_documentos() -> list[dict[str, Any]]:
    return rest_select(
        "tipos_atendimento",
        select="id,codigo,nome,status",
        params={"order": "nome.asc"},
    )

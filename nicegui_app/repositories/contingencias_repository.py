from __future__ import annotations
from typing import Any
from nicegui_app.data.supabase_client import rest_select

def list_contingencias() -> list[dict[str, Any]]:
    return rest_select("contingencias", select="*", params={"order": "inicio_em.desc"})

def get_contingencia(contingency_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "contingencias",
        select="*",
        params={"id": f"eq.{contingency_id}", "limit": "1"},
    )
    return rows[0] if rows else None

def list_operadoras_for_contingencias() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,codigo,status",
        params={"order": "nome.asc"},
    )

def list_planos_for_contingencias() -> list[dict[str, Any]]:
    return rest_select(
        "planos",
        select="id,operadora_id,nome,nome_padronizado,codigo,status",
        params={"order": "nome.asc"},
    )

def list_locais_for_contingencias() -> list[dict[str, Any]]:
    return rest_select(
        "locais_atendimento",
        select="id,codigo,nome,status",
        params={"order": "nome.asc"},
    )

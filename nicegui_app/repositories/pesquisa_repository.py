from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def _list(table: str) -> list[dict[str, Any]]:
    return rest_select(table, select="*")


def load_search_catalog() -> dict[str, list[dict[str, Any]]]:
    return {
        "operadoras": _list("operadoras"),
        "planos": _list("planos"),
        "portais": _list("portais"),
        "documentos": _list("documentos"),
        "contatos": _list("contatos"),
        "consultores": _list("consultores"),
        "comunicados": _list("comunicados"),
        "contingencias": _list("contingencias"),
        "elegibilidade": _list("elegibilidade"),
        "autorizacoes": _list("autorizacoes"),
        "coberturas": _list("coberturas"),
        "dicas_operacionais": _list("dicas_operacionais"),
    }

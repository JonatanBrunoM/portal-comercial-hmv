from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from nicegui_app.data.supabase_client import rest_select


def _list(table: str) -> list[dict[str, Any]]:
    return rest_select(table, select="*")


def load_search_catalog() -> dict[str, list[dict[str, Any]]]:
    tables = (
        "operadoras", "planos", "portais", "documentos", "contatos",
        "consultores", "comunicados", "contingencias", "elegibilidade",
        "autorizacoes", "coberturas", "dicas_operacionais",
    )

    # As consultas são independentes. Executá-las em paralelo evita que a tela
    # de Pesquisa pague a soma da latência de doze chamadas HTTP sequenciais.
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="portal-search") as pool:
        rows = pool.map(_list, tables)
        return dict(zip(tables, rows))

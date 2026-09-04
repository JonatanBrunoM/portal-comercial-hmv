from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from nicegui_app.data.supabase_client import rest_select


def _load_operadoras() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,status",
        params={"order": "nome.asc"},
    )


def _load_portais() -> list[dict[str, Any]]:
    return rest_select(
        "portais",
        select="id,nome,operadora_id,status",
        params={"order": "nome.asc"},
    )


def _load_documentos() -> list[dict[str, Any]]:
    return rest_select(
        "documentos",
        select="id,nome,operadora_id,status",
        params={"order": "nome.asc"},
    )


def _load_comunicados() -> list[dict[str, Any]]:
    return rest_select(
        "comunicados",
        select=(
            "id,operadora_id,titulo,resumo,categoria,prioridade,"
            "inicio_em,fim_em,destaque,status"
        ),
        params={"order": "inicio_em.desc"},
    )


def _load_contingencias() -> list[dict[str, Any]]:
    return rest_select(
        "contingencias",
        select=(
            "id,operadora_id,titulo,descricao,orientacao_alternativa,"
            "prioridade,inicio_em,fim_em,status"
        ),
        params={"order": "inicio_em.desc"},
    )


def load_home_snapshot() -> dict[str, list[dict[str, Any]]]:
    """Carrega os blocos independentes da Home em paralelo.

    Na maior parte do tempo as leituras são atendidas pelo snapshot em memória
    do Supabase client. O paralelismo também evita latência acumulada no primeiro
    acesso após um cold start.
    """
    loaders: dict[str, Callable[[], list[dict[str, Any]]]] = {
        "operadoras": _load_operadoras,
        "portais": _load_portais,
        "documentos": _load_documentos,
        "comunicados": _load_comunicados,
        "contingencias": _load_contingencias,
    }

    result: dict[str, list[dict[str, Any]]] = {key: [] for key in loaders}

    with ThreadPoolExecutor(
        max_workers=len(loaders),
        thread_name_prefix="portal-home",
    ) as pool:
        futures = {pool.submit(loader): key for key, loader in loaders.items()}
        for future, key in ((future, futures[future]) for future in futures):
            try:
                result[key] = future.result()
            except Exception:
                # A Home deve continuar útil mesmo se um bloco informativo
                # estiver temporariamente indisponível.
                result[key] = []

    return result

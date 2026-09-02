from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import httpx
from supabase import Client, create_client


class SupabaseConfigurationError(RuntimeError):
    """Indica que as variáveis obrigatórias do Supabase não foram configuradas."""


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SupabaseConfigurationError(
            f"A variável de ambiente {name} não está configurada."
        )
    return value


def get_supabase_url() -> str:
    return _required_env("SUPABASE_URL").rstrip("/")


def get_supabase_server_key() -> str:
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    if not key:
        raise SupabaseConfigurationError(
            "Configure SUPABASE_SECRET_KEY ou SUPABASE_SERVICE_ROLE_KEY."
        )
    return key


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Cliente oficial mantido para recursos que precisarem do SDK."""
    return create_client(
        get_supabase_url(),
        get_supabase_server_key(),
    )


def _rest_headers() -> dict[str, str]:
    """
    Cabeçalhos server-side para o PostgREST.

    Chaves sb_secret_* usam o header apikey.
    service_role legado também recebe Authorization Bearer.
    """
    key = get_supabase_server_key()

    headers = {
        "apikey": key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if not key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {key}"

    return headers


def rest_select(
    table_name: str,
    *,
    select: str = "*",
    params: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> list[dict[str, Any]]:
    """Executa leitura REST server-side diretamente no PostgREST do Supabase."""
    query_params = {"select": select}
    query_params.update(params or {})

    response = httpx.get(
        f"{get_supabase_url()}/rest/v1/{table_name}",
        headers=_rest_headers(),
        params=query_params,
        timeout=timeout,
    )
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list):
        raise RuntimeError(
            "O Supabase retornou um formato inesperado para uma consulta de tabela."
        )

    return [
        dict(row)
        for row in payload
        if isinstance(row, dict)
    ]


def check_supabase_connection() -> tuple[bool, str]:
    """Executa uma leitura mínima sem revelar detalhes sensíveis."""
    try:
        rest_select(
            "operadoras",
            select="id",
            params={"limit": "1"},
        )
        return True, "Supabase conectado"
    except SupabaseConfigurationError as error:
        return False, str(error)
    except Exception:
        return False, "Não foi possível consultar o Supabase."

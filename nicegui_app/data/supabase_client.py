from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

import httpx
from supabase import Client, create_client


logger = logging.getLogger(__name__)


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

    logger.info(
        "Supabase REST respondeu. tabela=%s status=%s content_type=%s",
        table_name,
        response.status_code,
        response.headers.get("content-type", "não informado"),
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



def rest_insert(
    table_name: str,
    payload: dict[str, Any],
    *,
    timeout: float = 15.0,
) -> dict[str, Any] | None:
    """Insere um registro via PostgREST usando somente a credencial server-side."""
    headers = {
        **_rest_headers(),
        "Prefer": "return=representation",
    }

    response = httpx.post(
        f"{get_supabase_url()}/rest/v1/{table_name}",
        headers=headers,
        json=payload,
        timeout=timeout,
    )

    logger.info(
        "Supabase REST insert respondeu. tabela=%s status=%s",
        table_name,
        response.status_code,
    )

    if response.is_error:
        try:
            error_payload = response.json()
        except Exception:
            error_payload = {}

        message = str(error_payload.get("message") or "").strip()
        details = str(error_payload.get("details") or "").strip()
        hint = str(error_payload.get("hint") or "").strip()
        code = str(error_payload.get("code") or "").strip()

        parts = [
            part
            for part in (
                f"Supabase recusou o cadastro em {table_name}.",
                f"Código: {code}" if code else "",
                f"Motivo: {message}" if message else "",
                f"Detalhes: {details}" if details else "",
                f"Dica: {hint}" if hint else "",
            )
            if part
        ]
        raise RuntimeError(" ".join(parts))

    data = response.json()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return dict(data[0])
    return None


def rest_update(
    table_name: str,
    *,
    match: dict[str, str],
    payload: dict[str, Any],
    timeout: float = 15.0,
) -> dict[str, Any] | None:
    """Atualiza registro(s) via PostgREST usando filtros explícitos."""
    if not match:
        raise ValueError("rest_update exige ao menos um filtro em match.")

    headers = {
        **_rest_headers(),
        "Prefer": "return=representation",
    }

    supported_operators = (
        "eq.",
        "neq.",
        "gt.",
        "gte.",
        "lt.",
        "lte.",
        "like.",
        "ilike.",
        "in.",
        "is.",
        "not.",
        "cs.",
        "cd.",
        "ov.",
        "sl.",
        "sr.",
        "nxr.",
        "nxl.",
        "adj.",
    )

    params = {
        key: (
            value
            if str(value).startswith(supported_operators)
            else f"eq.{value}"
        )
        for key, value in match.items()
    }

    response = httpx.patch(
        f"{get_supabase_url()}/rest/v1/{table_name}",
        headers=headers,
        params=params,
        json=payload,
        timeout=timeout,
    )

    logger.info(
        "Supabase REST update respondeu. tabela=%s status=%s",
        table_name,
        response.status_code,
    )

    if response.is_error:
        try:
            error_payload = response.json()
        except Exception:
            error_payload = {}

        message = str(error_payload.get("message") or "").strip()
        details = str(error_payload.get("details") or "").strip()
        hint = str(error_payload.get("hint") or "").strip()
        code = str(error_payload.get("code") or "").strip()

        parts = [
            part
            for part in (
                f"Supabase recusou a alteração em {table_name}.",
                f"Código: {code}" if code else "",
                f"Motivo: {message}" if message else "",
                f"Detalhes: {details}" if details else "",
                f"Dica: {hint}" if hint else "",
            )
            if part
        ]
        raise RuntimeError(" ".join(parts))

    data = response.json()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return dict(data[0])
    return None

def check_supabase_connection() -> tuple[bool, str]:
    """Executa uma leitura mínima sem revelar chave, URL completa ou dados."""
    try:
        rest_select(
            "operadoras",
            select="id",
            params={"limit": "1"},
        )
        return True, "Supabase conectado"

    except SupabaseConfigurationError as error:
        logger.error("Configuração Supabase ausente: %s", error)
        return False, str(error)

    except httpx.HTTPStatusError as error:
        logger.error(
            "Supabase REST recusou a consulta. status=%s",
            error.response.status_code,
        )
        return (
            False,
            f"Supabase respondeu com HTTP {error.response.status_code}.",
        )

    except httpx.RequestError as error:
        logger.error(
            "Falha de transporte ao acessar Supabase. tipo=%s",
            type(error).__name__,
        )
        return False, "Falha de rede ao consultar o Supabase."

    except Exception as error:
        logger.exception(
            "Falha inesperada na validação REST do Supabase. tipo=%s",
            type(error).__name__,
        )
        return False, "Não foi possível consultar o Supabase."

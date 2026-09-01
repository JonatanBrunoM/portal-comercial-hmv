from __future__ import annotations

import os
from functools import lru_cache

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


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Cria um único cliente Supabase, exclusivamente no servidor."""
    url = _required_env("SUPABASE_URL")
    secret_key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )

    if not secret_key:
        raise SupabaseConfigurationError(
            "Configure SUPABASE_SECRET_KEY ou SUPABASE_SERVICE_ROLE_KEY."
        )

    return create_client(url, secret_key)


def check_supabase_connection() -> tuple[bool, str]:
    """Executa uma leitura mínima sem revelar detalhes sensíveis."""
    try:
        (
            get_supabase_client()
            .table("operadoras")
            .select("id")
            .limit(1)
            .execute()
        )
        return True, "Supabase conectado"
    except SupabaseConfigurationError as error:
        return False, str(error)
    except Exception:
        return False, "Não foi possível consultar o Supabase."

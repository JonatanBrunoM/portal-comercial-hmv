from __future__ import annotations

import json
import logging
from typing import Any

from nicegui_app.data.supabase_client import get_supabase_client


logger = logging.getLogger(__name__)


def _normalize_rows(data: Any) -> list[dict[str, Any]]:
    """Normaliza diferentes formatos de resposta sem expor o conteúdo nos logs."""
    if data is None:
        return []

    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]

    if isinstance(data, dict):
        nested = data.get("data")
        if isinstance(nested, list):
            return [row for row in nested if isinstance(row, dict)]
        return [data]

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            logger.error(
                "Resposta inesperada do Supabase: conteúdo textual não JSON."
            )
            return []

        return _normalize_rows(parsed)

    logger.error(
        "Resposta inesperada do Supabase. Tipo recebido: %s",
        type(data).__name__,
    )
    return []


def list_operadoras() -> list[dict[str, Any]]:
    """Lista as operadoras diretamente da base atual do Portal Comercial."""
    response = (
        get_supabase_client()
        .table("operadoras")
        .select("*")
        .order("nome")
        .execute()
    )

    return _normalize_rows(response.data)

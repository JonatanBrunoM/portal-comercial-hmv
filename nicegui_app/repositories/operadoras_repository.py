from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

from nicegui_app.data.supabase_client import get_supabase_client


logger = logging.getLogger(__name__)


def _to_mapping(value: Any) -> dict[str, Any] | None:
    """Converte um registro isolado em dict sem registrar seu conteúdo."""
    if isinstance(value, Mapping):
        return dict(value)

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None

        if isinstance(parsed, Mapping):
            return dict(parsed)

        return None

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dict(dumped)

    as_dict = getattr(value, "dict", None)
    if callable(as_dict):
        dumped = as_dict()
        if isinstance(dumped, Mapping):
            return dict(dumped)

    return None


def _normalize_rows(data: Any) -> list[dict[str, Any]]:
    """
    Normaliza a resposta do PostgREST/Supabase.

    A função aceita listas, mappings, JSON textual e objetos Pydantic,
    mas nunca registra o conteúdo das linhas.
    """
    if data is None:
        return []

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            logger.error(
                "Resposta textual inesperada do Supabase; JSON inválido."
            )
            return []

        return _normalize_rows(parsed)

    if isinstance(data, Mapping):
        if "data" in data:
            return _normalize_rows(data["data"])

        row = _to_mapping(data)
        return [row] if row is not None else []

    if isinstance(data, Sequence) and not isinstance(
        data,
        (str, bytes, bytearray),
    ):
        rows: list[dict[str, Any]] = []

        for item in data:
            row = _to_mapping(item)

            if row is not None:
                rows.append(row)
                continue

            if isinstance(item, str):
                try:
                    parsed_item = json.loads(item)
                except json.JSONDecodeError:
                    continue

                if isinstance(parsed_item, Sequence) and not isinstance(
                    parsed_item,
                    (str, bytes, bytearray),
                ):
                    rows.extend(_normalize_rows(parsed_item))

        if not rows and data:
            logger.error(
                "Resposta do Supabase recebida como sequência, mas nenhum "
                "registro pôde ser normalizado. Tipo do primeiro item: %s",
                type(data[0]).__name__,
            )

        return rows

    row = _to_mapping(data)
    if row is not None:
        return [row]

    logger.error(
        "Formato de resposta não suportado pelo repository. Tipo: %s",
        type(data).__name__,
    )
    return []


def list_operadoras() -> list[dict[str, Any]]:
    """Lista as operadoras diretamente da base atual do Portal Comercial."""
    response = (
        get_supabase_client()
        .table("operadoras")
        .select("id,codigo,nome,status")
        .order("nome")
        .execute()
    )

    data = response.data

    logger.info(
        "Consulta operadoras concluída. Tipo de response.data: %s; "
        "quantidade informada: %s",
        type(data).__name__,
        len(data) if hasattr(data, "__len__") else "indisponível",
    )

    if isinstance(data, Sequence) and not isinstance(
        data,
        (str, bytes, bytearray),
    ) and data:
        logger.info(
            "Tipo do primeiro registro retornado por operadoras: %s",
            type(data[0]).__name__,
        )

    return _normalize_rows(data)

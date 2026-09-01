from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.operadoras_repository import list_operadoras


@dataclass(frozen=True, slots=True)
class OperadoraPreview:
    operator_id: str
    code: str
    name: str
    short_name: str
    status: str


def _text(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def get_operadoras_preview() -> list[OperadoraPreview]:
    """Normaliza apenas os campos necessários para a prova de conexão."""
    result: list[OperadoraPreview] = []

    for record in list_operadoras():
        name = _text(record, "nome", "name") or "Operadora sem nome"
        result.append(
            OperadoraPreview(
                operator_id=_text(record, "id"),
                code=_text(record, "codigo", "code"),
                name=name,
                short_name=_text(
                    record,
                    "nome_curto",
                    "nome_fantasia",
                    "short_name",
                )
                or name,
                status=_text(record, "status") or "Não informado",
            )
        )

    return result

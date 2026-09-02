from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


OPERADORA_FIELDS = (
    "id,codigo,nome,nome_curto,status,observacoes,logo_url,site_url"
)


def list_operadoras() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select=OPERADORA_FIELDS,
        params={"order": "nome.asc"},
    )


def get_operadora(operator_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "operadoras",
        select=OPERADORA_FIELDS,
        params={
            "id": f"eq.{operator_id}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def list_planos_by_operadora(
    operator_id: str,
) -> list[dict[str, Any]]:
    return rest_select(
        "planos",
        select=(
            "id,codigo,nome,nome_padronizado,tipo_plano,"
            "observacao_resumida,status"
        ),
        params={
            "operadora_id": f"eq.{operator_id}",
            "order": "nome.asc",
        },
    )

from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_operadoras_admin() -> list[dict[str, Any]]:
    return rest_select("operadoras", select="*", params={"order": "nome.asc"})


def list_planos_admin() -> list[dict[str, Any]]:
    return rest_select("planos", select="*", params={"order": "nome.asc"})


def get_operadora_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select("operadoras", select="*", params={"id": f"eq.{record_id}", "limit": "1"})
    return rows[0] if rows else None


def get_plano_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select("planos", select="*", params={"id": f"eq.{record_id}", "limit": "1"})
    return rows[0] if rows else None


def create_operadora(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("operadoras", payload)


def update_operadora(record_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_update("operadoras", match={"id": record_id}, payload=payload)


def create_plano(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("planos", payload)


def update_plano(record_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_update("planos", match={"id": record_id}, payload=payload)


def append_admin_audit(
    *,
    actor_id: str | None,
    action: str,
    entity: str,
    entity_id: str,
    description: str,
    previous_data: dict[str, Any] | None,
    new_data: dict[str, Any],
) -> None:
    rest_insert(
        "audit_logs",
        {
            "usuario_id": actor_id,
            "acao": action,
            "entidade": entity,
            "entidade_id": entity_id,
            "descricao": description,
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )

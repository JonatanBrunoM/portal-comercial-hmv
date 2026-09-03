from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_consultores_admin() -> list[dict[str, Any]]:
    return rest_select(
        "consultores",
        select="*",
        params={"order": "nome.asc"},
    )


def list_carteiras_admin() -> list[dict[str, Any]]:
    return rest_select(
        "carteiras",
        select="*",
        params={"order": "created_at.asc"},
    )


def list_operadoras_admin() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,status",
        params={"order": "nome.asc"},
    )


def list_planos_admin() -> list[dict[str, Any]]:
    return rest_select(
        "planos",
        select="id,operadora_id,nome,nome_padronizado,status",
        params={"order": "nome.asc"},
    )


def get_consultor_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "consultores",
        select="*",
        params={"id": f"eq.{record_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def get_carteira_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "carteiras",
        select="*",
        params={"id": f"eq.{record_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def create_consultor(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("consultores", payload)


def update_consultor(
    record_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "consultores",
        match={"id": record_id},
        payload=payload,
    )


def create_carteira(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("carteiras", payload)


def update_carteira(
    record_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "carteiras",
        match={"id": record_id},
        payload=payload,
    )


def append_admin_audit(
    *,
    actor_id: str | None,
    action: str,
    entity: str,
    entity_id: str,
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
            "descricao": f"Registro de {entity} alterado pela Administração.",
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )

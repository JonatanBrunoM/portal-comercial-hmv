from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_comunicados_admin() -> list[dict[str, Any]]:
    return rest_select(
        "comunicados",
        select="*",
        params={"order": "created_at.desc"},
    )


def list_operadoras_admin() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select="id,nome,nome_curto,status",
        params={"order": "nome.asc"},
    )


def get_comunicado_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "comunicados",
        select="*",
        params={"id": f"eq.{record_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def create_comunicado(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("comunicados", payload)


def update_comunicado(
    record_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "comunicados",
        match={"id": record_id},
        payload=payload,
    )


def append_comunicado_audit(
    *,
    actor_id: str | None,
    action: str,
    entity_id: str,
    previous_data: dict[str, Any] | None,
    new_data: dict[str, Any],
) -> None:
    rest_insert(
        "audit_logs",
        {
            "usuario_id": actor_id,
            "acao": action,
            "entidade": "comunicados",
            "entidade_id": entity_id,
            "descricao": "Cadastro de comunicado alterado pela Administração.",
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )

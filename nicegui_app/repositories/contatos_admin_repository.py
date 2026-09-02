from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_contatos_admin() -> list[dict[str, Any]]:
    return rest_select(
        "contatos",
        select="*",
        params={"order": "nome_setor.asc"},
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


def get_contato_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "contatos",
        select="*",
        params={"id": f"eq.{record_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def create_contato(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("contatos", payload)


def update_contato(
    record_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "contatos",
        match={"id": record_id},
        payload=payload,
    )


def append_contato_audit(
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
            "entidade": "contatos",
            "entidade_id": entity_id,
            "descricao": "Cadastro de contato alterado pela Administração.",
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )

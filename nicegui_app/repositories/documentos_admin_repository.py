from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_documentos_admin() -> list[dict[str, Any]]:
    return rest_select(
        "documentos",
        select="*",
        params={"order": "nome.asc"},
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


def list_locais_admin() -> list[dict[str, Any]]:
    return rest_select(
        "locais_atendimento",
        select="id,nome,status",
        params={"order": "nome.asc"},
    )


def list_tipos_atendimento_admin() -> list[dict[str, Any]]:
    return rest_select(
        "tipos_atendimento",
        select="id,nome,status",
        params={"order": "nome.asc"},
    )


def get_documento_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "documentos",
        select="*",
        params={"id": f"eq.{record_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def create_documento(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("documentos", payload)


def update_documento(
    record_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "documentos",
        match={"id": record_id},
        payload=payload,
    )


def append_documento_audit(
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
            "entidade": "documentos",
            "entidade_id": entity_id,
            "descricao": "Cadastro de documento alterado pela Administração.",
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )

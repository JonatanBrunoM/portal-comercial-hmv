from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_contingencias_admin() -> list[dict[str, Any]]:
    return rest_select(
        "contingencias",
        select="*",
        params={"order": "created_at.desc"},
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


def get_contingencia_admin(record_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "contingencias",
        select="*",
        params={"id": f"eq.{record_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def create_contingencia(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("contingencias", payload)


def update_contingencia(
    record_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "contingencias",
        match={"id": record_id},
        payload=payload,
    )


def append_contingencia_audit(
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
            "entidade": "contingencias",
            "entidade_id": entity_id,
            "descricao": "Cadastro de contingência alterado pela Administração.",
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )

from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def list_audit_logs_admin(limit: int = 300) -> list[dict[str, Any]]:
    return rest_select(
        "audit_logs",
        select=(
            "id,usuario_id,acao,entidade,entidade_id,descricao,"
            "dados_anteriores,dados_novos,created_at"
        ),
        params={
            "order": "created_at.desc",
            "limit": str(max(1, min(limit, 500))),
        },
    )


def list_audit_profiles_admin() -> list[dict[str, Any]]:
    return rest_select(
        "profiles",
        select="id,nome,email,role,status",
        params={"order": "nome.asc"},
    )

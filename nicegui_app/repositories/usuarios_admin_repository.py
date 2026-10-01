from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_profiles() -> list[dict[str, Any]]:
    return rest_select(
        "profiles",
        select="id,nome,email,foto_url,role,status,created_at,updated_at,ultimo_login_em",
        params={"order": "nome.asc"},
    )


def get_profile(profile_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "profiles",
        select="id,nome,email,foto_url,role,status,created_at,updated_at,ultimo_login_em",
        params={"id": f"eq.{profile_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def update_profile_access(
    profile_id: str,
    *,
    role: str,
    status: str,
) -> dict[str, Any] | None:
    return rest_update(
        "profiles",
        match={"id": profile_id},
        payload={
            "role": role,
            "status": status,
        },
    )


def count_active_admins() -> int:
    rows = rest_select(
        "profiles",
        select="id",
        params={
            "role": "eq.admin",
            "status": "eq.Ativo",
        },
    )
    return len(rows)


def append_profile_audit(
    *,
    actor_id: str | None,
    target_profile_id: str,
    previous_data: dict[str, Any],
    new_data: dict[str, Any],
) -> None:
    # Nunca incluir token, cookie, segredo ou qualquer credencial neste payload.
    rest_insert(
        "audit_logs",
        {
            "usuario_id": actor_id,
            "acao": "Atualização de acesso",
            "entidade": "profiles",
            "entidade_id": target_profile_id,
            "descricao": "Perfil de acesso do usuário atualizado pela Administração.",
            "dados_anteriores": previous_data,
            "dados_novos": new_data,
        },
    )



def list_particular_access() -> list[dict[str, Any]]:
    return rest_select(
        "particular_user_access_view",
        select=(
            "profile_id,has_particular_access,particular_access_id,"
            "particular_role,particular_status,granted_at,revoked_at,notes"
        ),
        params={"order": "nome.asc"},
    )


def get_particular_access(profile_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "particular_user_access",
        select="id,profile_id,module_role,status,granted_by,granted_at,revoked_by,revoked_at,revocation_reason,notes",
        params={"profile_id": f"eq.{profile_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def insert_particular_access(
    profile_id: str,
    *,
    module_role: str,
    granted_by: str | None,
) -> dict[str, Any] | None:
    return rest_insert(
        "particular_user_access",
        {
            "profile_id": profile_id,
            "module_role": module_role,
            "status": "ACTIVE",
            "granted_by": granted_by,
            "revoked_by": None,
            "revoked_at": None,
            "revocation_reason": None,
        },
    )


def update_particular_access(
    access_id: str,
    *,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return rest_update(
        "particular_user_access",
        match={"id": access_id},
        payload=payload,
    )

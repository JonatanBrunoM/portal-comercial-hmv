from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_insert, rest_select, rest_update


def list_credentials_by_portal(portal_id: str, *, active_only: bool = False) -> list[dict[str, Any]]:
    params = {"portal_id": f"eq.{portal_id}", "order": "identificacao.asc"}
    if active_only:
        params["status"] = "eq.Ativo"
    return rest_select("portal_credenciais", select="*", params=params)


def get_credential(credential_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "portal_credenciais",
        select="*",
        params={"id": f"eq.{credential_id}", "limit": "1"},
    )
    return rows[0] if rows else None



def get_active_profile(*, profile_id: str = "", email: str = "") -> dict[str, Any] | None:
    params: dict[str, str] = {"limit": "1"}

    if profile_id.strip():
        params["id"] = f"eq.{profile_id.strip()}"
    elif email.strip():
        params["email"] = f"ilike.{email.strip().lower()}"
    else:
        return None

    rows = rest_select(
        "profiles",
        select="id,nome,email,role,status",
        params=params,
    )
    if not rows:
        return None

    profile = rows[0]
    if str(profile.get("status") or "").strip().lower() != "ativo":
        return None
    return profile


def create_credential(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("portal_credenciais", payload)


def update_credential(credential_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_update(
        "portal_credenciais",
        match={"id": credential_id},
        payload=payload,
    )


def list_credential_history(credential_id: str) -> list[dict[str, Any]]:
    return rest_select(
        "historico_credenciais",
        select="*",
        params={
            "credencial_id": f"eq.{credential_id}",
            "order": "alterado_em.desc",
        },
    )


def append_credential_history(payload: dict[str, Any]) -> dict[str, Any] | None:
    return rest_insert("historico_credenciais", payload)


def append_credential_audit(
    *,
    actor_id: str | None,
    action: str,
    credential_id: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    rest_insert(
        "audit_logs",
        {
            "usuario_id": actor_id,
            "acao": action,
            "entidade": "portal_credenciais",
            "entidade_id": credential_id,
            "descricao": description,
            "dados_anteriores": None,
            "dados_novos": metadata or {},
        },
    )

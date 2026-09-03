from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


class AdminAccessError(PermissionError):
    """Acesso administrativo recusado pelo estado atual do perfil no banco."""


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def get_current_admin_profile(actor: dict[str, Any]) -> dict[str, Any] | None:
    """Revalida o administrador diretamente na tabela profiles.

    Não confia apenas no role/status armazenado na sessão, pois as operações
    administrativas usam uma credencial server-side privilegiada do Supabase.
    """
    profile_id = str(actor.get("profile_id") or actor.get("id") or "").strip()
    email = str(actor.get("email") or "").strip().lower()

    rows: list[dict[str, Any]] = []

    if profile_id:
        rows = rest_select(
            "profiles",
            select="id,nome,email,role,status,foto_url",
            params={"id": f"eq.{profile_id}", "limit": "1"},
        )
    elif email:
        rows = rest_select(
            "profiles",
            select="id,nome,email,role,status,foto_url",
            params={"email": f"eq.{email}", "limit": "1"},
        )

    if not rows:
        return None

    profile = rows[0]
    if _text(profile, "role").lower() != "admin":
        return None
    if _text(profile, "status").lower() != "ativo":
        return None

    return profile


def require_current_admin(actor: dict[str, Any]) -> dict[str, Any]:
    profile = get_current_admin_profile(actor)
    if not profile:
        raise AdminAccessError(
            "Seu acesso administrativo não está mais ativo. "
            "Atualize a página ou entre novamente."
        )

    # Mantém os dados úteis da sessão, mas sobrescreve o que é sensível
    # à autorização com o estado atual do banco.
    refreshed = dict(actor)
    refreshed["profile_id"] = _text(profile, "id")
    refreshed["role"] = _text(profile, "role")
    refreshed["status"] = _text(profile, "status")
    refreshed["name"] = _text(profile, "nome") or refreshed.get("name")
    refreshed["email"] = _text(profile, "email") or refreshed.get("email")
    refreshed["picture"] = _text(profile, "foto_url") or refreshed.get("picture")
    return refreshed

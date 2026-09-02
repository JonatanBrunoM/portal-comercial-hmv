from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from nicegui_app.repositories.profiles_repository import (
    create_profile,
    find_profile_by_email,
    update_profile,
)


class ProfileAccessDenied(PermissionError):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_google_profile(
    *,
    email: str,
    name: str,
    picture: str,
    google_sub: str,
) -> dict[str, Any]:
    """
    Localiza ou provisiona um profile institucional e registra o login.

    profiles permanece desacoplada de auth.users: a identidade é vinculada
    pelo e-mail institucional e pelo subject estável emitido pelo Google.
    """
    normalized_email = email.strip().lower()
    now = _now_iso()

    profile = find_profile_by_email(normalized_email)

    if profile is None:
        return create_profile(
            {
                "nome": name or normalized_email.split("@", 1)[0],
                "email": normalized_email,
                "foto_url": picture or None,
                "google_sub": google_sub,
                "auth_provider": "google",
                "role": "usuario",
                "status": "Ativo",
                "primeiro_acesso_em": now,
                "ultimo_acesso_em": now,
                "ultimo_login_em": now,
                "updated_at": now,
            }
        )

    if profile.get("status") != "Ativo":
        raise ProfileAccessDenied(
            "inactive",
            "O perfil institucional está inativo.",
        )

    stored_sub = str(profile.get("google_sub") or "").strip()
    if stored_sub and stored_sub != google_sub:
        raise ProfileAccessDenied(
            "identity",
            "A identidade Google não corresponde ao vínculo existente.",
        )

    updates: dict[str, Any] = {
        "google_sub": google_sub,
        "auth_provider": "google",
        "ultimo_acesso_em": now,
        "ultimo_login_em": now,
        "updated_at": now,
    }

    if name:
        updates["nome"] = name
    if picture:
        updates["foto_url"] = picture
    if not profile.get("primeiro_acesso_em"):
        updates["primeiro_acesso_em"] = now

    return update_profile(str(profile["id"]), updates)

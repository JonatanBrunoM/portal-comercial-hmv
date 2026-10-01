from __future__ import annotations

import logging

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from nicegui_app.auth.admin_access import require_current_admin

from nicegui_app.repositories.usuarios_admin_repository import (
    append_profile_audit,
    count_active_admins,
    get_profile,
    get_particular_access,
    insert_particular_access,
    list_particular_access,
    list_profiles,
    update_particular_access,
    update_profile_access,
)


VALID_ROLES = {"usuario", "admin"}
VALID_STATUSES = {"Ativo", "Inativo"}
VALID_PARTICULAR_ROLES = {"OPERATOR", "MANAGER"}



logger = logging.getLogger(__name__)

def _text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    return str(value or "").strip()


def _format_datetime(value: Any) -> str:
    if not value:
        return "Ainda não registrado"

    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return raw[:16].replace("T", " ")


@dataclass(frozen=True, slots=True)
class ManagedProfile:
    profile_id: str
    name: str
    email: str
    role: str
    status: str
    last_login: str
    updated_at: str
    particular_access: bool = False
    particular_role: str = ""
    particular_status: str = ""


def _to_profile(row: dict[str, Any]) -> ManagedProfile:
    return ManagedProfile(
        profile_id=_text(row, "id"),
        name=_text(row, "nome") or "Usuário institucional",
        email=_text(row, "email"),
        role=_text(row, "role") or "usuario",
        status=_text(row, "status") or "Ativo",
        last_login=_format_datetime(row.get("ultimo_login_em")),
        updated_at=_format_datetime(row.get("updated_at") or row.get("created_at")),
    )


def get_managed_profiles() -> list[ManagedProfile]:
    access_by_profile = {
        _text(row, "profile_id"): row
        for row in list_particular_access()
        if _text(row, "profile_id")
    }
    profiles: list[ManagedProfile] = []
    for row in list_profiles():
        base = _to_profile(row)
        access = access_by_profile.get(base.profile_id, {})
        profiles.append(
            ManagedProfile(
                profile_id=base.profile_id,
                name=base.name,
                email=base.email,
                role=base.role,
                status=base.status,
                last_login=base.last_login,
                updated_at=base.updated_at,
                particular_access=bool(access.get("has_particular_access")),
                particular_role=_text(access, "particular_role"),
                particular_status=_text(access, "particular_status"),
            )
        )
    return profiles


def save_particular_access(
    *,
    profile_id: str,
    enabled: bool,
    module_role: str,
    actor: dict,
) -> None:
    actor = require_current_admin(actor)
    module_role = str(module_role or "").strip().upper()
    if enabled and module_role not in VALID_PARTICULAR_ROLES:
        raise ValueError("Perfil do módulo Particular inválido.")

    if not get_profile(profile_id):
        raise ValueError("Usuário não encontrado.")

    actor_id = str(actor.get("profile_id") or actor.get("id") or "").strip() or None
    current = get_particular_access(profile_id)
    now = datetime.now(timezone.utc).isoformat()

    if enabled:
        if current:
            update_particular_access(
                _text(current, "id"),
                payload={
                    "module_role": module_role,
                    "status": "ACTIVE",
                    "granted_by": actor_id,
                    "granted_at": now,
                    "revoked_by": None,
                    "revoked_at": None,
                    "revocation_reason": None,
                    "updated_at": now,
                },
            )
        else:
            insert_particular_access(
                profile_id,
                module_role=module_role,
                granted_by=actor_id,
            )
        return

    if current and _text(current, "status") == "ACTIVE":
        update_particular_access(
            _text(current, "id"),
            payload={
                "status": "INACTIVE",
                "revoked_by": actor_id,
                "revoked_at": now,
                "revocation_reason": "Acesso revogado pela Administração do Portal.",
                "updated_at": now,
            },
        )


def save_profile_access(
    *,
    profile_id: str,
    role: str,
    status: str,
    actor: dict,
) -> ManagedProfile:
    actor = require_current_admin(actor)

    role = str(role or "").strip().lower()
    status = str(status or "").strip().title()

    if role not in VALID_ROLES:
        raise ValueError("Perfil de acesso inválido.")

    if status not in VALID_STATUSES:
        raise ValueError("Status de usuário inválido.")

    current = get_profile(profile_id)
    if not current:
        raise ValueError("Usuário não encontrado.")

    actor_id = str(actor.get("profile_id") or "").strip()
    actor_email = str(actor.get("email") or "").strip().lower()
    target_email = _text(current, "email").lower()

    is_self = bool(
        (actor_id and actor_id == profile_id)
        or (actor_email and actor_email == target_email)
    )

    old_role = _text(current, "role").lower() or "usuario"
    old_status = _text(current, "status").title() or "Ativo"

    # Evita que o administrador derrube o próprio acesso por engano.
    if is_self and (role != "admin" or status != "Ativo"):
        raise ValueError(
            "Seu próprio usuário deve permanecer como Administrador e Ativo."
        )

    # Protege o último administrador ativo mesmo em alterações feitas por outro admin.
    losing_admin_access = (
        old_role == "admin"
        and old_status == "Ativo"
        and (role != "admin" or status != "Ativo")
    )
    if losing_admin_access and count_active_admins() <= 1:
        raise ValueError("O portal precisa manter pelo menos um administrador ativo.")

    updated = update_profile_access(
        profile_id,
        role=role,
        status=status,
    )
    if not updated:
        raise RuntimeError("O Supabase não retornou o perfil atualizado.")

    previous_audit = {
        "role": old_role,
        "status": old_status,
        "email": _text(current, "email"),
    }
    new_audit = {
        "role": role,
        "status": status,
        "email": _text(current, "email"),
    }

    try:
        append_profile_audit(
            actor_id=actor_id or None,
            target_profile_id=profile_id,
            previous_data=previous_audit,
            new_data=new_audit,
        )
    except Exception:
        # A alteração principal não é revertida se apenas o log falhar.
        # A UI informa sucesso da alteração; o logging técnico permanece no servidor.
        pass

    return _to_profile(updated)

from __future__ import annotations

import logging

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from nicegui_app.auth.admin_access import require_current_admin

from nicegui_app.repositories.usuarios_admin_repository import (
    append_profile_audit,
    count_active_admins,
    get_profile,
    list_profiles,
    update_profile_access,
)


VALID_ROLES = {"usuario", "admin"}
VALID_STATUSES = {"Ativo", "Inativo"}



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
    return [_to_profile(row) for row in list_profiles()]


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

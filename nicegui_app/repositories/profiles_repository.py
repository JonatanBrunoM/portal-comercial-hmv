from __future__ import annotations

from typing import Any

import httpx

from nicegui_app.data.supabase_client import (
    get_supabase_server_key,
    get_supabase_url,
)


def _headers(*, prefer: str | None = None) -> dict[str, str]:
    key = get_supabase_server_key()

    headers = {
        "apikey": key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if not key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {key}"

    if prefer:
        headers["Prefer"] = prefer

    return headers


def find_profile_by_email(email: str) -> dict[str, Any] | None:
    response = httpx.get(
        f"{get_supabase_url()}/rest/v1/profiles",
        headers=_headers(),
        params={
            "select": (
                "id,nome,email,foto_url,role,status,primeiro_acesso_em,"
                "ultimo_acesso_em,google_sub,auth_provider,ultimo_login_em"
            ),
            "email": f"ilike.{email}",
            "limit": "1",
        },
        timeout=15.0,
    )
    response.raise_for_status()

    rows = response.json()
    if not isinstance(rows, list) or not rows:
        return None

    row = rows[0]
    return dict(row) if isinstance(row, dict) else None


def create_profile(payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(
        f"{get_supabase_url()}/rest/v1/profiles",
        headers=_headers(prefer="return=representation"),
        json=payload,
        timeout=15.0,
    )
    response.raise_for_status()

    rows = response.json()
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        raise RuntimeError("O Supabase não retornou o perfil criado.")

    return dict(rows[0])


def update_profile(
    profile_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = httpx.patch(
        f"{get_supabase_url()}/rest/v1/profiles",
        headers=_headers(prefer="return=representation"),
        params={"id": f"eq.{profile_id}"},
        json=payload,
        timeout=15.0,
    )
    response.raise_for_status()

    rows = response.json()
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        raise RuntimeError("O Supabase não retornou o perfil atualizado.")

    return dict(rows[0])

from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


ADMIN_TABLES = (
    "operadoras",
    "planos",
    "portais",
    "documentos",
    "contatos",
    "consultores",
    "comunicados",
    "contingencias",
)


def _list(table: str, *, select: str = "*", order: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    params: dict[str, str] = {}

    if order:
        params["order"] = order

    if limit is not None:
        params["limit"] = str(limit)

    return rest_select(table, select=select, params=params)


def load_admin_counts() -> dict[str, int]:
    counts: dict[str, int] = {}

    for table in ADMIN_TABLES:
        try:
            counts[table] = len(_list(table, select="id"))
        except Exception:
            counts[table] = 0

    try:
        counts["profiles"] = len(_list("profiles", select="id"))
    except Exception:
        counts["profiles"] = 0

    try:
        counts["portal_credenciais"] = len(_list("portal_credenciais", select="id"))
    except Exception:
        counts["portal_credenciais"] = 0

    return counts


def list_profiles_admin() -> list[dict[str, Any]]:
    try:
        return _list(
            "profiles",
            select="id,nome,email,foto_url,role,status,created_at,updated_at",
            order="nome.asc",
        )
    except Exception:
        return []


def list_recent_audit_logs_admin(limit: int = 8) -> list[dict[str, Any]]:
    try:
        return _list(
            "audit_logs",
            select="*",
            order="created_at.desc",
            limit=limit,
        )
    except Exception:
        return []

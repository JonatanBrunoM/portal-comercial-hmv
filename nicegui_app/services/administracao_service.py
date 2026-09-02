from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from nicegui_app.repositories.administracao_repository import (
    list_profiles_admin,
    list_recent_audit_logs_admin,
    load_admin_counts,
)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _format_datetime(value: Any) -> str:
    if not value:
        return ""

    raw = str(value).strip()

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return raw[:16].replace("T", " ")


@dataclass(frozen=True, slots=True)
class AdminProfile:
    profile_id: str
    name: str
    email: str
    role: str
    status: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class AuditPreview:
    action: str
    entity: str
    actor: str
    created_at: str
    detail: str


def get_admin_overview() -> dict[str, int]:
    return load_admin_counts()


def get_admin_profiles() -> list[AdminProfile]:
    profiles: list[AdminProfile] = []

    for row in list_profiles_admin():
        profiles.append(
            AdminProfile(
                profile_id=_text(row, "id"),
                name=_text(row, "nome") or "Usuário institucional",
                email=_text(row, "email"),
                role=_text(row, "role") or "usuario",
                status=_text(row, "status") or "Não informado",
                updated_at=_format_datetime(row.get("updated_at") or row.get("created_at")),
            )
        )

    return profiles


def get_recent_audit_logs() -> list[AuditPreview]:
    logs: list[AuditPreview] = []

    for row in list_recent_audit_logs_admin():
        action = _text(row, "acao", "action", "evento", "event") or "Alteração"
        entity = _text(
            row,
            "entidade",
            "entity",
            "tabela",
            "table_name",
            "recurso",
            "resource",
        )
        actor = _text(
            row,
            "usuario_email",
            "actor_email",
            "email",
            "alterado_por",
            "created_by",
        )
        detail = _text(
            row,
            "descricao",
            "description",
            "detalhes",
            "details",
            "observacoes",
        )

        logs.append(
            AuditPreview(
                action=action,
                entity=entity or "Portal Comercial",
                actor=actor or "Sistema",
                created_at=_format_datetime(row.get("created_at")),
                detail=detail,
            )
        )

    return logs

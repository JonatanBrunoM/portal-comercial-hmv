from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any
from zoneinfo import ZoneInfo

from nicegui_app.repositories.auditoria_repository import (
    list_audit_logs_admin,
    list_audit_profiles_admin,
)


_SENSITIVE_FRAGMENTS = (
    "senha",
    "password",
    "secret",
    "token",
    "cipher",
    "criptograf",
    "authorization",
    "apikey",
    "api_key",
)

_SP_TZ = ZoneInfo("America/Sao_Paulo")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _is_sensitive_key(key: str) -> bool:
    normalized = _text(key).casefold()
    return any(fragment in normalized for fragment in _SENSITIVE_FRAGMENTS)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                safe[str(key)] = "[conteúdo protegido]"
            else:
                safe[str(key)] = _sanitize(item)
        return safe

    if isinstance(value, list):
        return [_sanitize(item) for item in value]

    return value


def _format_payload(value: Any) -> str:
    if value in (None, "", {}, []):
        return ""

    safe = _sanitize(value)
    try:
        return json.dumps(
            safe,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:
        return _text(safe)


def _parse_datetime(value: Any) -> datetime | None:
    raw = _text(value)
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))

    return parsed.astimezone(_SP_TZ)


def _format_datetime(value: Any) -> str:
    parsed = _parse_datetime(value)
    if parsed is None:
        return _text(value)
    return parsed.strftime("%d/%m/%Y às %H:%M")


def _entity_label(value: str) -> str:
    labels = {
        "portal_credenciais": "Credenciais",
        "profiles": "Usuários",
        "operadoras": "Operadoras",
        "planos": "Planos",
        "portais": "Portais",
        "documentos": "Documentos",
        "contatos": "Contatos",
        "consultores": "Consultores",
        "carteiras": "Carteiras",
        "comunicados": "Comunicados",
        "contingencias": "Contingências",
        "autorizacoes": "Autorizações",
        "elegibilidade": "Elegibilidade",
        "coberturas": "Coberturas",
    }
    return labels.get(value, value.replace("_", " ").title() if value else "Portal Comercial")


@dataclass(frozen=True, slots=True)
class AuditActor:
    profile_id: str
    name: str
    email: str


@dataclass(frozen=True, slots=True)
class AuditEntry:
    log_id: str
    actor_id: str
    actor_name: str
    actor_email: str
    action: str
    entity: str
    entity_label: str
    entity_id: str
    description: str
    before_json: str
    after_json: str
    created_at: str
    created_at_iso: str


@dataclass(frozen=True, slots=True)
class AuditData:
    entries: tuple[AuditEntry, ...]
    actors: tuple[AuditActor, ...]
    actions: tuple[str, ...]
    entities: tuple[str, ...]


def get_audit_data(limit: int = 300) -> AuditData:
    profiles = list_audit_profiles_admin()
    actors_by_id: dict[str, AuditActor] = {}

    for row in profiles:
        profile_id = _text(row.get("id"))
        if not profile_id:
            continue
        actor = AuditActor(
            profile_id=profile_id,
            name=_text(row.get("nome")) or "Usuário institucional",
            email=_text(row.get("email")),
        )
        actors_by_id[profile_id] = actor

    entries: list[AuditEntry] = []
    actions: set[str] = set()
    entities: set[str] = set()

    for row in list_audit_logs_admin(limit=limit):
        actor_id = _text(row.get("usuario_id"))
        actor = actors_by_id.get(actor_id)

        action = _text(row.get("acao")) or "Alteração"
        entity = _text(row.get("entidade")) or "portal_comercial"

        actions.add(action)
        entities.add(entity)

        parsed = _parse_datetime(row.get("created_at"))

        entries.append(
            AuditEntry(
                log_id=_text(row.get("id")),
                actor_id=actor_id,
                actor_name=actor.name if actor else "Sistema",
                actor_email=actor.email if actor else "",
                action=action,
                entity=entity,
                entity_label=_entity_label(entity),
                entity_id=_text(row.get("entidade_id")),
                description=_text(row.get("descricao")),
                before_json=_format_payload(row.get("dados_anteriores")),
                after_json=_format_payload(row.get("dados_novos")),
                created_at=_format_datetime(row.get("created_at")),
                created_at_iso=parsed.isoformat() if parsed else "",
            )
        )

    return AuditData(
        entries=tuple(entries),
        actors=tuple(sorted(actors_by_id.values(), key=lambda item: item.name.casefold())),
        actions=tuple(sorted(actions, key=str.casefold)),
        entities=tuple(sorted(entities, key=str.casefold)),
    )


def filter_audit_entries(
    entries: tuple[AuditEntry, ...],
    *,
    query: str = "",
    action: str = "Todas",
    entity: str = "Todas",
    actor_id: str = "Todos",
) -> list[AuditEntry]:
    normalized = _text(query).casefold()

    result: list[AuditEntry] = []
    for item in entries:
        if action != "Todas" and item.action != action:
            continue
        if entity != "Todas" and item.entity != entity:
            continue
        if actor_id != "Todos" and item.actor_id != actor_id:
            continue

        if normalized:
            haystack = " ".join(
                (
                    item.action,
                    item.entity_label,
                    item.actor_name,
                    item.actor_email,
                    item.description,
                    item.entity_id,
                )
            ).casefold()
            if normalized not in haystack:
                continue

        result.append(item)

    return result

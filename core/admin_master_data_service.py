from __future__ import annotations

import re
import unicodedata

import pandas as pd

from core.data_service import clear_data_cache
from core.supabase_repository import (
    append_audit_event,
    delete_record,
    fetch_by_id,
    fetch_records,
    insert_record,
    update_record,
)


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value).strip("_")
    return ascii_value.upper()[:60]


def _clean_optional(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _required(value: str | None, message: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(message)
    return cleaned


def get_all_operators() -> pd.DataFrame:
    return fetch_records("operadoras", order_by="nome")


def get_all_plans() -> pd.DataFrame:
    return fetch_records("planos", order_by="nome")


def get_all_locations() -> pd.DataFrame:
    return fetch_records("locais_atendimento", order_by="nome")


def get_all_attendance_types() -> pd.DataFrame:
    return fetch_records("tipos_atendimento", order_by="nome")


def get_plan_location_ids(plan_id: str) -> list[str]:
    if not plan_id:
        return []

    links = fetch_records(
        "plano_locais",
        filters={"plano_id": plan_id},
    )
    if links.empty or "local_id" not in links.columns:
        return []

    return [
        str(value)
        for value in links["local_id"].dropna().tolist()
    ]


def save_operator(
    *,
    operator_id: str | None,
    code: str,
    name: str,
    short_name: str | None,
    site_url: str | None,
    logo_url: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    name = _required(name, "Informe o nome da operadora.")
    code = (code or "").strip() or _slug(name)

    payload = {
        "codigo": code,
        "nome": name,
        "nome_curto": _clean_optional(short_name),
        "site_url": _clean_optional(site_url),
        "logo_url": _clean_optional(logo_url),
        "observacoes": _clean_optional(observations),
        "status": status,
    }

    if operator_id:
        previous = fetch_by_id("operadoras", operator_id) or {}
        result = update_record("operadoras", operator_id, payload)
        append_audit_event(
            action="operadora_atualizada",
            entity="operadoras",
            entity_id=operator_id,
            description=f"Operadora '{name}' atualizada.",
            previous_data=previous,
            new_data=result or payload,
        )
    else:
        result = insert_record("operadoras", payload)
        append_audit_event(
            action="operadora_criada",
            entity="operadoras",
            entity_id=(result or {}).get("id"),
            description=f"Operadora '{name}' criada.",
            new_data=result or payload,
        )

    clear_data_cache()
    return result


def save_plan(
    *,
    plan_id: str | None,
    code: str,
    operator_id: str,
    name: str,
    standardized_name: str | None,
    plan_type: str | None,
    summary: str | None,
    status: str,
    location_ids: list[str] | None = None,
) -> dict | None:
    if not operator_id:
        raise ValueError("Selecione a operadora do plano.")

    name = _required(name, "Informe o nome do plano.")
    code = (code or "").strip() or _slug(name)

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "nome": name,
        "nome_padronizado": _clean_optional(standardized_name),
        "tipo_plano": _clean_optional(plan_type),
        "observacao_resumida": _clean_optional(summary),
        "status": status,
    }

    if plan_id:
        previous = fetch_by_id("planos", plan_id) or {}
        result = update_record("planos", plan_id, payload)
        effective_plan_id = plan_id
        action = "plano_atualizado"
        description = f"Plano '{name}' atualizado."
    else:
        previous = {}
        result = insert_record("planos", payload)
        effective_plan_id = str((result or {}).get("id") or "")
        action = "plano_criado"
        description = f"Plano '{name}' criado."

    if not effective_plan_id:
        raise RuntimeError("O plano foi salvo, mas não foi possível identificar seu registro.")

    sync_plan_locations(
        plan_id=effective_plan_id,
        location_ids=location_ids or [],
        register_audit=False,
    )

    append_audit_event(
        action=action,
        entity="planos",
        entity_id=effective_plan_id,
        description=description,
        previous_data=previous or None,
        new_data=result or payload,
    )

    clear_data_cache()
    return result


def save_location(
    *,
    location_id: str | None,
    code: str,
    name: str,
    status: str,
) -> dict | None:
    name = _required(name, "Informe o nome do local de atendimento.")
    code = (code or "").strip() or _slug(name)

    payload = {
        "codigo": code,
        "nome": name,
        "status": status,
    }

    if location_id:
        previous = fetch_by_id("locais_atendimento", location_id) or {}
        result = update_record("locais_atendimento", location_id, payload)
        append_audit_event(
            action="local_atendimento_atualizado",
            entity="locais_atendimento",
            entity_id=location_id,
            description=f"Local de atendimento '{name}' atualizado.",
            previous_data=previous,
            new_data=result or payload,
        )
    else:
        result = insert_record("locais_atendimento", payload)
        append_audit_event(
            action="local_atendimento_criado",
            entity="locais_atendimento",
            entity_id=(result or {}).get("id"),
            description=f"Local de atendimento '{name}' criado.",
            new_data=result or payload,
        )

    clear_data_cache()
    return result


def save_attendance_type(
    *,
    attendance_type_id: str | None,
    code: str,
    name: str,
    status: str,
) -> dict | None:
    name = _required(name, "Informe o tipo de atendimento.")
    code = (code or "").strip() or _slug(name)

    payload = {
        "codigo": code,
        "nome": name,
        "status": status,
    }

    if attendance_type_id:
        previous = fetch_by_id("tipos_atendimento", attendance_type_id) or {}
        result = update_record("tipos_atendimento", attendance_type_id, payload)
        append_audit_event(
            action="tipo_atendimento_atualizado",
            entity="tipos_atendimento",
            entity_id=attendance_type_id,
            description=f"Tipo de atendimento '{name}' atualizado.",
            previous_data=previous,
            new_data=result or payload,
        )
    else:
        result = insert_record("tipos_atendimento", payload)
        append_audit_event(
            action="tipo_atendimento_criado",
            entity="tipos_atendimento",
            entity_id=(result or {}).get("id"),
            description=f"Tipo de atendimento '{name}' criado.",
            new_data=result or payload,
        )

    clear_data_cache()
    return result


def sync_plan_locations(
    *,
    plan_id: str,
    location_ids: list[str],
    register_audit: bool = True,
) -> None:
    if not plan_id:
        raise ValueError("Informe o plano para relacionar os locais.")

    desired = {str(value) for value in (location_ids or []) if value}
    current_df = fetch_records(
        "plano_locais",
        filters={"plano_id": plan_id},
    )

    current_by_location: dict[str, str] = {}
    if not current_df.empty:
        for _, row in current_df.iterrows():
            location_id = str(row.get("local_id") or "")
            link_id = str(row.get("id") or "")
            if location_id and link_id:
                current_by_location[location_id] = link_id

    current = set(current_by_location)
    to_add = desired - current
    to_remove = current - desired

    for location_id in to_add:
        insert_record(
            "plano_locais",
            {
                "plano_id": plan_id,
                "local_id": location_id,
            },
        )

    for location_id in to_remove:
        delete_record(
            "plano_locais",
            current_by_location[location_id],
        )

    if register_audit and (to_add or to_remove):
        append_audit_event(
            action="plano_locais_atualizados",
            entity="plano_locais",
            entity_id=plan_id,
            description="Locais vinculados ao plano atualizados.",
            previous_data={"local_ids": sorted(current)},
            new_data={"local_ids": sorted(desired)},
        )

    clear_data_cache()

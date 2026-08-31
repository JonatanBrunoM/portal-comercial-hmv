from __future__ import annotations

import re
import unicodedata

import pandas as pd

from core.data_service import clear_data_cache
from core.supabase_repository import (
    append_audit_event,
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


def _validate_relations(
    *,
    operator_id: str,
    plan_id: str | None,
) -> None:
    if not operator_id:
        raise ValueError("Selecione a operadora.")

    if not plan_id:
        return

    plan = fetch_by_id("planos", plan_id)
    if not plan:
        raise ValueError("O plano selecionado não foi encontrado.")

    if str(plan.get("operadora_id") or "") != str(operator_id):
        raise ValueError("O plano selecionado não pertence à operadora informada.")


def get_all_eligibility() -> pd.DataFrame:
    return fetch_records("elegibilidade", order_by="updated_at", ascending=False)


def get_all_authorizations() -> pd.DataFrame:
    return fetch_records("autorizacoes", order_by="updated_at", ascending=False)


def get_all_coverages() -> pd.DataFrame:
    return fetch_records("coberturas", order_by="updated_at", ascending=False)


def get_all_documents() -> pd.DataFrame:
    return fetch_records("documentos", order_by="updated_at", ascending=False)


def _save_rule(
    *,
    table: str,
    record_id: str | None,
    payload: dict,
    action_prefix: str,
    label: str,
) -> dict | None:
    if record_id:
        previous = fetch_by_id(table, record_id) or {}
        result = update_record(table, record_id, payload)
        action = f"{action_prefix}_atualizada"
        description = f"{label} atualizada."
    else:
        previous = None
        result = insert_record(table, payload)
        record_id = str((result or {}).get("id") or "")
        action = f"{action_prefix}_criada"
        description = f"{label} criada."

    append_audit_event(
        action=action,
        entity=table,
        entity_id=record_id or (result or {}).get("id"),
        description=description,
        previous_data=previous,
        new_data=result or payload,
    )
    clear_data_cache()
    return result


def save_eligibility(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    location_id: str | None,
    attendance_type_id: str | None,
    required: bool,
    guidance: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    _validate_relations(operator_id=operator_id, plan_id=plan_id)
    code = (code or "").strip() or _slug(f"ELEG_{operator_id}_{plan_id or 'GERAL'}")

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "tipo_atendimento_id": attendance_type_id,
        "necessario": bool(required),
        "orientacao": _clean_optional(guidance),
        "observacoes": _clean_optional(observations),
        "status": status,
    }
    return _save_rule(
        table="elegibilidade",
        record_id=record_id,
        payload=payload,
        action_prefix="elegibilidade",
        label="Regra de elegibilidade",
    )


def save_authorization(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    location_id: str | None,
    attendance_type_id: str | None,
    requires_authorization: bool,
    authorization_moment: str | None,
    requester: str | None,
    request_channel: str | None,
    deadline: str | None,
    guidance: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    _validate_relations(operator_id=operator_id, plan_id=plan_id)
    code = (code or "").strip() or _slug(f"AUT_{operator_id}_{plan_id or 'GERAL'}")

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "tipo_atendimento_id": attendance_type_id,
        "necessita_autorizacao": bool(requires_authorization),
        "momento_autorizacao": _clean_optional(authorization_moment),
        "quem_solicita": _clean_optional(requester),
        "meio_solicitacao": _clean_optional(request_channel),
        "prazo": _clean_optional(deadline),
        "orientacao": _clean_optional(guidance),
        "observacoes": _clean_optional(observations),
        "status": status,
    }
    return _save_rule(
        table="autorizacoes",
        record_id=record_id,
        payload=payload,
        action_prefix="autorizacao",
        label="Regra de autorização",
    )


def save_coverage(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    location_id: str | None,
    attendance_type_id: str | None,
    covered: bool | None,
    restrictions: str | None,
    accommodation: str | None,
    companion: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    _validate_relations(operator_id=operator_id, plan_id=plan_id)
    code = (code or "").strip() or _slug(f"COB_{operator_id}_{plan_id or 'GERAL'}")

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "tipo_atendimento_id": attendance_type_id,
        "coberto": covered,
        "restricoes_cobertura": _clean_optional(restrictions),
        "acomodacao": _clean_optional(accommodation),
        "acompanhante": _clean_optional(companion),
        "observacoes": _clean_optional(observations),
        "status": status,
    }
    return _save_rule(
        table="coberturas",
        record_id=record_id,
        payload=payload,
        action_prefix="cobertura",
        label="Regra de cobertura",
    )


def save_document(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    location_id: str | None,
    attendance_type_id: str | None,
    name: str,
    mandatory: bool,
    file_format: str | None,
    validity_days: int | None,
    guidance: str | None,
    observations: str | None,
    file_url: str | None,
    status: str,
) -> dict | None:
    _validate_relations(operator_id=operator_id, plan_id=plan_id)
    name = _required(name, "Informe o nome do documento.")
    code = (code or "").strip() or _slug(name)

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "tipo_atendimento_id": attendance_type_id,
        "nome": name,
        "obrigatorio": bool(mandatory),
        "formato": _clean_optional(file_format),
        "validade_dias": validity_days,
        "orientacao": _clean_optional(guidance),
        "observacoes": _clean_optional(observations),
        "arquivo_url": _clean_optional(file_url),
        "status": status,
    }
    return _save_rule(
        table="documentos",
        record_id=record_id,
        payload=payload,
        action_prefix="documento",
        label=f"Documento '{name}'",
    )

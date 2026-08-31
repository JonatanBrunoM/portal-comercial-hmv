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


def _validate_operator_plan(
    *,
    operator_id: str | None,
    plan_id: str | None,
    operator_required: bool = False,
) -> None:
    if operator_required and not operator_id:
        raise ValueError("Selecione a operadora.")

    if not plan_id:
        return

    plan = fetch_by_id("planos", plan_id)
    if not plan:
        raise ValueError("O plano selecionado não foi encontrado.")

    plan_operator_id = str(plan.get("operadora_id") or "")
    if not operator_id:
        raise ValueError("Ao selecionar um plano, informe também a operadora.")

    if plan_operator_id != str(operator_id):
        raise ValueError("O plano selecionado não pertence à operadora informada.")


def _save(
    *,
    table: str,
    record_id: str | None,
    payload: dict,
    create_action: str,
    update_action: str,
    description: str,
) -> dict | None:
    if record_id:
        previous = fetch_by_id(table, record_id) or {}
        result = update_record(table, record_id, payload)
        action = update_action
        entity_id = record_id
    else:
        previous = None
        result = insert_record(table, payload)
        action = create_action
        entity_id = str((result or {}).get("id") or "")

    append_audit_event(
        action=action,
        entity=table,
        entity_id=entity_id or None,
        description=description,
        previous_data=previous,
        new_data=result or payload,
    )
    clear_data_cache()
    return result


def get_all_contacts() -> pd.DataFrame:
    return fetch_records("contatos", order_by="updated_at", ascending=False)


def get_all_consultants() -> pd.DataFrame:
    return fetch_records("consultores", order_by="nome")


def get_all_wallets() -> pd.DataFrame:
    return fetch_records("carteiras", order_by="updated_at", ascending=False)


def get_all_announcements() -> pd.DataFrame:
    return fetch_records("comunicados", order_by="updated_at", ascending=False)


def get_all_contingencies() -> pd.DataFrame:
    return fetch_records("contingencias", order_by="updated_at", ascending=False)


def get_all_tips() -> pd.DataFrame:
    return fetch_records("dicas_operacionais", order_by="updated_at", ascending=False)


def save_contact(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    sector_name: str,
    purpose: str | None,
    contact_type: str | None,
    contact: str,
    responsible: str | None,
    service_hours: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    _validate_operator_plan(
        operator_id=operator_id,
        plan_id=plan_id,
        operator_required=True,
    )

    sector_name = _required(sector_name, "Informe o setor ou nome do contato.")
    contact = _required(contact, "Informe o contato.")
    code = (code or "").strip() or _slug(f"{sector_name}_{operator_id}")

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "nome_setor": sector_name,
        "finalidade": _clean_optional(purpose),
        "tipo": _clean_optional(contact_type),
        "contato": contact,
        "responsavel": _clean_optional(responsible),
        "horario_atendimento": _clean_optional(service_hours),
        "observacoes": _clean_optional(observations),
        "status": status,
    }

    return _save(
        table="contatos",
        record_id=record_id,
        payload=payload,
        create_action="contato_criado",
        update_action="contato_atualizado",
        description=f"Contato '{sector_name}' salvo.",
    )


def save_consultant(
    *,
    record_id: str | None,
    code: str,
    name: str,
    role_title: str | None,
    email: str | None,
    phone: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    name = _required(name, "Informe o nome do consultor.")
    code = (code or "").strip() or _slug(name)

    payload = {
        "codigo": code,
        "nome": name,
        "cargo": _clean_optional(role_title),
        "email": _clean_optional(email),
        "telefone": _clean_optional(phone),
        "observacoes": _clean_optional(observations),
        "status": status,
    }

    return _save(
        table="consultores",
        record_id=record_id,
        payload=payload,
        create_action="consultor_criado",
        update_action="consultor_atualizado",
        description=f"Consultor '{name}' salvo.",
    )


def save_wallet(
    *,
    record_id: str | None,
    consultant_id: str,
    operator_id: str,
    plan_id: str | None,
    role: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    if not consultant_id:
        raise ValueError("Selecione o consultor.")

    consultant = fetch_by_id("consultores", consultant_id)
    if not consultant:
        raise ValueError("O consultor selecionado não foi encontrado.")

    _validate_operator_plan(
        operator_id=operator_id,
        plan_id=plan_id,
        operator_required=True,
    )

    payload = {
        "consultor_id": consultant_id,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "papel": _clean_optional(role),
        "observacoes": _clean_optional(observations),
        "status": status,
    }

    return _save(
        table="carteiras",
        record_id=record_id,
        payload=payload,
        create_action="carteira_criada",
        update_action="carteira_atualizada",
        description="Vínculo de consultor com operadora/plano salvo.",
    )


def save_announcement(
    *,
    record_id: str | None,
    code: str,
    operator_id: str | None,
    title: str,
    summary: str | None,
    content: str,
    category: str | None,
    priority: str,
    target_audience: str | None,
    start_at: str | None,
    end_at: str | None,
    featured: bool,
    status: str,
    responsible: str | None,
) -> dict | None:
    title = _required(title, "Informe o título do comunicado.")
    content = _required(content, "Informe o conteúdo do comunicado.")
    code = (code or "").strip() or _slug(title)

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "titulo": title,
        "resumo": _clean_optional(summary),
        "conteudo": content,
        "categoria": _clean_optional(category),
        "prioridade": priority,
        "publico_alvo": _clean_optional(target_audience),
        "inicio_em": start_at,
        "fim_em": end_at,
        "destaque": bool(featured),
        "status": status,
        "responsavel": _clean_optional(responsible),
    }

    return _save(
        table="comunicados",
        record_id=record_id,
        payload=payload,
        create_action="comunicado_criado",
        update_action="comunicado_atualizado",
        description=f"Comunicado '{title}' salvo.",
    )


def save_contingency(
    *,
    record_id: str | None,
    code: str,
    operator_id: str | None,
    plan_id: str | None,
    location_id: str | None,
    title: str,
    description: str,
    alternative_guidance: str | None,
    alternative_contact: str | None,
    priority: str,
    start_at: str | None,
    end_at: str | None,
    status: str,
) -> dict | None:
    _validate_operator_plan(
        operator_id=operator_id,
        plan_id=plan_id,
        operator_required=False,
    )

    title = _required(title, "Informe o título da contingência.")
    description = _required(description, "Informe a descrição da contingência.")
    code = (code or "").strip() or _slug(title)

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "titulo": title,
        "descricao": description,
        "orientacao_alternativa": _clean_optional(alternative_guidance),
        "contato_alternativo": _clean_optional(alternative_contact),
        "prioridade": priority,
        "inicio_em": start_at,
        "fim_em": end_at,
        "status": status,
    }

    return _save(
        table="contingencias",
        record_id=record_id,
        payload=payload,
        create_action="contingencia_criada",
        update_action="contingencia_atualizada",
        description=f"Contingência '{title}' salva.",
    )


def save_tip(
    *,
    record_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    location_id: str | None,
    title: str,
    category: str | None,
    tip: str,
    keywords: str | None,
    featured: bool,
    status: str,
) -> dict | None:
    _validate_operator_plan(
        operator_id=operator_id,
        plan_id=plan_id,
        operator_required=True,
    )

    title = _required(title, "Informe o título da dica.")
    tip = _required(tip, "Informe a orientação da dica.")
    code = (code or "").strip() or _slug(title)

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "titulo": title,
        "categoria": _clean_optional(category),
        "dica": tip,
        "palavras_chave": _clean_optional(keywords),
        "destaque": bool(featured),
        "status": status,
    }

    return _save(
        table="dicas_operacionais",
        record_id=record_id,
        payload=payload,
        create_action="dica_operacional_criada",
        update_action="dica_operacional_atualizada",
        description=f"Dica operacional '{title}' salva.",
    )

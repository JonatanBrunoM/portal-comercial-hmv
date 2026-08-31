from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

import pandas as pd

from core.credentials_service import encrypt_password
from core.data_service import clear_data_cache
from core.supabase_repository import (
    append_audit_event,
    delete_record,
    fetch_by_id,
    fetch_records,
    insert_record,
    update_record,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value).strip("_")
    return ascii_value.upper()[:60]


def _clean_optional(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def get_all_portals() -> pd.DataFrame:
    return fetch_records("portais", order_by="nome")


def get_all_credentials(portal_id: str) -> pd.DataFrame:
    if not portal_id:
        return pd.DataFrame()
    return fetch_records(
        "portal_credenciais",
        filters={"portal_id": portal_id},
        order_by="updated_at",
        ascending=False,
    )


def save_portal(
    *,
    portal_id: str | None,
    code: str,
    operator_id: str,
    plan_id: str | None,
    location_id: str | None,
    name: str,
    portal_type: str | None,
    url: str | None,
    requires_login: bool,
    access_instruction: str | None,
    general_tip: str | None,
    observations: str | None,
    status: str,
) -> dict | None:
    code = (code or "").strip() or _slug(name)
    name = (name or "").strip()

    if not code:
        raise ValueError("Informe o código do portal.")
    if not operator_id:
        raise ValueError("Selecione a operadora.")
    if not name:
        raise ValueError("Informe o nome do portal.")

    payload = {
        "codigo": code,
        "operadora_id": operator_id,
        "plano_id": plan_id,
        "local_id": location_id,
        "nome": name,
        "tipo": _clean_optional(portal_type),
        "url": _clean_optional(url),
        "exige_login": bool(requires_login),
        "instrucao_acesso": _clean_optional(access_instruction),
        "dica_geral_acesso": _clean_optional(general_tip),
        "observacoes": _clean_optional(observations),
        "status": status,
    }

    if portal_id:
        previous = fetch_by_id("portais", portal_id) or {}
        result = update_record("portais", portal_id, payload)
        append_audit_event(
            action="portal_atualizado",
            entity="portais",
            entity_id=portal_id,
            description=f"Portal '{name}' atualizado.",
            previous_data=previous,
            new_data=result or payload,
        )
    else:
        result = insert_record("portais", payload)
        append_audit_event(
            action="portal_criado",
            entity="portais",
            entity_id=(result or {}).get("id"),
            description=f"Portal '{name}' criado.",
            new_data=result or payload,
        )

    clear_data_cache()
    return result


def save_credential(
    *,
    credential_id: str | None,
    portal_id: str,
    identification: str,
    login: str | None,
    new_password: str | None,
    access_tip: str | None,
    observations: str | None,
    blocked_password_count: int,
    password_rule: str | None,
    status: str,
    change_reason: str | None = None,
) -> dict | None:
    if not portal_id:
        raise ValueError("Selecione o portal da credencial.")

    identification = (identification or "").strip()
    if not identification:
        raise ValueError("Informe a identificação da credencial.")

    if not credential_id and not (new_password or "").strip():
        raise ValueError("Informe a senha para cadastrar uma nova credencial.")

    base_payload = {
        "portal_id": portal_id,
        "identificacao": identification,
        "login": _clean_optional(login),
        "dica_acesso": _clean_optional(access_tip),
        "observacoes": _clean_optional(observations),
        "quantidade_senhas_bloqueadas": int(blocked_password_count or 0),
        "regra_senha_observacao": _clean_optional(password_rule),
        "status": status,
    }

    password = (new_password or "").strip()

    if not credential_id:
        base_payload["senha_criptografada"] = encrypt_password(password)
        base_payload["senha_alterada_em"] = _utc_now_iso()
        result = insert_record("portal_credenciais", base_payload)
        append_audit_event(
            action="credencial_criada",
            entity="portal_credenciais",
            entity_id=(result or {}).get("id"),
            description="Credencial de portal criada.",
            new_data={
                "portal_id": portal_id,
                "identificacao": identification,
                "status": status,
                "senha_alterada": True,
            },
        )
        return result

    previous = fetch_by_id("portal_credenciais", credential_id)
    if not previous:
        raise ValueError("A credencial selecionada não foi encontrada.")

    history_record_id: str | None = None

    if password:
        old_ciphertext = previous.get("senha_criptografada")
        history_payload = {
            "credencial_id": credential_id,
            "alterado_por": None,
            "login": previous.get("login"),
            "senha_criptografada": old_ciphertext,
            "motivo_alteracao": _clean_optional(change_reason) or "Alteração administrativa de senha",
            "alterado_em": _utc_now_iso(),
            "dica_acesso": previous.get("dica_acesso"),
        }

        # O histórico é gravado antes da substituição da senha. Caso a atualização
        # da credencial falhe, o registro de histórico é removido para evitar um
        # estado incoerente.
        history = insert_record("historico_credenciais", history_payload)
        history_record_id = (history or {}).get("id")
        base_payload["senha_criptografada"] = encrypt_password(password)
        base_payload["senha_alterada_em"] = _utc_now_iso()

    try:
        result = update_record("portal_credenciais", credential_id, base_payload)
    except Exception:
        if history_record_id:
            try:
                delete_record("historico_credenciais", history_record_id)
            except Exception:
                pass
        raise

    append_audit_event(
        action="credencial_atualizada",
        entity="portal_credenciais",
        entity_id=credential_id,
        description="Credencial de portal atualizada.",
        previous_data={
            "portal_id": previous.get("portal_id"),
            "identificacao": previous.get("identificacao"),
            "status": previous.get("status"),
        },
        new_data={
            "portal_id": portal_id,
            "identificacao": identification,
            "status": status,
            "senha_alterada": bool(password),
        },
    )
    return result

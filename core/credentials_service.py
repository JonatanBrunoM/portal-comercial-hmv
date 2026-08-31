from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken

from core.supabase_repository import (
    append_audit_event,
    fetch_records,
)

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class DecryptionResult:
    value: str | None
    status: str


def _get_fernet() -> Fernet | None:
    """Obtém a chave de criptografia sem expor seu valor."""
    try:
        key = st.secrets["SECURITY"]["FERNET_KEY"]
    except Exception:
        return None

    if not key:
        return None

    try:
        return Fernet(str(key).encode("utf-8"))
    except Exception:
        return None


def decrypt_password(ciphertext: str | None) -> DecryptionResult:
    """
    Descriptografa uma senha Fernet.

    Nunca registra o conteúdo descriptografado em log, cache ou banco.
    """
    if not ciphertext:
        return DecryptionResult(None, "empty")

    # A massa fictícia criada durante o desenvolvimento é intencionalmente
    # não descriptografável e deve permanecer claramente identificada.
    if str(ciphertext).startswith("CREDENCIAL_FICTICIA_"):
        return DecryptionResult(None, "test_data")

    fernet = _get_fernet()
    if fernet is None:
        return DecryptionResult(None, "missing_key")

    try:
        value = fernet.decrypt(str(ciphertext).encode("utf-8")).decode("utf-8")
        return DecryptionResult(value, "ok")
    except (InvalidToken, ValueError, TypeError):
        return DecryptionResult(None, "invalid")


def encrypt_password(plaintext: str) -> str:
    """Criptografa uma senha antes da persistência no Supabase."""
    fernet = _get_fernet()
    if fernet is None:
        raise RuntimeError(
            "A chave de criptografia das credenciais não está configurada."
        )

    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def get_portal_credentials(portal_id: str) -> pd.DataFrame:
    """
    Busca credenciais ativas de um portal diretamente no Supabase.

    Credenciais não utilizam st.cache_data para reduzir o tempo de permanência
    de dados sensíveis na memória compartilhada do aplicativo.
    """
    if not portal_id:
        return pd.DataFrame()

    dataframe = fetch_records(
        "portal_credenciais",
        filters={
            "portal_id": portal_id,
            "status": "Ativo",
        },
        order_by="updated_at",
        ascending=False,
    )

    return dataframe.reset_index(drop=True)


def get_credential_history(credential_id: str) -> pd.DataFrame:
    """Histórico de senha disponível somente para administradores."""
    profile = st.session_state.get("auth_profile") or {}
    if profile.get("role") != "admin":
        return pd.DataFrame()

    if not credential_id:
        return pd.DataFrame()

    return fetch_records(
        "historico_credenciais",
        filters={"credencial_id": credential_id},
        order_by="alterado_em",
        ascending=False,
    ).reset_index(drop=True)


def log_password_reveal(
    *,
    credential_id: str,
    portal_id: str,
    portal_name: str,
) -> None:
    """
    Registra que uma credencial foi visualizada sem salvar login ou senha
    no audit log.
    """
    append_audit_event(
        action="credencial_visualizada",
        entity="portal_credenciais",
        entity_id=credential_id,
        description=f"Visualização de credencial do portal {portal_name}.",
        new_data={
            "portal_id": portal_id,
            "evento": "visualizacao_de_senha",
        },
    )


def format_timestamp(value: object) -> str:
    if value is None or pd.isna(value):
        return "Não informado"

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "Não informado"

    parsed = pd.Timestamp(parsed)

    if parsed.tzinfo is not None:
        parsed = parsed.tz_convert(BRAZIL_TZ)
    else:
        parsed = parsed.tz_localize(BRAZIL_TZ)

    return parsed.strftime("%d/%m/%Y %H:%M")

from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


class CredentialCryptoConfigurationError(RuntimeError):
    pass


def _key() -> str:
    value = os.getenv("PORTAL_CREDENTIALS_FERNET_KEY", "").strip()
    if not value:
        raise CredentialCryptoConfigurationError(
            "PORTAL_CREDENTIALS_FERNET_KEY não está configurada no servidor."
        )
    return value


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    try:
        return Fernet(_key().encode("utf-8"))
    except Exception as exc:
        raise CredentialCryptoConfigurationError(
            "PORTAL_CREDENTIALS_FERNET_KEY é inválida."
        ) from exc


def encrypt_password(password: str) -> str:
    value = password.strip()
    if not value:
        raise ValueError("Informe a senha.")
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_password(token: str) -> str:
    if not token:
        raise ValueError("A credencial não possui senha armazenada.")
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Não foi possível descriptografar esta senha com a chave configurada."
        ) from exc

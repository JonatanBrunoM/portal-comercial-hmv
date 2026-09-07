from __future__ import annotations

from dataclasses import dataclass
import os

from nicegui_app.auth.google_oauth import google_oauth_is_configured
from nicegui_app.data.supabase_client import check_supabase_connection
from nicegui_app.security.credentials_crypto import (
    CredentialCryptoConfigurationError,
    encrypt_password,
)


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    ok: bool
    checks: tuple[ReadinessCheck, ...]


def _env_present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def get_readiness_report() -> ReadinessReport:
    checks: list[ReadinessCheck] = []

    required_env = (
        "PORTAL_SESSION_SECRET",
        "PORTAL_CREDENTIALS_FERNET_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "PORTAL_BASE_URL",
    )

    for name in required_env:
        checks.append(
            ReadinessCheck(
                name=name,
                ok=_env_present(name),
                detail="configurada" if _env_present(name) else "ausente",
            )
        )

    oauth_ok = google_oauth_is_configured()
    checks.append(
        ReadinessCheck(
            name="Google OAuth",
            ok=oauth_ok,
            detail="configurado" if oauth_ok else "incompleto",
        )
    )

    try:
        # Valida o formato da chave Fernet sem revelar chave ou ciphertext.
        encrypt_password("__portal_readiness_probe__")
        crypto_ok = True
        crypto_detail = "chave válida"
    except CredentialCryptoConfigurationError:
        crypto_ok = False
        crypto_detail = "chave ausente ou inválida"
    except Exception:
        crypto_ok = False
        crypto_detail = "falha ao validar criptografia"

    checks.append(
        ReadinessCheck(
            name="Criptografia de credenciais",
            ok=crypto_ok,
            detail=crypto_detail,
        )
    )

    supabase_ok, supabase_message = check_supabase_connection()
    checks.append(
        ReadinessCheck(
            name="Supabase",
            ok=supabase_ok,
            detail="conectado" if supabase_ok else "indisponível",
        )
    )

    return ReadinessReport(
        ok=all(check.ok for check in checks),
        checks=tuple(checks),
    )

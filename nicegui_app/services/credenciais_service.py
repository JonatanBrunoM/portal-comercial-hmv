

import hmac
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from nicegui_app.auth.admin_access import require_current_admin
from nicegui_app.repositories.credenciais_repository import (
    append_credential_audit,
    append_credential_history,
    create_credential,
    get_active_profile,
    get_credential,
    list_credential_history,
    list_credentials_by_portal,
    update_credential,
)
from nicegui_app.security.credentials_crypto import (
    CredentialCryptoConfigurationError,
    decrypt_password,
    encrypt_password,
)


logger = logging.getLogger(__name__)


class CredentialAccessError(PermissionError):
    pass


class CredentialSecurityError(RuntimeError):
    pass


def _text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _actor_profile(actor: dict[str, Any]) -> dict[str, Any]:
    profile = get_active_profile(
        profile_id=str(actor.get("profile_id") or actor.get("id") or ""),
        email=str(actor.get("email") or ""),
    )
    if not profile:
        raise CredentialAccessError(
            "Seu perfil não está mais ativo. Atualize a página ou entre novamente."
        )
    return profile


def _audit(
    *,
    actor_id: str | None,
    action: str,
    credential_id: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Auditoria sem senha, ciphertext ou conteúdo sensível."""
    try:
        append_credential_audit(
            actor_id=actor_id,
            action=action,
            credential_id=credential_id,
            description=description,
            metadata=metadata or {},
        )
    except Exception:
        # A falha de auditoria não expõe payload nem segredo em log.
        logger.exception(
            "Falha ao registrar auditoria de credencial. acao=%s credencial_id=%s",
            action,
            credential_id,
        )


@dataclass(frozen=True, slots=True)
class CredentialPreview:
    credential_id: str
    portal_id: str
    identification: str
    login: str
    access_tip: str
    notes: str
    status: str
    password_changed_at: str
    blocked_passwords: int
    password_rule: str


def _preview(row: dict[str, Any]) -> CredentialPreview:
    return CredentialPreview(
        credential_id=_text(row, "id"),
        portal_id=_text(row, "portal_id"),
        identification=_text(row, "identificacao") or "Acesso principal",
        login=_text(row, "login"),
        access_tip=_text(row, "dica_acesso"),
        notes=_text(row, "observacoes"),
        status=_text(row, "status") or "Ativo",
        password_changed_at=_text(row, "senha_alterada_em"),
        blocked_passwords=max(0, int(row.get("quantidade_senhas_bloqueadas") or 0)),
        password_rule=_text(row, "regra_senha_observacao"),
    )


def get_public_credentials(portal_id: str) -> list[CredentialPreview]:
    return [
        _preview(row)
        for row in list_credentials_by_portal(portal_id, active_only=True)
    ]


def get_admin_credentials(portal_id: str, actor: dict) -> list[CredentialPreview]:
    require_current_admin(actor)
    return [_preview(row) for row in list_credentials_by_portal(portal_id)]


def reveal_password(
    credential_id: str,
    actor: dict,
    *,
    action: str = "Visualização de senha",
) -> str:
    profile = _actor_profile(actor)
    row = get_credential(credential_id)

    if not row or _text(row, "status") != "Ativo":
        raise ValueError("Credencial ativa não encontrada.")

    try:
        password = decrypt_password(_text(row, "senha_criptografada"))
    except CredentialCryptoConfigurationError:
        logger.error("Chave Fernet de credenciais ausente ou inválida.")
        raise CredentialSecurityError(
            "O serviço seguro de credenciais não está disponível no momento."
        ) from None
    except Exception:
        logger.exception(
            "Falha de descriptografia de credencial. credencial_id=%s",
            credential_id,
        )
        raise CredentialSecurityError(
            "Não foi possível acessar esta credencial com segurança."
        ) from None

    _audit(
        actor_id=_text(profile, "id") or None,
        action=action,
        credential_id=credential_id,
        description="Acesso autorizado à senha de portal.",
        metadata={"portal_id": _text(row, "portal_id")},
    )
    return password


def _password_was_used(
    *,
    candidate: str,
    current: dict[str, Any],
    history: list[dict[str, Any]],
) -> bool:
    encrypted_values = [_text(current, "senha_criptografada")]
    encrypted_values.extend(
        _text(row, "senha_criptografada")
        for row in history
        if _text(row, "senha_criptografada")
    )

    for encrypted in encrypted_values:
        if not encrypted:
            continue
        try:
            previous_password = decrypt_password(encrypted)
        except CredentialCryptoConfigurationError:
            logger.error("Chave Fernet de credenciais ausente ou inválida.")
            raise CredentialSecurityError(
                "Não é possível validar o histórico de senhas no momento."
            ) from None
        except Exception:
            # Fail closed: se uma versão histórica não puder ser validada,
            # a troca não prossegue.
            logger.exception(
                "Falha ao validar histórico criptografado. credencial_id=%s",
                _text(current, "id"),
            )
            raise CredentialSecurityError(
                "O histórico desta credencial precisa ser validado antes da troca de senha."
            ) from None

        if hmac.compare_digest(candidate, previous_password):
            return True

    return False


def save_credential(
    *,
    credential_id: str | None,
    portal_id: str,
    identification: str,
    login: str,
    password: str,
    access_tip: str,
    notes: str,
    status: str,
    blocked_passwords: int,
    password_rule: str,
    change_reason: str,
    actor: dict,
) -> None:
    admin = require_current_admin(actor)

    portal_id = portal_id.strip()
    login = login.strip()
    identification = identification.strip() or "Acesso principal"
    status = status.strip()
    password = password.strip()
    change_reason = change_reason.strip()

    if not portal_id:
        raise ValueError("Portal inválido.")
    if not login:
        raise ValueError("Informe o login.")
    if status not in {"Ativo", "Inativo"}:
        raise ValueError("Status inválido.")
    if blocked_passwords < 0:
        raise ValueError("A quantidade de senhas bloqueadas não pode ser negativa.")

    actor_id = str(admin.get("profile_id") or admin.get("id") or "").strip() or None
    now = datetime.now(timezone.utc).isoformat()
    previous = get_credential(credential_id) if credential_id else None

    if credential_id and not previous:
        raise ValueError("Credencial não encontrada.")

    password_changed = bool(password)

    if not credential_id and not password_changed:
        raise ValueError("Informe a senha inicial.")

    if credential_id and password_changed:
        if not change_reason:
            raise ValueError("Informe o motivo da troca de senha.")

        history = list_credential_history(credential_id)

        # A nova senha é validada ANTES de qualquer gravação.
        if _password_was_used(
            candidate=password,
            current=previous,
            history=history,
        ):
            raise ValueError(
                "Esta senha já foi utilizada nesta credencial. Informe uma senha diferente."
            )

    payload: dict[str, Any] = {
        "portal_id": portal_id,
        "identificacao": identification,
        "login": login,
        "dica_acesso": access_tip.strip() or None,
        "observacoes": notes.strip() or None,
        "status": status,
        "quantidade_senhas_bloqueadas": blocked_passwords,
        "regra_senha_observacao": password_rule.strip() or None,
        "updated_at": now,
    }

    if password_changed:
        try:
            # A senha é criptografada antes de qualquer persistência.
            encrypted_new_password = encrypt_password(password)
        except CredentialCryptoConfigurationError:
            logger.error("Chave Fernet de credenciais ausente ou inválida.")
            raise CredentialSecurityError(
                "O serviço seguro de credenciais não está disponível no momento."
            ) from None

        payload["senha_criptografada"] = encrypted_new_password
        payload["senha_alterada_em"] = now

    if credential_id and password_changed:
        # Só depois de todas as validações a versão atual vai ao histórico.
        append_credential_history(
            {
                "credencial_id": credential_id,
                "alterado_por": actor_id,
                "login": _text(previous, "login"),
                "senha_criptografada": _text(previous, "senha_criptografada"),
                "motivo_alteracao": change_reason,
                "dica_acesso": _text(previous, "dica_acesso") or None,
            }
        )

    saved = (
        update_credential(credential_id, payload)
        if credential_id
        else create_credential(
            {
                **payload,
                "senha_criptografada": payload["senha_criptografada"],
                "senha_alterada_em": now,
            }
        )
    )

    if not saved:
        raise RuntimeError("Não foi possível confirmar o salvamento da credencial.")

    _audit(
        actor_id=actor_id,
        action="Atualização de credencial" if credential_id else "Cadastro de credencial",
        credential_id=str(saved.get("id") or credential_id or ""),
        description="Credencial de portal alterada pela Administração.",
        metadata={
            "portal_id": portal_id,
            "identificacao": identification,
            "status": status,
            "senha_alterada": password_changed,
        },
    )


def get_admin_history(
    credential_id: str,
    actor: dict,
) -> list[dict[str, Any]]:
    require_current_admin(actor)
    return list_credential_history(credential_id)

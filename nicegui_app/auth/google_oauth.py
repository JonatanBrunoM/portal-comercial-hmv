from __future__ import annotations

import logging
import os

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Request
from starlette.responses import RedirectResponse

from nicegui_app.services.profile_service import (
    ProfileAccessDenied,
    resolve_google_profile,
)


logger = logging.getLogger(__name__)

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
ALLOWED_DOMAIN = "hmv.org.br"

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID", "").strip(),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    client_kwargs={"scope": "openid email profile"},
)


def google_oauth_is_configured() -> bool:
    return bool(
        os.getenv("GOOGLE_CLIENT_ID", "").strip()
        and os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        and os.getenv("PORTAL_BASE_URL", "").strip()
    )


def _callback_url() -> str:
    base_url = os.getenv("PORTAL_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PORTAL_BASE_URL não está configurada.")
    return f"{base_url}/auth/google/callback"


async def start_google_login(request: Request) -> RedirectResponse:
    if not google_oauth_is_configured():
        return RedirectResponse("/login?error=config", status_code=303)

    return await oauth.google.authorize_redirect(
        request,
        _callback_url(),
        prompt="select_account",
        hd=ALLOWED_DOMAIN,
    )


async def finish_google_login(request: Request) -> RedirectResponse:
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")

        if not userinfo:
            userinfo = await oauth.google.userinfo(token=token)

        email = str(userinfo.get("email") or "").strip().lower()
        email_verified = bool(userinfo.get("email_verified"))
        google_sub = str(userinfo.get("sub") or "").strip()

        if (
            not email
            or not google_sub
            or not email_verified
            or not email.endswith(f"@{ALLOWED_DOMAIN}")
        ):
            logger.warning(
                "Login Google recusado por política institucional. "
                "email_verified=%s domain_ok=%s",
                email_verified,
                email.endswith(f"@{ALLOWED_DOMAIN}") if email else False,
            )
            return RedirectResponse("/login?error=domain", status_code=303)

        profile = resolve_google_profile(
            email=email,
            name=str(userinfo.get("name") or "").strip(),
            picture=str(userinfo.get("picture") or "").strip(),
            google_sub=google_sub,
        )

        request.session["portal_auth"] = {
            "authenticated": True,
            "profile_id": profile["id"],
            "name": profile.get("nome") or "",
            "email": profile["email"],
            "role": profile.get("role") or "usuario",
            "status": profile.get("status") or "",
            "picture": profile.get("foto_url") or "",
        }

        logger.info(
            "Login institucional concluído. profile_id=%s role=%s",
            profile["id"],
            profile.get("role") or "usuario",
        )
        return RedirectResponse("/", status_code=303)

    except ProfileAccessDenied as error:
        logger.warning("Login recusado pelo perfil: %s", error.reason)
        return RedirectResponse(f"/login?error={error.code}", status_code=303)

    except OAuthError as error:
        logger.warning(
            "Falha OAuth Google. tipo=%s",
            type(error).__name__,
        )
        return RedirectResponse("/login?error=oauth", status_code=303)

    except Exception as error:
        logger.exception(
            "Falha inesperada no login institucional. tipo=%s",
            type(error).__name__,
        )
        return RedirectResponse("/login?error=unexpected", status_code=303)


def logout(request: Request) -> RedirectResponse:
    request.session.pop("portal_auth", None)
    return RedirectResponse("/login", status_code=303)


def get_session_user(request: Request) -> dict | None:
    user = request.session.get("portal_auth")
    if not isinstance(user, dict):
        return None
    if not user.get("authenticated"):
        return None
    if user.get("status") != "Ativo":
        return None
    return user

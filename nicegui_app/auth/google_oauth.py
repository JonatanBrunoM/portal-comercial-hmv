from __future__ import annotations

import logging
import os
import time
from urllib.parse import urlsplit

from itsdangerous import BadData, URLSafeTimedSerializer

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


# Authlib's temporary state must not share NiceGUI's browser session cookie:
# a late UI response can otherwise replace it with a pre-login snapshot.
_OAUTH_COOKIE = "portal_google_oauth"
_OAUTH_COOKIE_PATH = "/auth/google"
_OAUTH_TTL = 600


def _oauth_serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("PORTAL_SESSION_SECRET", "").strip()
    if not secret:
        if os.getenv("RENDER", "").strip():
            raise RuntimeError("PORTAL_SESSION_SECRET precisa ser configurada no Render.")
        secret = "local-development-only-change-me"
    return URLSafeTimedSerializer(secret, salt="portal-google-oauth-v1")


def _oauth_request(request: Request) -> Request:
    """A separate request scope keeps temporary OAuth data out of portal_auth."""
    session = {}
    cookie = request.cookies.get(_OAUTH_COOKIE)
    if cookie:
        try:
            value = _oauth_serializer().loads(cookie, max_age=_OAUTH_TTL)
            if isinstance(value, dict):
                session = value
        except BadData:
            pass  # Authlib rejects a missing, expired or tampered state.
    return Request({**request.scope, "session": session}, request.receive)


def _secure_oauth_cookie() -> bool:
    return urlsplit(_callback_url()).scheme == "https"


async def start_google_login(request: Request) -> RedirectResponse:
    if not google_oauth_is_configured():
        return RedirectResponse("/login?error=config", status_code=303)

    base_url = os.getenv("PORTAL_BASE_URL", "").strip().rstrip("/")
    if request.url.netloc != urlsplit(base_url).netloc:
        return RedirectResponse(f"{base_url}/auth/google/login", status_code=303)

    auth_request = _oauth_request(request)
    # Only one pending login per browser; retries replace the previous attempt.
    auth_request.session.clear()
    response = await oauth.google.authorize_redirect(
        auth_request,
        _callback_url(),
        prompt="select_account",
        hd=ALLOWED_DOMAIN,
    )
    response.set_cookie(
        _OAUTH_COOKIE,
        _oauth_serializer().dumps(auth_request.session),
        max_age=_OAUTH_TTL,
        path=_OAUTH_COOKIE_PATH,
        secure=_secure_oauth_cookie(),
        httponly=True,
        samesite="lax",  # Google's top-level GET callback must carry the cookie.
    )
    response.headers["Cache-Control"] = "no-store"
    return response


async def finish_google_login(request: Request) -> RedirectResponse:
    response = await _finish_google_login(request, _oauth_request(request))
    response.delete_cookie(
        _OAUTH_COOKIE, path=_OAUTH_COOKIE_PATH,
        secure=_secure_oauth_cookie(), httponly=True, samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


async def _finish_google_login(request: Request, auth_request: Request) -> RedirectResponse:
    started = time.monotonic()
    oauth_keys = [key for key in auth_request.session if key.startswith("_state_google_")]
    logger.info("Callback Google: state_presente=%s estados_oauth=%d", bool(request.query_params.get("state")), len(oauth_keys))
    try:
        token = await oauth.google.authorize_access_token(auth_request)
        logger.info("OAuth Google: token recebido em %.2fs", time.monotonic() - started)
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

        profile_started = time.monotonic()
        profile = resolve_google_profile(
            email=email,
            name=str(userinfo.get("name") or "").strip(),
            picture=str(userinfo.get("picture") or "").strip(),
            google_sub=google_sub,
        )

        logger.info("OAuth Google: perfil resolvido em %.2fs", time.monotonic() - profile_started)
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
            "Falha OAuth Google. tipo=%s codigo=%s descricao=%s tempo=%.2fs",
            type(error).__name__,
            str(getattr(error, "error", "") or "")[:100],
            str(getattr(error, "description", "") or "")[:180],
            time.monotonic() - started,
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

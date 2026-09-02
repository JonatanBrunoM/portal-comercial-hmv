from __future__ import annotations

import os

from fastapi import Request
from nicegui import app, ui
from starlette.responses import RedirectResponse

from nicegui_app.auth.google_oauth import (
    finish_google_login,
    get_session_user,
    logout,
    start_google_login,
)
from nicegui_app.pages.home import render_home
from nicegui_app.pages.login import render_login
from nicegui_app.pages.supabase_test import render_supabase_test
from nicegui_app.theme import apply_theme


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "application": "portal-comercial-nicegui-poc"}


@app.get("/auth/google/login")
async def google_login(request: Request):
    return await start_google_login(request)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    return await finish_google_login(request)


@app.get("/logout")
def portal_logout(request: Request):
    return logout(request)


@ui.page("/login")
def login_page(error: str | None = None) -> None:
    render_login(error)


@ui.page("/")
def index(request: Request):
    user = get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    apply_theme()
    render_home(user)
    return None


@ui.page("/supabase-test")
def supabase_test(request: Request):
    user = get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    apply_theme()
    render_supabase_test(user)
    return None


def _storage_secret() -> str:
    secret = os.getenv("PORTAL_SESSION_SECRET", "").strip()
    if secret:
        return secret

    if os.getenv("RENDER", "").strip():
        raise RuntimeError(
            "PORTAL_SESSION_SECRET precisa ser configurada no Render."
        )

    return "local-development-only-change-me"


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        title="Portal Comercial | Hospital Moinhos de Vento",
        favicon="🏥",
        reload=False,
        show=False,
        storage_secret=_storage_secret(),
    )

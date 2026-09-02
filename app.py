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
from nicegui_app.pages.comunicados import render_comunicado_detail, render_comunicados
from nicegui_app.pages.consultores import render_consultor_detail, render_consultores
from nicegui_app.pages.contatos import render_contato_detail, render_contatos
from nicegui_app.pages.documentos import render_documento_detail, render_documentos
from nicegui_app.pages.login import render_login
from nicegui_app.pages.portais import render_portal_detail, render_portais
from nicegui_app.pages.operadoras import (
    render_operadora_detail,
    render_operadoras,
)
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


def _authenticated_user(request: Request) -> dict | RedirectResponse:
    user = get_session_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user


@ui.page("/")
def index(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_home(user)
    return None


@ui.page("/operadoras")
def operators_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_operadoras(user)
    return None


@ui.page("/operadoras/{operator_id}")
def operator_detail_page(request: Request, operator_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_operadora_detail(user, operator_id)
    return None



@ui.page("/portais")
def portals_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_portais(user)
    return None


@ui.page("/portais/{portal_id}")
def portal_detail_page(request: Request, portal_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_portal_detail(user, portal_id)
    return None



@ui.page("/documentos")
def documents_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_documentos(user)
    return None


@ui.page("/documentos/{document_id}")
def document_detail_page(request: Request, document_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_documento_detail(user, document_id)
    return None



@ui.page("/contatos")
def contacts_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_contatos(user)
    return None


@ui.page("/contatos/{contact_id}")
def contact_detail_page(request: Request, contact_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_contato_detail(user, contact_id)
    return None



@ui.page("/consultores")
def consultants_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_consultores(user)
    return None


@ui.page("/consultores/{consultant_id}")
def consultant_detail_page(request: Request, consultant_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_consultor_detail(user, consultant_id)
    return None


@ui.page("/comunicados")
def communications_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse): return user
    apply_theme()
    render_comunicados(user)

@ui.page("/comunicados/{communication_id}")
def communication_detail_page(request: Request, communication_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse): return user
    apply_theme()
    render_comunicado_detail(user, communication_id)


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

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
from nicegui_app.auth.admin_access import get_current_admin_profile
from nicegui_app.pages.home import render_home
from nicegui_app.pages.administracao import render_administracao
from nicegui_app.pages.usuarios_admin import render_admin_usuarios
from nicegui_app.pages.cadastros_admin import render_admin_cadastros
from nicegui_app.pages.portais_admin import render_admin_portais
from nicegui_app.pages.credenciais_admin import render_admin_credenciais
from nicegui_app.pages.documentos_admin import render_admin_documentos
from nicegui_app.pages.contatos_admin import render_admin_contatos
from nicegui_app.pages.consultores_admin import render_admin_consultores
from nicegui_app.pages.comunicados_admin import render_admin_comunicados
from nicegui_app.pages.contingencias_admin import render_admin_contingencias
from nicegui_app.pages.pesquisa import render_pesquisa
from nicegui_app.pages.contingencias import render_contingencia_detail, render_contingencias
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
from nicegui_app.data.supabase_client import warm_public_data_cache


@app.on_startup
async def warm_portal_cache() -> None:
    """Aquece dados institucionais sem bloquear a inicialização da interface."""
    import asyncio

    asyncio.create_task(asyncio.to_thread(warm_public_data_cache))


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



def _admin_user(request: Request) -> dict | RedirectResponse:
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    profile = get_current_admin_profile(user)
    if not profile:
        return RedirectResponse("/", status_code=303)

    refreshed = dict(user)
    refreshed["profile_id"] = str(profile.get("id") or "").strip()
    refreshed["role"] = str(profile.get("role") or "").strip()
    refreshed["status"] = str(profile.get("status") or "").strip()
    refreshed["name"] = str(profile.get("nome") or refreshed.get("name") or "").strip()
    refreshed["email"] = str(profile.get("email") or refreshed.get("email") or "").strip()
    refreshed["picture"] = str(
        profile.get("foto_url") or refreshed.get("picture") or ""
    ).strip()

    return refreshed


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



@ui.page("/contingencias")
def contingencies_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user
    apply_theme()
    render_contingencias(user)


@ui.page("/contingencias/{contingency_id}")
def contingency_detail_page(request: Request, contingency_id: str):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user
    apply_theme()
    render_contingencia_detail(user, contingency_id)



@ui.page("/pesquisa")
def search_page(request: Request):
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_pesquisa(user)



@ui.page("/administracao")
def administration_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_administracao(user)
    return None



@ui.page("/administracao/usuarios")
def administration_users_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_usuarios(user)
    return None



@ui.page("/administracao/cadastros")
def administration_registers_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_cadastros(user)
    return None



@ui.page("/administracao/portais")
def administration_portals_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user
    apply_theme()
    render_admin_portais(user)
    return None



@ui.page("/administracao/credenciais")
def administration_credentials_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_credenciais(user)
    return None


@ui.page("/administracao/documentos")
def administration_documents_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_documentos(user)
    return None



@ui.page("/administracao/contatos")
def administration_contacts_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_contatos(user)
    return None



@ui.page("/administracao/consultores")
def administration_consultants_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_consultores(user)
    return None



@ui.page("/administracao/comunicados")
def administration_communications_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_comunicados(user)
    return None



@ui.page("/administracao/contingencias")
def administration_contingencies_page(request: Request):
    user = _admin_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()
    render_admin_contingencias(user)
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
        reconnect_timeout=15.0,
    )

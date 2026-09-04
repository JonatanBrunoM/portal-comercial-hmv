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
from nicegui_app.layout import portal_shell, spa_content_mode
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


def _render_spa_page(renderer, user: dict, *args) -> None:
    """Renderiza somente o conteúdo variável dentro do shell persistente."""
    with spa_content_mode():
        with ui.element("div").classes("portal-spa-page"):
            renderer(user, *args)


def _render_admin_spa_page(renderer, user: dict, *args) -> None:
    """Proteção de rota administrativa no shell.

    As mutações administrativas continuam revalidando o perfil no Supabase
    pelos services existentes.
    """
    if str(user.get("role") or "").strip().lower() != "admin":
        ui.navigate.to("/")
        return

    _render_spa_page(renderer, user, *args)


def _build_portal_routes(user: dict) -> dict[str, object]:
    return {
        "/": lambda: _render_spa_page(render_home, user),
        "/pesquisa": lambda: _render_spa_page(render_pesquisa, user),
        "/operadoras": lambda: _render_spa_page(render_operadoras, user),
        "/operadoras/{operator_id}": (
            lambda operator_id: _render_spa_page(
                render_operadora_detail,
                user,
                operator_id,
            )
        ),
        "/portais": lambda: _render_spa_page(render_portais, user),
        "/portais/{portal_id}": (
            lambda portal_id: _render_spa_page(
                render_portal_detail,
                user,
                portal_id,
            )
        ),
        "/documentos": lambda: _render_spa_page(render_documentos, user),
        "/documentos/{document_id}": (
            lambda document_id: _render_spa_page(
                render_documento_detail,
                user,
                document_id,
            )
        ),
        "/contatos": lambda: _render_spa_page(render_contatos, user),
        "/contatos/{contact_id}": (
            lambda contact_id: _render_spa_page(
                render_contato_detail,
                user,
                contact_id,
            )
        ),
        "/consultores": lambda: _render_spa_page(render_consultores, user),
        "/consultores/{consultant_id}": (
            lambda consultant_id: _render_spa_page(
                render_consultor_detail,
                user,
                consultant_id,
            )
        ),
        "/comunicados": lambda: _render_spa_page(render_comunicados, user),
        "/comunicados/{communication_id}": (
            lambda communication_id: _render_spa_page(
                render_comunicado_detail,
                user,
                communication_id,
            )
        ),
        "/contingencias": lambda: _render_spa_page(render_contingencias, user),
        "/contingencias/{contingency_id}": (
            lambda contingency_id: _render_spa_page(
                render_contingencia_detail,
                user,
                contingency_id,
            )
        ),
        "/administracao": (
            lambda: _render_admin_spa_page(render_administracao, user)
        ),
        "/administracao/usuarios": (
            lambda: _render_admin_spa_page(render_admin_usuarios, user)
        ),
        "/administracao/cadastros": (
            lambda: _render_admin_spa_page(render_admin_cadastros, user)
        ),
        "/administracao/portais": (
            lambda: _render_admin_spa_page(render_admin_portais, user)
        ),
        "/administracao/credenciais": (
            lambda: _render_admin_spa_page(render_admin_credenciais, user)
        ),
        "/administracao/documentos": (
            lambda: _render_admin_spa_page(render_admin_documentos, user)
        ),
        "/administracao/contatos": (
            lambda: _render_admin_spa_page(render_admin_contatos, user)
        ),
        "/administracao/consultores": (
            lambda: _render_admin_spa_page(render_admin_consultores, user)
        ),
        "/administracao/comunicados": (
            lambda: _render_admin_spa_page(render_admin_comunicados, user)
        ),
        "/administracao/contingencias": (
            lambda: _render_admin_spa_page(render_admin_contingencias, user)
        ),
    }


@ui.page("/")
@ui.page("/{_:path}")
def portal_page(request: Request) -> RedirectResponse | None:
    """Entrada única do Portal Comercial.

    ``ui.sub_pages`` troca apenas o conteúdo central via History API.
    Sidebar, topbar, sessão e conexão NiceGUI permanecem vivas entre módulos.
    """
    user = _authenticated_user(request)
    if isinstance(user, RedirectResponse):
        return user

    apply_theme()

    # Remove espaçamentos padrão do cliente NiceGUI; todo o layout é do Portal.
    ui.context.client.content.classes("p-0 gap-0")

    with portal_shell(user=user) as navigation:
        router = ui.sub_pages(
            _build_portal_routes(user),
            show_404=True,
        ).classes("portal-spa-router")

    client_router = ui.context.client.sub_pages_router
    client_router.on_path_changed(navigation.update)
    navigation.update(client_router.current_path)

    # Evita manter scroll intermediário ao trocar de módulo e acrescenta
    # feedback visual imediato sem bloquear a navegação.
    ui.add_head_html(
        """
        <script>
        (() => {
            if (window.__portalSpaNavigationInstalled) return;
            window.__portalSpaNavigationInstalled = true;

            const markNavigation = () => {
                document.documentElement.classList.add('portal-is-navigating');
                window.scrollTo({ top: 0, behavior: 'instant' });
                window.clearTimeout(window.__portalNavigationTimer);
                window.__portalNavigationTimer = window.setTimeout(
                    () => document.documentElement.classList.remove('portal-is-navigating'),
                    450,
                );
            };

            window.addEventListener('pushstate', markNavigation);
            window.addEventListener('popstate', markNavigation);
        })();
        </script>
        """
    )

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
        favicon="https://www.hospitalmoinhos.org.br/assets/images/logo-w-hopkins.png",
        reload=False,
        show=False,
        storage_secret=_storage_secret(),
        reconnect_timeout=15.0,
    )

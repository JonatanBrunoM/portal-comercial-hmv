from __future__ import annotations

from nicegui import ui

from nicegui_app.auth.google_oauth import google_oauth_is_configured
from nicegui_app.brand import BRAND_LOGO_WHITE
from nicegui_app.theme import apply_theme


ERROR_MESSAGES = {
    "config": "O login institucional ainda não foi configurado no servidor.",
    "domain": "Utilize uma conta institucional @hmv.org.br.",
    "inactive": "Seu acesso ao Portal Comercial está inativo.",
    "identity": "Não foi possível validar o vínculo desta conta institucional.",
    "oauth": "O Google não concluiu a autenticação. Tente novamente.",
    "unexpected": "Não foi possível concluir o login. Tente novamente.",
}


def render_login(error: str | None = None) -> None:
    apply_theme()

    with ui.element("main").classes("portal-login-shell"):
        with ui.element("section").classes("portal-login-brand-panel"):
            with ui.element("div").classes("portal-login-brand-glow"):
                pass

            with ui.element("div").classes("portal-login-brand-content"):
                with ui.element("header").classes("portal-login-brand-header"):
                    ui.image(BRAND_LOGO_WHITE).classes("portal-login-hmv-logo")
                    ui.label("PORTAL COMERCIAL").classes("portal-login-product-kicker")

                with ui.element("div").classes("portal-login-message"):
                    ui.label(
                        "A informação certa, quando a operação precisa."
                    ).classes("portal-login-headline")
                    ui.label(
                        "Um ambiente único para consultar operadoras, acessos, "
                        "documentos, contatos e orientações comerciais."
                    ).classes("portal-login-description")

                with ui.element("div").classes("portal-login-capabilities"):
                    for icon, title, detail in (
                        (
                            "search",
                            "Consulta centralizada",
                            "Encontre a informação sem percorrer arquivos e planilhas.",
                        ),
                        (
                            "vpn_key",
                            "Acessos protegidos",
                            "Credenciais e orientações reunidas com segurança.",
                        ),
                        (
                            "campaign",
                            "Operação atualizada",
                            "Comunicados e contingências no mesmo fluxo.",
                        ),
                    ):
                        with ui.element("article").classes("portal-login-capability"):
                            with ui.element("div").classes(
                                "portal-login-capability-icon"
                            ):
                                ui.icon(icon)
                            with ui.element("div").classes(
                                "portal-login-capability-copy"
                            ):
                                ui.label(title).classes(
                                    "portal-login-capability-title"
                                )
                                ui.label(detail).classes(
                                    "portal-login-capability-detail"
                                )

            with ui.element("div").classes("portal-login-brand-signature"):
                ui.icon("shield")
                ui.label("Ambiente institucional · Hospital Moinhos de Vento")

        with ui.element("section").classes("portal-login-access-panel"):
            with ui.element("div").classes("portal-login-access-wrap"):
                with ui.element("div").classes("portal-login-access-intro"):
                    ui.label("ACESSO INSTITUCIONAL").classes("portal-login-kicker")
                    ui.label("Bem-vindo ao Portal Comercial").classes(
                        "portal-login-title"
                    )
                    ui.label(
                        "Entre com sua conta corporativa para acessar informações "
                        "e ferramentas da operação."
                    ).classes("portal-login-card-description")

                if error in ERROR_MESSAGES:
                    with ui.element("div").classes("portal-login-alert"):
                        ui.icon("info_outline")
                        ui.label(ERROR_MESSAGES[error])

                if not google_oauth_is_configured():
                    with ui.element("div").classes("portal-login-config-warning"):
                        ui.icon("settings")
                        ui.label(
                            "As variáveis do Google OAuth ainda precisam "
                            "ser configuradas no Render."
                        )

                with ui.link(target="/auth/google/login").classes(
                    "portal-google-login-link"
                ):
                    with ui.element("div").classes("portal-google-login-button"):
                        with ui.element("div").classes("portal-google-symbol"):
                            ui.label("G")
                        with ui.element("div").classes("portal-google-login-copy"):
                            ui.label("Continuar com Google").classes(
                                "portal-google-login-title"
                            )
                            ui.label("Conta corporativa @hmv.org.br").classes(
                                "portal-google-login-subtitle"
                            )
                        ui.icon("arrow_forward").classes(
                            "portal-google-login-arrow"
                        )

                with ui.element("div").classes("portal-login-access-foot"):
                    with ui.element("div").classes("portal-login-trust-item"):
                        ui.icon("lock")
                        ui.label("Sessão protegida")
                    with ui.element("div").classes("portal-login-divider-dot"):
                        pass
                    with ui.element("div").classes("portal-login-trust-item"):
                        ui.icon("domain")
                        ui.label("Somente @hmv.org.br")

                ui.label(
                    "Não é necessário criar uma nova senha."
                ).classes("portal-login-footer")

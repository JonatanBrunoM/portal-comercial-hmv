from __future__ import annotations

from nicegui import ui

from nicegui_app.auth.google_oauth import google_oauth_is_configured
from nicegui_app.theme import apply_theme


OFFICIAL_HMV_LOGO = "https://www.hospitalmoinhos.org.br/assets/images/logo-w-hopkins.png"

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
            with ui.element("div").classes("portal-login-brand-content"):
                ui.image(OFFICIAL_HMV_LOGO).classes("portal-login-hmv-logo")

                ui.label("PORTAL COMERCIAL").classes("portal-login-product-kicker")
                ui.label(
                    "A informação certa, no momento em que a operação precisa."
                ).classes("portal-login-headline")
                ui.label(
                    "Um único ambiente para consultar operadoras, acessos, "
                    "documentos, contatos, regras e orientações comerciais."
                ).classes("portal-login-description")

                with ui.element("div").classes("portal-login-capabilities"):
                    for icon, title, detail in (
                        (
                            "search",
                            "Consulta centralizada",
                            "Encontre informações sem percorrer arquivos e planilhas.",
                        ),
                        (
                            "vpn_key",
                            "Acessos protegidos",
                            "Credenciais e orientações reunidas com segurança.",
                        ),
                        (
                            "campaign",
                            "Operação atualizada",
                            "Comunicados e contingências no mesmo fluxo de trabalho.",
                        ),
                    ):
                        with ui.element("div").classes("portal-login-capability"):
                            with ui.element("div").classes(
                                "portal-login-capability-icon"
                            ):
                                ui.icon(icon)
                            with ui.column().classes(
                                "portal-login-capability-copy"
                            ):
                                ui.label(title).classes(
                                    "portal-login-capability-title"
                                )
                                ui.label(detail).classes(
                                    "portal-login-capability-detail"
                                )

        with ui.element("section").classes("portal-login-access-panel"):
            with ui.element("div").classes("portal-login-access-wrap"):
                ui.label("PORTAL COMERCIAL").classes("portal-login-mobile-product")

                with ui.element("div").classes("portal-login-card"):
                    with ui.element("div").classes("portal-login-card-icon"):
                        ui.icon("verified_user")

                    ui.label("Acesso institucional").classes("portal-login-kicker")
                    ui.label("Entre para continuar").classes("portal-login-title")
                    ui.label(
                        "Use sua conta Google do Hospital Moinhos de Vento. "
                        "Não é necessário criar uma nova senha."
                    ).classes("portal-login-card-description")

                    if error in ERROR_MESSAGES:
                        with ui.row().classes("portal-login-alert"):
                            ui.icon("info_outline")
                            ui.label(ERROR_MESSAGES[error])

                    if not google_oauth_is_configured():
                        with ui.row().classes("portal-login-config-warning"):
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
                            with ui.column().classes("portal-google-login-copy"):
                                ui.label("Continuar com Google").classes(
                                    "portal-google-login-title"
                                )
                                ui.label("Conta corporativa @hmv.org.br").classes(
                                    "portal-google-login-subtitle"
                                )
                            ui.icon("arrow_forward").classes(
                                "portal-google-login-arrow"
                            )

                    with ui.element("div").classes("portal-login-trust"):
                        with ui.row().classes("portal-login-trust-item"):
                            ui.icon("lock")
                            ui.label("Sessão protegida")
                        with ui.row().classes("portal-login-trust-item"):
                            ui.icon("business")
                            ui.label("Acesso institucional")

                ui.label(
                    "Hospital Moinhos de Vento · Ambiente interno"
                ).classes("portal-login-footer")

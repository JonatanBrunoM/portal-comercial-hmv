from __future__ import annotations

from nicegui import ui

from nicegui_app.auth.google_oauth import google_oauth_is_configured
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
            with ui.element("div").classes("portal-login-brand-content"):
                with ui.row().classes("portal-login-brand"):
                    with ui.element("div").classes("portal-login-brand-mark"):
                        ui.icon("local_hospital")
                    with ui.column().classes("portal-login-brand-copy"):
                        ui.label("PORTAL COMERCIAL").classes(
                            "portal-login-brand-title"
                        )
                        ui.label("Hospital Moinhos de Vento").classes(
                            "portal-login-brand-subtitle"
                        )

                ui.label("Informação comercial, organizada para a operação.").classes(
                    "portal-login-headline"
                )
                ui.label(
                    "Consulte operadoras, planos, acessos, documentos, contatos "
                    "e orientações em um único ambiente institucional."
                ).classes("portal-login-description")

                with ui.element("div").classes("portal-login-network"):
                    with ui.element("div").classes("portal-login-network-center"):
                        ui.icon("hub")
                    for icon, label, css_class in (
                        ("domain", "Operadoras", "node-one"),
                        ("vpn_key", "Acessos", "node-two"),
                        ("description", "Documentos", "node-three"),
                        ("support_agent", "Contatos", "node-four"),
                    ):
                        with ui.element("div").classes(
                            f"portal-login-network-node {css_class}"
                        ):
                            ui.icon(icon)
                            ui.label(label)

        with ui.element("section").classes("portal-login-access-panel"):
            with ui.element("div").classes("portal-login-card"):
                ui.label("ACESSO INSTITUCIONAL").classes("portal-login-kicker")
                ui.label("Bem-vindo ao Portal Comercial").classes(
                    "portal-login-title"
                )
                ui.label(
                    "Entre com sua conta Google corporativa para continuar."
                ).classes("portal-login-card-description")

                if error in ERROR_MESSAGES:
                    with ui.row().classes("portal-login-alert"):
                        ui.icon("info_outline")
                        ui.label(ERROR_MESSAGES[error])

                if not google_oauth_is_configured():
                    with ui.row().classes("portal-login-config-warning"):
                        ui.icon("settings")
                        ui.label(
                            "As variáveis do Google OAuth ainda precisam ser "
                            "configuradas no Render."
                        )

                with ui.link(target="/auth/google/login").classes(
                    "portal-google-login-link"
                ):
                    with ui.element("div").classes("portal-google-login-button"):
                        with ui.element("div").classes("portal-google-symbol"):
                            ui.label("G")
                        ui.label("Continuar com Google")
                        ui.icon("arrow_forward")

                ui.label(
                    "Acesso permitido somente para contas @hmv.org.br."
                ).classes("portal-login-domain-note")

                with ui.element("div").classes("portal-login-divider"):
                    pass

                with ui.row().classes("portal-login-security"):
                    ui.icon("verified_user")
                    with ui.column().classes("portal-login-security-copy"):
                        ui.label("Ambiente institucional").classes(
                            "portal-login-security-title"
                        )
                        ui.label(
                            "Autenticação Google e sessão protegida no servidor."
                        ).classes("portal-login-security-text")

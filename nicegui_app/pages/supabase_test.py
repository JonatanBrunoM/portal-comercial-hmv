from __future__ import annotations

from nicegui import ui

from nicegui_app.data.supabase_client import (
    SupabaseConfigurationError,
    check_supabase_connection,
)
from nicegui_app.layout import portal_layout
from nicegui_app.services.operadoras_service import get_operadoras_preview


def _operator_card(operator: object) -> None:
    with ui.element("article").classes("portal-db-operator-card"):
        with ui.row().classes("portal-db-operator-head"):
            with ui.element("div").classes("portal-db-operator-icon"):
                ui.icon("domain")
            with ui.column().classes("portal-db-operator-copy"):
                ui.label(operator.short_name).classes("portal-db-operator-name")
                if operator.name != operator.short_name:
                    ui.label(operator.name).classes("portal-db-operator-full-name")

        with ui.row().classes("portal-db-operator-meta"):
            if operator.code:
                ui.label(operator.code).classes("portal-db-code")
            ui.label(operator.status).classes("portal-db-status")


def render_supabase_test() -> None:
    with portal_layout(
        active="operators",
        page_eyebrow="ETAPA 3A · INFRAESTRUTURA DE DADOS",
        page_title="NiceGUI conectado ao Supabase.",
        page_description=(
            "Esta tela existe apenas para validar a nova arquitetura. "
            "Os registros abaixo vêm da tabela operadoras da base atual."
        ),
    ):
        connected, message = check_supabase_connection()

        with ui.element("section").classes(
            "portal-db-status-panel is-connected" if connected
            else "portal-db-status-panel is-error"
        ):
            with ui.element("div").classes("portal-db-status-icon"):
                ui.icon("cloud_done" if connected else "cloud_off")
            with ui.column().classes("portal-db-status-copy"):
                ui.label(
                    "Conexão estabelecida" if connected else "Conexão pendente"
                ).classes("portal-db-status-title")
                ui.label(message).classes("portal-db-status-description")

        if not connected:
            with ui.element("section").classes("portal-db-help"):
                ui.label("O código está pronto.").classes("portal-db-help-title")
                ui.label(
                    "Cadastre as variáveis do Supabase no Render e faça um novo "
                    "deploy. Nenhuma chave deve ser adicionada ao GitHub."
                ).classes("portal-db-help-text")
            return

        try:
            operators = get_operadoras_preview()
        except SupabaseConfigurationError as error:
            ui.label(str(error)).classes("portal-db-error-text")
            return
        except Exception:
            ui.label(
                "A conexão respondeu, mas não foi possível carregar as operadoras."
            ).classes("portal-db-error-text")
            return

        with ui.row().classes("portal-db-section-heading"):
            with ui.column().classes("portal-db-section-copy"):
                ui.label("PROVA DE LEITURA").classes("portal-section-kicker")
                ui.label("Operadoras encontradas na base").classes(
                    "portal-section-title"
                )
            ui.label(f"{len(operators):02d} registro(s)").classes(
                "portal-db-count-badge"
            )

        if not operators:
            ui.label(
                "A tabela operadoras está acessível, mas não possui registros."
            ).classes("portal-db-empty")
            return

        with ui.element("div").classes("portal-db-operators-grid"):
            for operator in operators:
                _operator_card(operator)

        with ui.element("section").classes("portal-db-proof"):
            ui.icon("verified_user")
            ui.label(
                "A leitura é executada no backend Python. A chave privilegiada "
                "não é enviada ao navegador."
            )

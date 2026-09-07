from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.home_service import (
    HomeCommunication,
    HomeContingency,
    HomeData,
    HomeMetric,
    get_home_data,
)


SUPPORT_LINKS = (
    (
        "contacts",
        "Contatos",
        "Centrais, setores e canais de apoio.",
        "/contatos",
    ),
    (
        "support_agent",
        "Consultores",
        "Responsáveis e carteiras das operadoras.",
        "/consultores",
    ),
)


def _first_name(user: dict) -> str:
    name = str(user.get("name") or "").strip()
    return name.split()[0] if name else ""


def _module_card(item: HomeMetric) -> None:
    """Atalho principal da Home.

    O valor numérico do HomeMetric não é exibido de propósito: na Home,
    estes elementos são navegação e não indicadores de desempenho.
    """
    with ui.button(
        on_click=lambda route=item.route: ui.navigate.to(route),
    ).props("flat no-caps").classes("home-module-card"):
        with ui.element("div").classes("home-module-icon"):
            ui.icon(item.icon)

        with ui.column().classes("home-module-copy"):
            ui.label(item.label).classes("home-module-title")
            ui.label(item.detail).classes("home-module-detail")

        ui.icon("arrow_forward").classes("home-module-arrow")


def _support_link(
    icon: str,
    title: str,
    description: str,
    route: str,
) -> None:
    with ui.button(
        on_click=lambda target=route: ui.navigate.to(target),
    ).props("flat no-caps").classes("home-support-link"):
        with ui.element("div").classes("home-support-icon"):
            ui.icon(icon)
        with ui.column().classes("home-support-copy"):
            ui.label(title).classes("home-support-title")
            ui.label(description).classes("home-support-description")
        ui.icon("arrow_forward").classes("home-support-arrow")


def _communication_row(item: HomeCommunication) -> None:
    classes = "home-update-row"
    if item.featured:
        classes += " is-featured"

    with ui.button(
        on_click=lambda route=item.route: ui.navigate.to(route),
    ).props("flat no-caps").classes(classes):
        with ui.element("div").classes("home-update-rail"):
            ui.icon("campaign" if item.featured else "article")

        with ui.column().classes("home-update-main"):
            with ui.row().classes("home-update-meta"):
                ui.label(item.operator_name).classes("home-update-operator")
                if item.featured:
                    ui.label("DESTAQUE").classes("home-update-badge")
                elif item.category:
                    ui.label(item.category).classes("home-update-badge is-soft")

            ui.label(item.title).classes("home-update-title")

            if item.summary:
                ui.label(item.summary).classes("home-update-description")

        with ui.column().classes("home-update-side"):
            ui.label(item.priority).classes("home-update-priority")
            ui.icon("arrow_forward").classes("home-update-arrow")


def _contingency_row(item: HomeContingency) -> None:
    with ui.button(
        on_click=lambda route=item.route: ui.navigate.to(route),
    ).props("flat no-caps").classes("home-alert-row"):
        with ui.element("div").classes("home-alert-indicator"):
            ui.icon("warning_amber")

        with ui.column().classes("home-alert-copy"):
            with ui.row().classes("home-alert-meta"):
                ui.label(item.operator_name).classes("home-alert-operator")
                ui.label(item.status).classes("home-alert-status")
                if item.priority:
                    ui.label(item.priority).classes("home-alert-priority")

            ui.label(item.title).classes("home-alert-title")

            detail = item.alternative_guidance or item.description
            if detail:
                ui.label(detail).classes("home-alert-description")

        ui.icon("arrow_forward").classes("home-alert-arrow")


def _empty_state(
    *,
    icon: str,
    title: str,
    description: str,
    route: str,
    action: str,
) -> None:
    with ui.element("div").classes("home-empty-state"):
        with ui.element("div").classes("home-empty-icon"):
            ui.icon(icon)
        with ui.column().classes("home-empty-copy"):
            ui.label(title).classes("home-empty-title")
            ui.label(description).classes("home-empty-description")
        ui.button(
            action,
            icon="arrow_forward",
            on_click=lambda: ui.navigate.to(route),
        ).props("flat no-caps").classes("home-empty-action")


def _render_home_data(data: HomeData) -> None:
    # Navegação principal: mantém os quatro módulos, mas sem números.
    with ui.element("section").classes("home-module-section"):
        with ui.row().classes("home-module-heading"):
            with ui.column().classes("home-module-heading-copy"):
                ui.label("ACESSO RÁPIDO").classes("home-section-kicker")
                ui.label("Ir direto para").classes("home-module-heading-title")
            ui.label(
                "Atalhos para as consultas mais frequentes."
            ).classes("home-module-heading-note")

        with ui.element("nav").classes("home-module-grid"):
            for metric in data.metrics:
                _module_card(metric)

    # Atualizações e contingências formam uma única área de consciência
    # operacional: o usuário entende rapidamente o que mudou e o que afeta
    # o fluxo agora.
    with ui.element("section").classes("home-operation-section"):
        with ui.row().classes("home-operation-heading"):
            with ui.column().classes("home-operation-heading-copy"):
                ui.label("AGORA NO PORTAL").classes("home-section-kicker")
                ui.label("Informação que pode mudar sua rotina").classes("home-operation-title")
            ui.label(
                "Comunicados e contingências vigentes, priorizados para consulta rápida."
            ).classes("home-operation-note")

        with ui.element("div").classes("home-workspace-grid"):
            with ui.element("article").classes("home-panel home-updates-panel"):
                with ui.row().classes("home-panel-heading"):
                    with ui.column().classes("home-panel-heading-copy"):
                        ui.label("ATUALIZAÇÕES").classes("home-section-kicker")
                        ui.label("O que merece sua atenção").classes("home-section-title")
                    ui.button(
                        "Ver todos",
                        icon="arrow_forward",
                        on_click=lambda: ui.navigate.to("/comunicados"),
                    ).props("flat no-caps").classes("home-text-action")

                if data.communications:
                    with ui.column().classes("home-updates-list"):
                        for item in data.communications:
                            _communication_row(item)
                else:
                    _empty_state(
                        icon="mark_email_read",
                        title="Nenhum comunicado vigente.",
                        description=(
                            "Quando houver uma comunicação publicada para o período, "
                            "ela aparecerá aqui."
                        ),
                        route="/comunicados",
                        action="Ver comunicados",
                    )

            with ui.element("article").classes("home-panel home-alerts-panel"):
                with ui.row().classes("home-panel-heading"):
                    with ui.column().classes("home-panel-heading-copy"):
                        ui.label("OPERAÇÃO AGORA").classes("home-section-kicker")
                        ui.label("Contingências vigentes").classes("home-section-title")
                    ui.button(
                        "Ver todas",
                        icon="arrow_forward",
                        on_click=lambda: ui.navigate.to("/contingencias"),
                    ).props("flat no-caps").classes("home-text-action")

                if data.contingencies:
                    with ui.column().classes("home-alerts-list"):
                        for item in data.contingencies:
                            _contingency_row(item)
                else:
                    _empty_state(
                        icon="verified",
                        title="Nenhuma contingência vigente.",
                        description=(
                            "A operação não possui alertas ativos para o período neste momento."
                        ),
                        route="/contingencias",
                        action="Consultar histórico",
                    )

    # Contatos e consultores continuam acessíveis sem repetir outra grade
    # inteira de cards já representados na navegação principal/sidebar.
    with ui.element("section").classes("home-support-section"):
        with ui.column().classes("home-support-intro"):
            ui.label("PRECISA DE APOIO?").classes("home-section-kicker")
            ui.label("Encontre quem pode ajudar").classes("home-support-heading")

        with ui.element("div").classes("home-support-links"):
            for item in SUPPORT_LINKS:
                _support_link(*item)


def render_home(user: dict) -> None:
    first_name = _first_name(user)

    try:
        data = get_home_data()
    except Exception:
        data = HomeData(metrics=(), communications=(), contingencies=())

    with portal_layout(
        user=user,
        active="home",
    ):
        with ui.element("section").classes("home-hero"):
            with ui.element("div").classes("home-hero-glow home-hero-glow-one"):
                pass
            with ui.element("div").classes("home-hero-glow home-hero-glow-two"):
                pass

            with ui.element("div").classes("home-hero-content"):
                ui.label("PORTAL COMERCIAL").classes("home-hero-kicker")

                greeting = f"Olá, {first_name}." if first_name else "Olá."
                ui.label(greeting).classes("home-hero-greeting")

                ui.label(
                    "O que você precisa consultar agora?"
                ).classes("home-hero-title")

                ui.label(
                    "Pesquise ou acesse diretamente operadoras, portais, documentos, "
                    "contatos e orientações da operação."
                ).classes("home-hero-description")

                def submit_home_search() -> None:
                    query = str(home_search.value or "").strip()
                    if len(query) < 2:
                        ui.notify(
                            "Digite pelo menos 2 caracteres para pesquisar.",
                            type="info",
                            position="top",
                        )
                        home_search.run_method("focus")
                        return

                    ui.context.client.storage["portal_pending_search_query"] = query
                    ui.navigate.to("/pesquisa")

                with ui.element("div").classes("home-search-command"):
                    with ui.element("div").classes("home-search-icon"):
                        ui.icon("search")

                    home_search = ui.input(
                        placeholder=(
                            "Ex.: senha Unimed, autorização Bradesco, contato CASSI..."
                        )
                    ).props(
                        "borderless dense autocomplete='off'"
                    ).classes("home-search-input")
                    home_search.on("keydown.enter", submit_home_search)

                    ui.button(
                        "Pesquisar",
                        icon="arrow_forward",
                        on_click=submit_home_search,
                    ).props("unelevated no-caps").classes("home-search-submit")

            # Elemento gráfico discreto: reforça a ideia de central de consulta
            # sem disputar atenção com a pesquisa.
            with ui.element("div").classes("home-hero-mark"):
                with ui.element("div").classes("home-hero-mark-ring ring-one"):
                    pass
                with ui.element("div").classes("home-hero-mark-ring ring-two"):
                    pass
                with ui.element("div").classes("home-hero-mark-core"):
                    ui.icon("hub")
                ui.label("CENTRAL DE CONSULTA").classes("home-mark-caption")

        if data.metrics:
            _render_home_data(data)

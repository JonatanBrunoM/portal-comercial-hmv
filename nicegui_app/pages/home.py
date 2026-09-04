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


QUICK_ACCESS = (
    (
        "domain",
        "Operadoras",
        "Planos, regras, coberturas e orientações.",
        "/operadoras",
    ),
    (
        "vpn_key",
        "Portais e acessos",
        "Credenciais e instruções para os portais externos.",
        "/portais",
    ),
    (
        "description",
        "Documentos",
        "Manuais, formulários e referências institucionais.",
        "/documentos",
    ),
    (
        "contacts",
        "Contatos",
        "Canais de apoio para cada necessidade.",
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


def _metric_card(item: HomeMetric) -> None:
    with ui.button(
        on_click=lambda route=item.route: ui.navigate.to(route),
    ).props("flat no-caps").classes("home-metric-card"):
        with ui.element("div").classes("home-metric-icon"):
            ui.icon(item.icon)
        with ui.element("div").classes("home-metric-copy"):
            ui.label(str(item.value)).classes("home-metric-value")
            ui.label(item.label).classes("home-metric-label")
            ui.label(item.detail).classes("home-metric-detail")
        ui.icon("north_east").classes("home-metric-arrow")


def _quick_card(
    icon: str,
    title: str,
    description: str,
    route: str,
) -> None:
    with ui.button(
        on_click=lambda: ui.navigate.to(route),
    ).props("flat no-caps").classes("home-quick-card"):
        with ui.element("div").classes("home-quick-icon"):
            ui.icon(icon)
        with ui.column().classes("home-quick-copy"):
            ui.label(title).classes("home-quick-title")
            ui.label(description).classes("home-quick-description")
        ui.icon("arrow_forward").classes("home-quick-arrow")


def _communication_card(item: HomeCommunication) -> None:
    classes = "home-update-card"
    if item.featured:
        classes += " is-featured"

    with ui.button(
        on_click=lambda: ui.navigate.to(item.route),
    ).props("flat no-caps").classes(classes):
        with ui.row().classes("home-update-meta"):
            ui.label(item.operator_name).classes("home-update-operator")
            if item.featured:
                ui.label("DESTAQUE").classes("home-update-badge")
            elif item.category:
                ui.label(item.category).classes("home-update-badge is-soft")

        ui.label(item.title).classes("home-update-title")
        if item.summary:
            ui.label(item.summary).classes("home-update-description")

        with ui.row().classes("home-update-footer"):
            ui.label(item.priority).classes("home-update-priority")
            with ui.row().classes("home-update-link"):
                ui.label("Ler comunicado")
                ui.icon("arrow_forward")


def _contingency_card(item: HomeContingency) -> None:
    with ui.button(
        on_click=lambda: ui.navigate.to(item.route),
    ).props("flat no-caps").classes("home-alert-card"):
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
    with ui.element("section").classes("home-metrics-grid"):
        for metric in data.metrics:
            _metric_card(metric)

    with ui.element("section").classes("home-workspace-grid"):
        with ui.element("article").classes("home-panel home-updates-panel"):
            with ui.row().classes("home-panel-heading"):
                with ui.column().classes("home-panel-heading-copy"):
                    ui.label("ATUALIZAÇÕES").classes("home-section-kicker")
                    ui.label("O que merece sua atenção").classes("home-section-title")
                ui.button(
                    "Todos",
                    icon="arrow_forward",
                    on_click=lambda: ui.navigate.to("/comunicados"),
                ).props("flat no-caps").classes("home-text-action")

            if data.communications:
                with ui.column().classes("home-updates-list"):
                    for item in data.communications:
                        _communication_card(item)
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
                    "Todas",
                    icon="arrow_forward",
                    on_click=lambda: ui.navigate.to("/contingencias"),
                ).props("flat no-caps").classes("home-text-action")

            if data.contingencies:
                with ui.column().classes("home-alerts-list"):
                    for item in data.contingencies:
                        _contingency_card(item)
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
                    "Encontre a informação que a operação precisa, sem perder tempo."
                ).classes("home-hero-title")
                ui.label(
                    "Operadoras, portais, documentos, contatos e orientações "
                    "reunidos em um único ponto de consulta."
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

                    # A consulta é transferida para a página de Pesquisa.
                    # O resultado não é renderizado na Home.
                    ui.context.client.storage["portal_home_search_query"] = query
                    ui.navigate.to("/pesquisa")

                with ui.element("div").classes("home-search-command"):
                    with ui.element("div").classes("home-search-icon"):
                        ui.icon("search")

                    home_search = ui.input(
                        placeholder=(
                            "Operadora, autorização, elegibilidade, portal, contato..."
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

            with ui.element("div").classes("home-hero-mark"):
                with ui.element("div").classes("home-hero-mark-ring ring-one"):
                    pass
                with ui.element("div").classes("home-hero-mark-ring ring-two"):
                    pass
                with ui.element("div").classes("home-hero-mark-core"):
                    ui.icon("hub")
                ui.label("CONSULTAR").classes("home-mark-label mark-a")
                ui.label("ORIENTAR").classes("home-mark-label mark-b")
                ui.label("DECIDIR").classes("home-mark-label mark-c")

        if data.metrics:
            _render_home_data(data)

        with ui.element("section").classes("home-quick-section"):
            with ui.row().classes("home-section-heading"):
                with ui.column().classes("home-section-heading-copy"):
                    ui.label("ATALHOS").classes("home-section-kicker")
                    ui.label("Acesso direto ao que você mais usa").classes(
                        "home-section-title"
                    )
                ui.label(
                    "Entre no módulo certo sem percorrer menus intermediários."
                ).classes("home-section-note")

            with ui.element("div").classes("home-quick-grid"):
                for item in QUICK_ACCESS:
                    _quick_card(*item)

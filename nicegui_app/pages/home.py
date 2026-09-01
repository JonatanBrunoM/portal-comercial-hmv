from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout


def _metric(icon: str, label: str, value: str, detail: str) -> None:
    with ui.element("article").classes("portal-metric-card"):
        with ui.row().classes("portal-metric-head"):
            with ui.element("div").classes("portal-metric-icon"):
                ui.icon(icon)
            ui.label(label).classes("portal-metric-label")

        ui.label(value).classes("portal-metric-value")
        ui.label(detail).classes("portal-metric-detail")


def _feature_card(
    icon: str,
    title: str,
    description: str,
    *,
    featured: bool = False,
) -> None:
    classes = "portal-feature-card"
    if featured:
        classes += " is-featured"

    with ui.element("article").classes(classes):
        with ui.element("div").classes("portal-feature-icon"):
            ui.icon(icon)
        ui.label(title).classes("portal-feature-title")
        ui.label(description).classes("portal-feature-description")

        with ui.button(
            "Explorar",
            icon="arrow_forward",
            on_click=lambda: ui.notify(
                f"{title}: será conectado nas próximas etapas.",
                type="info",
                position="top",
            ),
        ).props("flat no-caps").classes("portal-feature-action"):
            pass


def render_home() -> None:
    with portal_layout(
        active="home",
        page_eyebrow="CENTRAL DE INFORMAÇÃO COMERCIAL",
        page_title="Um único ponto de partida.",
        page_description=(
            "A nova estrutura do Portal Comercial começa aqui: "
            "mais clara, consistente e preparada para crescer."
        ),
    ):
        with ui.element("section").classes("portal-hero-panel"):
            with ui.element("div").classes("portal-hero-copy"):
                with ui.row().classes("portal-status-badge"):
                    ui.element("span").classes("portal-status-dot")
                    ui.label("Nova geração em desenvolvimento")

                ui.label(
                    "Informação certa, no momento em que a operação precisa."
                ).classes("portal-hero-title")

                ui.label(
                    "Esta etapa valida o Design System, o layout responsivo "
                    "e os componentes que serão reutilizados em todo o portal."
                ).classes("portal-hero-description")

                with ui.row().classes("portal-hero-actions"):
                    with ui.button(
                        "Pesquisar no portal",
                        icon="search",
                        on_click=lambda: ui.notify(
                            "A pesquisa será conectada em uma próxima etapa.",
                            type="info",
                            position="top",
                        ),
                    ).props("unelevated no-caps").classes("portal-button-primary"):
                        pass

                    with ui.button(
                        "Ver operadoras",
                        icon="domain",
                        on_click=lambda: ui.notify(
                            "A central de operadoras será conectada em breve.",
                            type="info",
                            position="top",
                        ),
                    ).props("flat no-caps").classes("portal-button-secondary"):
                        pass

            with ui.element("div").classes("portal-hero-visual"):
                with ui.element("div").classes("portal-orbit portal-orbit-one"):
                    pass
                with ui.element("div").classes("portal-orbit portal-orbit-two"):
                    pass
                with ui.element("div").classes("portal-hero-symbol"):
                    ui.icon("hub")
                ui.label("INFORMAÇÃO").classes("portal-orbit-label label-one")
                ui.label("ACESSO").classes("portal-orbit-label label-two")
                ui.label("DECISÃO").classes("portal-orbit-label label-three")

        with ui.element("section").classes("portal-metrics-grid"):
            _metric("domain", "Operadoras", "03", "Base de desenvolvimento")
            _metric("vpn_key", "Portais", "—", "Integração na próxima fase")
            _metric("description", "Documentos", "—", "Estrutura preparada")
            _metric("verified_user", "Ambiente", "POC", "NiceGUI + Render")

        with ui.element("section").classes("portal-section"):
            with ui.row().classes("portal-section-heading"):
                with ui.column().classes("portal-section-heading-copy"):
                    ui.label("ACESSOS PRINCIPAIS").classes("portal-section-kicker")
                    ui.label("Tudo começa por uma necessidade.").classes(
                        "portal-section-title"
                    )
                ui.label(
                    "A fundação visual já está pronta para receber os "
                    "módulos reais do portal."
                ).classes("portal-section-note")

            with ui.element("div").classes("portal-feature-grid"):
                _feature_card(
                    "domain",
                    "Operadoras",
                    "Planos, regras, contatos, portais e orientações reunidos "
                    "em uma única central.",
                    featured=True,
                )
                _feature_card(
                    "vpn_key",
                    "Portais e acessos",
                    "Acesso rápido às plataformas externas utilizadas pela operação.",
                )
                _feature_card(
                    "description",
                    "Documentos",
                    "Materiais institucionais, manuais e referências para consulta.",
                )
                _feature_card(
                    "support_agent",
                    "Contatos e consultores",
                    "Encontre rapidamente quem pode apoiar cada necessidade.",
                )

        with ui.element("section").classes("portal-foundation-strip"):
            with ui.element("div").classes("portal-foundation-icon"):
                ui.icon("architecture")
            with ui.column().classes("portal-foundation-copy"):
                ui.label("FUNDAÇÃO NICEGUI").classes("portal-foundation-kicker")
                ui.label(
                    "Design System e layout compartilhado ativos."
                ).classes("portal-foundation-title")
                ui.label(
                    "Cores, tipografia, espaçamento, componentes e responsividade "
                    "agora pertencem ao portal — não ao framework."
                ).classes("portal-foundation-description")
            with ui.row().classes("portal-foundation-tags"):
                for tag in ("Desktop", "Tablet", "Mobile", "Componentes"):
                    ui.label(tag).classes("portal-tag")

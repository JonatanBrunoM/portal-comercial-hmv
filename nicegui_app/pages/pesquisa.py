from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.pesquisa_service import (
    SearchResult,
    get_search_catalog,
    search_catalog,
)


def _result_card(item: SearchResult) -> None:
    with ui.element("article").classes("portal-search-result"):
        with ui.element("div").classes("portal-search-result-icon"):
            ui.icon(item.icon)

        with ui.column().classes("portal-search-result-copy"):
            ui.label(item.eyebrow).classes("portal-search-result-eyebrow")
            ui.label(item.title).classes("portal-search-result-title")

            if item.subtitle:
                ui.label(item.subtitle).classes("portal-search-result-subtitle")

            if item.description:
                ui.label(item.description).classes("portal-search-result-description")

        ui.button(
            icon="arrow_forward",
            on_click=lambda route=item.route: ui.navigate.to(route),
        ).props("flat round").classes("portal-search-result-action")


def render_pesquisa(user: dict) -> None:
    catalog = get_search_catalog()
    kinds = ["Tudo"] + sorted({item.kind for item in catalog})

    with portal_layout(
        user=user,
        active="search",
        page_eyebrow="PESQUISA GLOBAL",
        page_title="Pergunte ao Portal Comercial.",
        page_description=(
            "Encontre rapidamente operadoras, planos, portais, documentos, "
            "contatos, consultores, elegibilidade, autorizações, coberturas, dicas, comunicados e contingências."
        ),
    ):
        with ui.element("section").classes("portal-search-hero"):
            with ui.element("div").classes("portal-search-orb"):
                ui.icon("travel_explore")

            ui.label("O que você precisa encontrar?").classes("portal-search-question")
            ui.label(
                "Digite uma operadora, um plano, uma orientação ou qualquer termo relacionado ao atendimento."
            ).classes("portal-search-helper")

            with ui.element("div").classes("portal-search-box"):
                search = ui.input(
                    placeholder="Ex.: Unimed autorização, portal elegibilidade, contato..."
                ).props(
                    "borderless clearable autofocus"
                ).classes("portal-search-input")
                ui.icon("search").classes("portal-search-box-icon")

            with ui.row().classes("portal-search-suggestions"):
                ui.label("Experimente:").classes("portal-search-suggestions-label")
                for suggestion in ("Unimed", "Autorização", "Elegibilidade", "Portal", "Contato"):
                    ui.button(
                        suggestion,
                        on_click=lambda value=suggestion: (search.set_value(value), search.run_method("focus")),
                    ).props("outline rounded no-caps").classes("portal-search-suggestion")

        with ui.row().classes("portal-search-controls"):
            category = ui.select(
                kinds,
                value="Tudo",
                label="Pesquisar em",
            ).props("outlined dense").classes("portal-search-category")

            result_count = ui.label(
                "Digite pelo menos 2 caracteres para pesquisar."
            ).classes("portal-search-count")

        results_container = ui.element("div").classes("portal-search-results")

        with ui.element("section").classes("portal-search-start") as start_state:
            ui.icon("hub")
            ui.label("Uma busca, todo o portal.").classes("portal-search-start-title")
            ui.label(
                f"O catálogo atual reúne {len(catalog)} registros pesquisáveis em "
                f"{len(kinds) - 1} áreas do Portal Comercial."
            ).classes("portal-search-start-description")

        def refresh() -> None:
            query = search.value or ""
            results_container.clear()

            if len(query.strip()) < 2:
                start_state.set_visibility(True)
                result_count.set_text("Digite pelo menos 2 caracteres para pesquisar.")
                return

            start_state.set_visibility(False)
            matches = search_catalog(catalog, query, category.value or "Tudo")
            result_count.set_text(f"{len(matches)} resultado(s) encontrado(s)")

            with results_container:
                if not matches:
                    with ui.element("section").classes("portal-search-empty"):
                        ui.icon("search_off")
                        ui.label("Nenhum resultado encontrado.").classes(
                            "portal-search-empty-title"
                        )
                        ui.label(
                            "Tente usar menos palavras ou um termo mais amplo."
                        ).classes("portal-search-empty-description")
                    return

                for item in matches[:60]:
                    _result_card(item)

        search.on_value_change(lambda _: refresh())
        category.on_value_change(lambda _: refresh())

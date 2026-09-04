from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.pesquisa_service import (
    RankedSearchResult,
    SearchResult,
    get_search_catalog,
    search_catalog_smart,
)


def _result_card(match: RankedSearchResult, *, featured: bool = False) -> None:
    item = match.item
    classes = "portal-search-result"
    if featured:
        classes += " is-featured"

    with ui.element("article").classes(classes):
        with ui.element("div").classes("portal-search-result-icon"):
            ui.icon(item.icon)

        with ui.column().classes("portal-search-result-copy"):
            with ui.row().classes("portal-search-result-meta"):
                ui.label(item.eyebrow).classes("portal-search-result-eyebrow")
                if featured:
                    ui.label("MELHOR RESULTADO").classes(
                        "portal-search-result-best"
                    )

            ui.label(item.title).classes("portal-search-result-title")

            if item.subtitle:
                ui.label(item.subtitle).classes("portal-search-result-subtitle")

            if item.description:
                ui.label(item.description).classes(
                    "portal-search-result-description"
                )

            ui.label(match.reason).classes("portal-search-result-reason")

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
        page_eyebrow="PESQUISA INTELIGENTE",
        page_title="Pergunte ao Portal Comercial.",
        page_description=(
            "Pesquise do seu jeito. O Portal interpreta termos, contexto e "
            "erros simples de digitação para priorizar a informação mais útil."
        ),
    ):
        with ui.element("section").classes("portal-search-hero"):
            with ui.element("div").classes("portal-search-orb"):
                ui.icon("travel_explore")

            ui.label("O que você precisa saber?").classes("portal-search-question")
            ui.label(
                'Experimente frases como “senha do portal Unimed”, '
                '“telefone da Cassi” ou “como autorizar Bradesco”.'
            ).classes("portal-search-helper")

            with ui.element("div").classes("portal-search-box"):
                initial_query = str(
                    ui.context.client.storage.pop(
                        "portal_pending_search_query",
                        "",
                    ) or ""
                ).strip()

                search = ui.input(
                    placeholder=(
                        "Ex.: senha do portal Unimed, telefone Cassi, "
                        "autorização Bradesco..."
                    ),
                    value=initial_query,
                ).props(
                    "borderless clearable autofocus autocomplete='off'"
                ).classes("portal-search-input")
                ui.icon("search").classes("portal-search-box-icon")

            with ui.row().classes("portal-search-suggestions"):
                ui.label("Experimente:").classes(
                    "portal-search-suggestions-label"
                )
                for suggestion in (
                    "senha do portal",
                    "como autorizar",
                    "telefone da operadora",
                    "elegibilidade",
                    "documentos",
                ):
                    ui.button(
                        suggestion,
                        on_click=lambda value=suggestion: (
                            search.set_value(value),
                            search.run_method("focus"),
                        ),
                    ).props("outline rounded no-caps").classes(
                        "portal-search-suggestion"
                    )

        with ui.row().classes("portal-search-controls"):
            category = ui.select(
                kinds,
                value="Tudo",
                label="Pesquisar em",
            ).props("outlined dense").classes("portal-search-category")

            result_count = ui.label(
                "Digite pelo menos 2 caracteres para pesquisar."
            ).classes("portal-search-count")

        interpretation = ui.element("div").classes(
            "portal-search-interpretation"
        )
        interpretation.set_visibility(False)

        results_container = ui.element("div").classes("portal-search-results")

        with ui.element("section").classes("portal-search-start") as start_state:
            ui.icon("hub")
            ui.label("Uma busca, todo o portal.").classes(
                "portal-search-start-title"
            )
            ui.label(
                f"O catálogo atual reúne {len(catalog)} registros pesquisáveis "
                f"em {len(kinds) - 1} áreas. Você não precisa saber em qual "
                "módulo a informação está."
            ).classes("portal-search-start-description")

        def refresh() -> None:
            query = str(search.value or "")
            results_container.clear()
            interpretation.clear()

            if len(query.strip()) < 2:
                interpretation.set_visibility(False)
                start_state.set_visibility(True)
                result_count.set_text(
                    "Digite pelo menos 2 caracteres para pesquisar."
                )
                return

            start_state.set_visibility(False)
            response = search_catalog_smart(
                catalog,
                query,
                category.value or "Tudo",
            )

            if response.interpreted_as or response.relaxed:
                interpretation.set_visibility(True)
                with interpretation:
                    ui.label("Entendi sua busca como:").classes(
                        "portal-search-interpretation-label"
                    )

                    for label in response.interpreted_as:
                        ui.label(label).classes(
                            "portal-search-interpretation-chip"
                        )

                    if response.relaxed:
                        ui.label(
                            "busca aproximada"
                        ).classes(
                            "portal-search-interpretation-chip is-relaxed"
                        )
            else:
                interpretation.set_visibility(False)

            matches = response.results
            count = len(matches)
            result_count.set_text(
                f"{count} resultado{'s' if count != 1 else ''} priorizado"
                f"{'s' if count != 1 else ''}"
            )

            with results_container:
                if not matches:
                    with ui.element("section").classes("portal-search-empty"):
                        ui.icon("search_off")
                        ui.label(
                            "Não encontrei uma correspondência segura."
                        ).classes("portal-search-empty-title")
                        ui.label(
                            "Tente informar a operadora junto com o que precisa, "
                            "por exemplo: “Unimed contato” ou “Bradesco autorização”."
                        ).classes("portal-search-empty-description")
                    return

                _result_card(matches[0], featured=True)

                if len(matches) > 1:
                    with ui.row().classes("portal-search-more-heading"):
                        ui.label("Outros resultados relevantes").classes(
                            "portal-search-more-title"
                        )
                        ui.label(
                            f"{len(matches) - 1} correspondência(s)"
                        ).classes("portal-search-more-count")

                    for match in matches[1:]:
                        _result_card(match)

        search.on_value_change(lambda _: refresh())
        category.on_value_change(lambda _: refresh())

        if initial_query:
            refresh()

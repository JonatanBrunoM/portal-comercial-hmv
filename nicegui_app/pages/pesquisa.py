from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.pesquisa_service import (
    ConversationalAnswer,
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



def _answer_card(answer: ConversationalAnswer) -> None:
    confidence_label = {
        "alta": "Correspondência alta",
        "média": "Correspondência moderada",
        "baixa": "Correspondência ampla",
    }.get(answer.confidence, "Correspondência")

    with ui.element("section").classes(
        f"portal-conversation-answer confidence-{answer.confidence}"
    ):
        with ui.row().classes("portal-conversation-answer-top"):
            with ui.element("div").classes("portal-conversation-avatar"):
                ui.icon("auto_awesome")

            with ui.column().classes("portal-conversation-heading"):
                ui.label("RESPOSTA DO PORTAL").classes(
                    "portal-conversation-kicker"
                )
                ui.label(answer.title).classes("portal-conversation-title")

            ui.label(confidence_label).classes(
                "portal-conversation-confidence"
            )

        ui.label(answer.lead).classes("portal-conversation-lead")

        if answer.bullets:
            with ui.column().classes("portal-conversation-points"):
                for bullet in answer.bullets:
                    with ui.row().classes("portal-conversation-point"):
                        ui.icon("check_circle")
                        ui.label(bullet)

        with ui.row().classes("portal-conversation-footer"):
            with ui.row().classes("portal-conversation-note"):
                ui.icon("verified")
                ui.label(answer.note)

            ui.button(
                answer.source_label,
                icon="arrow_forward",
                on_click=lambda: ui.navigate.to(answer.source_route),
            ).props("unelevated no-caps").classes(
                "portal-conversation-source"
            )



def render_pesquisa(user: dict) -> None:
    catalog = get_search_catalog()
    kinds = ["Tudo"] + sorted({item.kind for item in catalog})

    with portal_layout(
        user=user,
        active="search",
    ):
        with ui.element("section").classes("portal-search-workspace"):
            with ui.element("div").classes("portal-search-intro"):
                with ui.row().classes("portal-search-intro-top"):
                    with ui.element("div").classes("portal-search-intro-icon"):
                        ui.icon("travel_explore")

                    with ui.column().classes("portal-search-intro-copy"):
                        ui.label("PESQUISA INTELIGENTE").classes(
                            "portal-search-kicker"
                        )
                        ui.label(
                            "O que você precisa encontrar?"
                        ).classes("portal-search-question")
                        ui.label(
                            "Pergunte do seu jeito. O Portal interpreta o contexto "
                            "e procura a informação mais provável entre os registros "
                            "oficiais cadastrados."
                        ).classes("portal-search-helper")

            with ui.element("div").classes("portal-search-box"):
                initial_query = str(
                    ui.context.client.storage.pop(
                        "portal_pending_search_query",
                        "",
                    ) or ""
                ).strip()

                ui.icon("search").classes("portal-search-box-leading")
                search = ui.input(
                    placeholder=(
                        "Ex.: como faço autorização na Unimed?"
                    ),
                    value=initial_query,
                ).props(
                    "borderless clearable autofocus autocomplete='off'"
                ).classes("portal-search-input")

                search_button = ui.button(
                    "Pesquisar",
                    icon="arrow_forward",
                ).props("unelevated no-caps").classes(
                    "portal-search-submit"
                )

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
                    ).props("flat rounded no-caps").classes(
                        "portal-search-suggestion"
                    )

        category_state = {"value": "Tudo"}

        with ui.row().classes("portal-search-controls"):
            with ui.element("div").classes("portal-search-filter-wrap"):
                ui.label("Pesquisar em").classes("portal-search-filter-label")

                with ui.button().props(
                    "flat no-caps"
                ).classes("portal-search-filter-button") as filter_button:
                    ui.icon("tune").classes("portal-search-filter-icon")
                    filter_value = ui.label("Tudo").classes(
                        "portal-search-filter-value"
                    )
                    ui.icon("expand_more").classes(
                        "portal-search-filter-chevron"
                    )

                    with ui.menu().classes("portal-search-filter-menu") as filter_menu:
                        ui.label("FILTRAR RESULTADOS").classes(
                            "portal-search-filter-menu-title"
                        )

                        for kind_name in kinds:
                            def select_kind(
                                value: str = kind_name,
                            ) -> None:
                                category_state["value"] = value
                                filter_value.set_text(value)
                                filter_menu.close()
                                refresh()

                            with ui.button(
                                on_click=select_kind,
                            ).props("flat no-caps").classes(
                                "portal-search-filter-option"
                            ):
                                ui.icon(
                                    "check" if kind_name == "Tudo" else "radio_button_unchecked"
                                ).classes("portal-search-filter-option-icon")
                                ui.label(kind_name).classes(
                                    "portal-search-filter-option-label"
                                )

            result_count = ui.label(
                "Digite pelo menos 2 caracteres para pesquisar."
            ).classes("portal-search-count")

        interpretation = ui.element("div").classes(
            "portal-search-interpretation"
        )
        interpretation.set_visibility(False)

        answer_container = ui.element("div").classes(
            "portal-conversation-container"
        )
        answer_container.set_visibility(False)

        results_container = ui.element("div").classes("portal-search-results")

        with ui.element("section").classes("portal-search-start") as start_state:
            with ui.row().classes("portal-search-start-inner"):
                ui.icon("verified_user")
                ui.label(
                    f"{len(catalog)} informações pesquisáveis em "
                    f"{len(kinds) - 1} áreas do Portal."
                ).classes("portal-search-start-description")
                ui.element("span").classes("portal-search-start-dot")
                ui.label(
                    "A resposta usa somente conteúdo cadastrado."
                ).classes("portal-search-start-description")

        def refresh() -> None:
            query = str(search.value or "")
            results_container.clear()
            interpretation.clear()
            answer_container.clear()

            if len(query.strip()) < 2:
                interpretation.set_visibility(False)
                answer_container.set_visibility(False)
                start_state.set_visibility(True)
                result_count.set_text(
                    "Digite pelo menos 2 caracteres para pesquisar."
                )
                return

            start_state.set_visibility(False)
            response = search_catalog_smart(
                catalog,
                query,
                category_state["value"],
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

                    if response.corrections:
                        correction_text = " · ".join(
                            f"{source} → {target}"
                            for source, target in response.corrections[:3]
                        )
                        ui.label(
                            f"corrigido: {correction_text}"
                        ).classes(
                            "portal-search-interpretation-chip is-correction"
                        )
                    elif response.relaxed:
                        ui.label(
                            "busca aproximada"
                        ).classes(
                            "portal-search-interpretation-chip is-relaxed"
                        )
            else:
                interpretation.set_visibility(False)

            if response.answer is not None:
                answer_container.set_visibility(True)
                with answer_container:
                    _answer_card(response.answer)
            else:
                answer_container.set_visibility(False)

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

                _result_card(matches[0], featured=False)

                with ui.row().classes("portal-search-more-heading"):
                    ui.label("Fontes e resultados relacionados").classes(
                        "portal-search-more-title"
                    )
                    ui.label(
                        f"{len(matches)} correspondência(s)"
                    ).classes("portal-search-more-count")

                for match in matches:
                    _result_card(match)

        search_button.on_click(refresh)
        search.on("keydown.enter", refresh)
        search.on_value_change(lambda _: refresh())

        if initial_query:
            refresh()

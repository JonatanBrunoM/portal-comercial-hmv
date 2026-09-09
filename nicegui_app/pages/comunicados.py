from __future__ import annotations

from datetime import date

from nicegui import ui

from nicegui_app.hero_art import render_hero_art
from nicegui_app.layout import portal_layout
from nicegui_app.services.comunicados_service import (
    ComunicadoPreview,
    get_comunicado_detail,
    get_comunicados_preview,
)


def _norm(value: str) -> str:
    return " ".join((value or "").lower().strip().split())


def _date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def _period(communication: ComunicadoPreview) -> str:
    start = _date(communication.start_date)
    end = _date(communication.end_date)
    if start and end:
        return f"{start} a {end}"
    if start:
        return f"A partir de {start}"
    if end:
        return f"Até {end}"
    return "Sem período definido"


def _theme(communication: ComunicadoPreview) -> tuple[str, str]:
    """Retorna tema visual e ícone usando apenas dados já existentes do comunicado."""
    text = _norm(
        " ".join(
            (
                communication.category,
                communication.priority,
                communication.title,
            )
        )
    )

    if any(word in text for word in ("urgente", "critica", "crítica", "alerta", "suspens", "bloque")):
        return "alert", "warning_amber"
    if any(word in text for word in ("atualiza", "mudanca", "mudança", "alteracao", "alteração", "novo", "novidade")):
        return "update", "sync_alt"
    if any(word in text for word in ("orienta", "processo", "fluxo", "manual", "instrucao", "instrução")):
        return "guide", "route"
    if any(word in text for word in ("campanha", "beneficio", "benefício", "programa", "acao", "ação")):
        return "campaign", "auto_awesome"
    if communication.operator_name == "Geral / institucional":
        return "institutional", "domain"
    return "operator", "campaign"


def _hero_step(icon: str, title: str, subtitle: str) -> None:
    with ui.element("div").classes("portal-communications-hero-step"):
        with ui.element("div").classes("portal-communications-hero-step-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-communications-hero-step-copy"):
            ui.label(title).classes("portal-communications-hero-step-title")
            ui.label(subtitle).classes("portal-communications-hero-step-subtitle")


def _cover_art(theme: str, icon: str, *, compact: bool = False) -> None:
    with ui.element("div").classes(
        f"portal-communication-cover portal-communication-cover--{theme}"
        + (" is-compact" if compact else "")
    ):
        ui.element("span").classes("portal-communication-cover-ring ring-one")
        ui.element("span").classes("portal-communication-cover-ring ring-two")
        ui.element("span").classes("portal-communication-cover-line line-one")
        ui.element("span").classes("portal-communication-cover-line line-two")
        with ui.element("div").classes("portal-communication-cover-icon"):
            ui.icon(icon)
        ui.label("COMUNICADO").classes("portal-communication-cover-watermark")


def _gallery_card(
    communication: ComunicadoPreview,
    *,
    position: int,
) -> None:
    theme, icon = _theme(communication)
    size_class = " is-lead" if position == 0 else " is-wide" if position in (3, 8) else ""

    with ui.element("article").classes(
        f"portal-communication-gallery-card theme-{theme}{size_class}"
        + (" is-featured" if communication.featured else "")
    ):
        _cover_art(theme, icon, compact=position != 0)

        with ui.column().classes("portal-communication-gallery-body"):
            with ui.row().classes("portal-communication-gallery-tags"):
                if communication.featured:
                    ui.label("DESTAQUE").classes("portal-communication-gallery-badge is-featured")
                if communication.category:
                    ui.label(communication.category).classes("portal-communication-gallery-badge")
                if communication.priority:
                    ui.label(communication.priority).classes("portal-communication-gallery-badge is-priority")

            ui.label(communication.title).classes("portal-communication-gallery-title")
            ui.label(communication.operator_name).classes("portal-communication-gallery-operator")

            summary = communication.summary or communication.content or "Consulte o comunicado completo."
            ui.label(summary).classes("portal-communication-gallery-summary")

            with ui.row().classes("portal-communication-gallery-meta"):
                with ui.row().classes("portal-communication-gallery-meta-item"):
                    ui.icon("calendar_month")
                    ui.label(_period(communication))
                if communication.audience:
                    with ui.row().classes("portal-communication-gallery-meta-item audience"):
                        ui.icon("groups")
                        ui.label(communication.audience)

            ui.button(
                "Abrir comunicado",
                icon="arrow_outward",
                on_click=lambda cid=communication.communication_id: ui.navigate.to(
                    f"/comunicados/{cid}"
                ),
            ).props("flat no-caps").classes("portal-communication-gallery-action")


def _empty() -> None:
    with ui.element("div").classes("portal-communications-empty"):
        with ui.element("div").classes("portal-communications-empty-icon"):
            ui.icon("collections_bookmark")
        ui.label("Nenhum comunicado nesta seleção.").classes("portal-communications-empty-title")
        ui.label(
            "Ajuste a busca ou os filtros para explorar outros avisos."
        ).classes("portal-communications-empty-description")


def render_comunicados(user: dict) -> None:
    items = get_comunicados_preview()
    operators = sorted({item.operator_name for item in items if item.operator_name})
    categories = sorted({item.category for item in items if item.category})

    # Destaques vigentes primeiro; o restante preserva a ordem já fornecida pelo service.
    ordered_items = sorted(
        items,
        key=lambda item: (not (item.featured and item.period_active), not item.period_active),
    )

    with portal_layout(user=user, active="communications"):
        with ui.element("section").classes("portal-communications-hero"):
            with ui.column().classes("portal-communications-hero-copy"):
                ui.label("NOVIDADES & ORIENTAÇÕES").classes("portal-communications-hero-kicker")
                ui.label("Tudo o que mudou, em uma galeria feita para ser explorada.").classes(
                    "portal-communications-hero-title"
                )
                ui.label(
                    "Acompanhe avisos das operadoras, mudanças de processo e orientações institucionais "
                    "com destaque visual para o que merece atenção primeiro."
                ).classes("portal-communications-hero-description")

            render_hero_art(variant="communications", icon="campaign")

            with ui.element("div").classes("portal-communications-hero-flow"):
                _hero_step("visibility", "DESCUBRA", "o que mudou")
                _hero_step("filter_alt", "EXPLORE", "por tema ou operadora")
                _hero_step("task_alt", "APLIQUE", "a orientação correta")

        with ui.element("section").classes("portal-communications-gallery-intro"):
            with ui.column().classes("portal-communications-gallery-intro-copy"):
                ui.label("GALERIA DE COMUNICADOS").classes("portal-section-kicker")
                ui.label("Atualizações em destaque").classes("portal-communications-gallery-heading")
                ui.label(
                    "Cada peça reúne o contexto essencial. Abra somente quando precisar do conteúdo completo."
                ).classes("portal-communications-gallery-description")

            with ui.row().classes("portal-communications-gallery-summary"):
                with ui.column().classes("portal-communications-gallery-stat"):
                    ui.label(str(len(items)).zfill(2)).classes("portal-communications-gallery-stat-value")
                    ui.label("No acervo").classes("portal-communications-gallery-stat-label")
                with ui.column().classes("portal-communications-gallery-stat"):
                    ui.label(str(sum(item.period_active for item in items)).zfill(2)).classes(
                        "portal-communications-gallery-stat-value"
                    )
                    ui.label("Vigentes").classes("portal-communications-gallery-stat-label")

        with ui.element("section").classes("portal-communications-searchbar"):
            search = ui.input(
                placeholder="Buscar comunicado, assunto, operadora ou conteúdo..."
            ).props("borderless clearable prepend-icon=search").classes(
                "portal-communications-search"
            )
            search_button = ui.button("Pesquisar", icon="arrow_forward").props(
                "unelevated no-caps"
            ).classes("portal-communications-search-button")

        selected_category = {"value": "Todas"}
        category_buttons: dict[str, object] = {}

        with ui.element("section").classes("portal-communications-filterbar"):
            with ui.row().classes("portal-communications-category-filter"):
                ui.label("ASSUNTO").classes("portal-communications-filter-caption")
                for category_name in ["Todas"] + categories:
                    button = ui.button(category_name).props("flat no-caps").classes(
                        "portal-communications-chip"
                    )
                    category_buttons[category_name] = button

            with ui.row().classes("portal-communications-selects"):
                operator = ui.select(
                    ["Todas"] + operators,
                    value="Todas",
                    label="Operadora",
                ).props("outlined dense").classes("portal-communications-filter")
                period = ui.select(
                    ["Todos", "Vigentes", "Fora da vigência"],
                    value="Todos",
                    label="Período",
                ).props("outlined dense").classes("portal-communications-filter")

        with ui.row().classes("portal-communications-results-head"):
            with ui.column().classes("portal-communications-results-copy"):
                ui.label("ACERVO").classes("portal-communications-results-kicker")
                result_label = ui.label("").classes("portal-communications-result-label")
            ui.label(
                "Os destaques aparecem primeiro; a composição se reorganiza conforme os filtros."
            ).classes("portal-communications-results-note")

        gallery = ui.element("div").classes("portal-communications-gallery")

        def _paint_category_buttons() -> None:
            for name, button in category_buttons.items():
                active = name == selected_category["value"]
                button.classes(
                    add="is-active" if active else "",
                    remove="" if active else "is-active",
                )

        def refresh() -> None:
            term = _norm(search.value or "")
            filtered: list[ComunicadoPreview] = []

            for communication in ordered_items:
                haystack = _norm(
                    " ".join(
                        (
                            communication.title,
                            communication.summary,
                            communication.content,
                            communication.operator_name,
                            communication.category,
                            communication.priority,
                            communication.audience,
                            communication.responsible,
                        )
                    )
                )
                category_ok = (
                    selected_category["value"] == "Todas"
                    or communication.category == selected_category["value"]
                )
                operator_ok = operator.value == "Todas" or communication.operator_name == operator.value
                period_ok = (
                    period.value == "Todos"
                    or (period.value == "Vigentes" and communication.period_active)
                    or (period.value == "Fora da vigência" and not communication.period_active)
                )

                if (not term or term in haystack) and category_ok and operator_ok and period_ok:
                    filtered.append(communication)

            result_label.set_text(
                f"{len(filtered)} comunicado" + ("" if len(filtered) == 1 else "s") + " encontrado" + ("" if len(filtered) == 1 else "s")
            )
            _paint_category_buttons()
            gallery.clear()
            with gallery:
                if not filtered:
                    _empty()
                else:
                    for index, communication in enumerate(filtered):
                        _gallery_card(communication, position=index)

        def choose_category(name: str) -> None:
            selected_category["value"] = name
            refresh()

        for name, button in category_buttons.items():
            button.on("click", lambda _, selected=name: choose_category(selected))

        search.on("keydown.enter", lambda _: refresh())
        search_button.on("click", lambda _: refresh())
        operator.on_value_change(lambda _: refresh())
        period.on_value_change(lambda _: refresh())
        refresh()


def _detail(icon: str, label: str, value: str) -> None:
    if not value:
        return
    with ui.element("div").classes("portal-communication-detail-item"):
        with ui.element("div").classes("portal-communication-detail-item-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-communication-detail-item-copy"):
            ui.label(label).classes("portal-communication-detail-label")
            ui.label(value).classes("portal-communication-detail-value")


def render_comunicado_detail(user: dict, communication_id: str) -> None:
    communication = get_comunicado_detail(communication_id)

    with portal_layout(user=user, active="communications"):
        if not communication:
            with ui.element("div").classes("portal-communications-empty"):
                ui.icon("campaign_off")
                ui.label("Comunicado não encontrado.").classes("portal-communications-empty-title")
            return

        theme, icon = _theme(communication)

        ui.button(
            "Voltar para Comunicados",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/comunicados"),
        ).props("flat no-caps").classes("portal-communication-back")

        with ui.element("section").classes(
            f"portal-communication-detail-hero theme-{theme}"
        ):
            with ui.column().classes("portal-communication-detail-hero-copy"):
                with ui.row().classes("portal-communication-detail-badges"):
                    if communication.featured:
                        ui.label("DESTAQUE").classes("portal-communication-gallery-badge is-featured")
                    if communication.category:
                        ui.label(communication.category).classes("portal-communication-gallery-badge")
                ui.label(communication.title).classes("portal-communication-detail-title")
                ui.label(communication.operator_name).classes("portal-communication-detail-operator")
                if communication.summary:
                    ui.label(communication.summary).classes("portal-communication-detail-lead")

            _cover_art(theme, icon)

        with ui.element("section").classes("portal-communication-detail-grid"):
            _detail("business", "Operadora", communication.operator_name)
            _detail("calendar_month", "Vigência", _period(communication))
            _detail("groups", "Público-alvo", communication.audience)
            _detail("person", "Responsável", communication.responsible)
            _detail("priority_high", "Prioridade", communication.priority)
            _detail("fact_check", "Status", communication.status)

        with ui.element("section").classes("portal-communication-reading-layout"):
            with ui.element("article").classes("portal-communication-content-card"):
                ui.label("COMUNICADO COMPLETO").classes("portal-section-kicker")
                ui.label(
                    communication.content or "Nenhum conteúdo detalhado foi informado."
                ).classes("portal-communication-content")

            with ui.element("aside").classes("portal-communication-reading-aside"):
                ui.icon("bookmark_added")
                ui.label("Antes de concluir").classes("portal-communication-reading-aside-title")
                ui.label(
                    "Confira a vigência e o público-alvo acima para garantir que a orientação se aplica ao seu atendimento."
                ).classes("portal-communication-reading-aside-text")

from __future__ import annotations

from datetime import date

from nicegui import ui

from nicegui_app.hero_art import render_hero_art
from nicegui_app.layout import portal_layout
from nicegui_app.services.contingencias_service import (
    ContingenciaPreview,
    get_contingencia_detail,
    get_contingencias_preview,
)


def _norm(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _format_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def _period(item: ContingenciaPreview) -> str:
    start = _format_date(item.start_date)
    end = _format_date(item.end_date)
    if start and end:
        return f"{start} a {end}"
    if start:
        return f"A partir de {start}"
    if end:
        return f"Até {end}"
    return "Sem período definido"


def _priority_class(priority: str) -> str:
    value = _norm(priority)
    if value in {"alta", "urgente", "critica", "crítica"}:
        return "is-high"
    if value in {"media", "média"}:
        return "is-medium"
    return "is-normal"


def _status_class(item: ContingenciaPreview) -> str:
    return "is-active" if item.period_active else "is-inactive"


def _hero_step(icon: str, title: str, subtitle: str) -> None:
    with ui.element("div").classes("portal-contingencies-hero-step"):
        with ui.element("div").classes("portal-contingencies-hero-step-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-contingencies-hero-step-copy"):
            ui.label(title).classes("portal-contingencies-hero-step-title")
            ui.label(subtitle).classes("portal-contingencies-hero-step-subtitle")


def _priority_badge(item: ContingenciaPreview) -> None:
    with ui.element("div").classes(
        f"portal-contingency-priority {_priority_class(item.priority)}"
    ):
        ui.icon("priority_high")
        ui.label(item.priority)


def _status_badge(item: ContingenciaPreview) -> None:
    with ui.element("div").classes(
        f"portal-contingency-status {_status_class(item)}"
    ):
        ui.element("span").classes("portal-contingency-status-dot")
        ui.label("Ativa agora" if item.period_active else item.status)


def _active_card(item: ContingenciaPreview) -> None:
    """Card de resposta rápida para contingências vigentes."""
    with ui.element("article").classes(
        f"portal-contingency-live-card {_priority_class(item.priority)}"
    ):
        with ui.row().classes("portal-contingency-live-head"):
            with ui.row().classes("portal-contingency-live-identity"):
                with ui.element("div").classes("portal-contingency-live-icon"):
                    ui.icon("warning_amber")
                with ui.column().classes("portal-contingency-live-heading-copy"):
                    ui.label(item.operator_name).classes("portal-contingency-live-operator")
                    ui.label(item.title).classes("portal-contingency-live-title")
            with ui.row().classes("portal-contingency-live-badges"):
                _priority_badge(item)
                _status_badge(item)

        scope = " · ".join(v for v in (item.plan_name, item.local_name) if v)
        if scope:
            with ui.row().classes("portal-contingency-live-scope"):
                ui.icon("location_on")
                ui.label(scope)

        with ui.element("div").classes("portal-contingency-response-grid"):
            with ui.element("section").classes("portal-contingency-response-block is-context"):
                with ui.row().classes("portal-contingency-response-label"):
                    ui.icon("error_outline")
                    ui.label("O QUE MUDOU")
                ui.label(
                    item.description or "Consulte a orientação completa desta contingência."
                ).classes("portal-contingency-response-text")

            with ui.element("section").classes("portal-contingency-response-block is-action"):
                with ui.row().classes("portal-contingency-response-label"):
                    ui.icon("alt_route")
                    ui.label("FAÇA AGORA")
                ui.label(
                    item.alternative_guidance
                    or "Abra a orientação completa para verificar o fluxo alternativo."
                ).classes("portal-contingency-response-text")

            with ui.element("section").classes("portal-contingency-response-block is-support"):
                with ui.row().classes("portal-contingency-response-label"):
                    ui.icon("support_agent")
                    ui.label("APOIO")
                ui.label(
                    item.alternative_contact or "Contato alternativo não informado."
                ).classes("portal-contingency-response-text")

        with ui.row().classes("portal-contingency-live-footer"):
            with ui.row().classes("portal-contingency-live-period"):
                ui.icon("schedule")
                ui.label(_period(item))
            ui.button(
                "Abrir orientação completa",
                icon="arrow_forward",
                on_click=lambda cid=item.contingency_id: ui.navigate.to(f"/contingencias/{cid}"),
            ).props("unelevated no-caps").classes("portal-contingency-live-button")


def _history_card(item: ContingenciaPreview) -> None:
    with ui.element("article").classes("portal-contingency-history-card"):
        with ui.row().classes("portal-contingency-history-top"):
            with ui.element("div").classes("portal-contingency-history-icon"):
                ui.icon("route")
            _priority_badge(item)

        ui.label(item.title).classes("portal-contingency-history-title")
        ui.label(item.operator_name).classes("portal-contingency-history-operator")

        meta = " · ".join(v for v in (item.plan_name, item.local_name) if v)
        if meta:
            ui.label(meta).classes("portal-contingency-history-meta")

        ui.label(
            item.description or item.alternative_guidance or "Consulte os detalhes da contingência."
        ).classes("portal-contingency-history-description")

        with ui.column().classes("portal-contingency-history-info"):
            with ui.row().classes("portal-contingency-history-info-line"):
                ui.icon("calendar_month")
                ui.label(_period(item))
            if item.alternative_contact:
                with ui.row().classes("portal-contingency-history-info-line"):
                    ui.icon("contact_phone")
                    ui.label(item.alternative_contact)

        with ui.row().classes("portal-contingency-history-actions"):
            _status_badge(item)
            ui.button(
                "Ver orientação",
                icon="arrow_forward",
                on_click=lambda cid=item.contingency_id: ui.navigate.to(f"/contingencias/{cid}"),
            ).props("flat no-caps").classes("portal-contingency-history-button")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-contingencies-empty"):
        ui.icon("verified_user")
        ui.label(title).classes("portal-contingencies-empty-title")
        ui.label(description).classes("portal-contingencies-empty-description")


def render_contingencias(user: dict) -> None:
    items = get_contingencias_preview()
    active_items = [item for item in items if item.period_active]
    inactive_items = [item for item in items if not item.period_active]

    # Ativas primeiro; dentro do grupo, maior prioridade primeiro.
    priority_order = {"is-high": 0, "is-medium": 1, "is-normal": 2}
    active_items = sorted(
        active_items,
        key=lambda item: (priority_order[_priority_class(item.priority)], item.title.lower()),
    )

    with portal_layout(user=user, active="contingencies"):
        with ui.element("section").classes("portal-contingencies-hero"):
            with ui.column().classes("portal-contingencies-hero-copy"):
                ui.label("CENTRAL DE CONTINGÊNCIAS").classes("portal-contingencies-hero-kicker")
                ui.label("Quando o fluxo muda, saiba exatamente como seguir.").classes(
                    "portal-contingencies-hero-title"
                )
                ui.label(
                    "Visualize indisponibilidades, caminhos alternativos e contatos de apoio "
                    "com prioridade para o que exige ação imediata."
                ).classes("portal-contingencies-hero-description")

            render_hero_art(variant="contingencies", icon="shield")

            with ui.element("div").classes("portal-contingencies-hero-flow"):
                _hero_step("warning_amber", "IDENTIFIQUE", "o que mudou")
                _hero_step("alt_route", "REDIRECIONE", "para o fluxo alternativo")
                _hero_step("support_agent", "ACIONE", "o apoio correto")

        with ui.element("section").classes("portal-contingencies-command-strip"):
            with ui.column().classes("portal-contingencies-command-copy"):
                ui.label("PAINEL OPERACIONAL").classes("portal-section-kicker")
                ui.label("Situação atual das contingências").classes(
                    "portal-contingencies-command-title"
                )
                ui.label(
                    "Contingências vigentes aparecem primeiro porque representam mudança imediata no fluxo de trabalho."
                ).classes("portal-contingencies-command-description")

            with ui.row().classes("portal-contingencies-command-stats"):
                with ui.column().classes("portal-contingencies-command-stat is-active"):
                    ui.label(str(len(active_items)).zfill(2)).classes(
                        "portal-contingencies-command-value"
                    )
                    ui.label("Ativas agora").classes("portal-contingencies-command-label")
                with ui.column().classes("portal-contingencies-command-stat is-critical"):
                    ui.label(
                        str(sum(_priority_class(i.priority) == "is-high" for i in active_items)).zfill(2)
                    ).classes("portal-contingencies-command-value")
                    ui.label("Alta prioridade").classes("portal-contingencies-command-label")
                with ui.column().classes("portal-contingencies-command-stat"):
                    ui.label(str(len(items)).zfill(2)).classes("portal-contingencies-command-value")
                    ui.label("No histórico").classes("portal-contingencies-command-label")

        if active_items:
            with ui.row().classes("portal-contingencies-section-head is-live"):
                with ui.column().classes("portal-contingencies-section-copy"):
                    ui.label("ATENÇÃO AGORA").classes("portal-contingencies-section-kicker")
                    ui.label("Contingências em vigor").classes("portal-contingencies-section-title")
                with ui.element("div").classes("portal-contingencies-live-indicator"):
                    ui.element("span").classes("portal-contingencies-live-dot")
                    ui.label("Fluxos alternativos ativos")

            with ui.element("div").classes("portal-contingencies-live-list"):
                for item in active_items:
                    _active_card(item)
        else:
            with ui.element("section").classes("portal-contingencies-all-clear"):
                with ui.element("div").classes("portal-contingencies-all-clear-icon"):
                    ui.icon("verified_user")
                with ui.column().classes("portal-contingencies-all-clear-copy"):
                    ui.label("OPERAÇÃO SEM CONTINGÊNCIAS ATIVAS").classes(
                        "portal-contingencies-all-clear-kicker"
                    )
                    ui.label("Nenhum fluxo alternativo está vigente agora.").classes(
                        "portal-contingencies-all-clear-title"
                    )
                    ui.label(
                        "Continue utilizando os fluxos habituais. O histórico permanece disponível para consulta abaixo."
                    ).classes("portal-contingencies-all-clear-description")

        operators = sorted({item.operator_name for item in items if item.operator_name})
        priorities = sorted({item.priority for item in items if item.priority})

        with ui.element("section").classes("portal-contingencies-search-panel"):
            with ui.row().classes("portal-contingencies-search-row"):
                search = ui.input(
                    placeholder="Buscar evento, operadora, orientação ou contato..."
                ).props("borderless clearable prepend-icon=search").classes(
                    "portal-contingencies-search"
                )
                search_button = ui.button("Pesquisar", icon="arrow_forward").props(
                    "unelevated no-caps"
                ).classes("portal-contingencies-search-button")

            with ui.row().classes("portal-contingencies-filters"):
                operator = ui.select(
                    ["Todas"] + operators,
                    value="Todas",
                    label="Operadora",
                ).props("outlined dense").classes("portal-contingencies-filter")
                priority = ui.select(
                    ["Todas"] + priorities,
                    value="Todas",
                    label="Prioridade",
                ).props("outlined dense").classes("portal-contingencies-filter")
                period = ui.select(
                    ["Todos", "Ativas", "Fora da vigência"],
                    value="Todos",
                    label="Período",
                ).props("outlined dense").classes("portal-contingencies-filter")

        with ui.row().classes("portal-contingencies-results-head"):
            with ui.column().classes("portal-contingencies-results-copy"):
                ui.label("CONSULTA COMPLETA").classes("portal-contingencies-results-kicker")
                count = ui.label("").classes("portal-contingencies-results-title")
            ui.label(
                "Use os filtros para consultar contingências atuais ou registros anteriores."
            ).classes("portal-contingencies-results-note")

        grid = ui.element("div").classes("portal-contingencies-history-grid")

        def refresh() -> None:
            term = _norm(search.value or "")
            filtered: list[ContingenciaPreview] = []

            for item in items:
                haystack = _norm(
                    " ".join(
                        (
                            item.code,
                            item.title,
                            item.description,
                            item.alternative_guidance,
                            item.alternative_contact,
                            item.operator_name,
                            item.plan_name,
                            item.local_name,
                            item.priority,
                            item.status,
                        )
                    )
                )
                operator_ok = operator.value == "Todas" or item.operator_name == operator.value
                priority_ok = priority.value == "Todas" or item.priority == priority.value
                period_ok = (
                    period.value == "Todos"
                    or (period.value == "Ativas" and item.period_active)
                    or (period.value == "Fora da vigência" and not item.period_active)
                )

                if (not term or term in haystack) and operator_ok and priority_ok and period_ok:
                    filtered.append(item)

            filtered.sort(
                key=lambda item: (
                    0 if item.period_active else 1,
                    priority_order[_priority_class(item.priority)],
                    item.title.lower(),
                )
            )

            suffix = "" if len(filtered) == 1 else "s"
            count.set_text(f"{len(filtered)} contingência{suffix} encontrada{suffix}")
            grid.clear()

            with grid:
                if not filtered:
                    _empty(
                        "Nenhuma contingência encontrada.",
                        "Revise a pesquisa ou altere os filtros para ampliar a consulta.",
                    )
                    return
                for item in filtered:
                    _history_card(item)

        search.on("keydown.enter", lambda _: refresh())
        search_button.on("click", lambda _: refresh())
        operator.on_value_change(lambda _: refresh())
        priority.on_value_change(lambda _: refresh())
        period.on_value_change(lambda _: refresh())
        refresh()


def _detail_item(icon: str, label: str, value: str) -> None:
    if not value:
        return
    with ui.element("div").classes("portal-contingency-detail-item"):
        with ui.element("div").classes("portal-contingency-detail-item-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-contingency-detail-item-copy"):
            ui.label(label).classes("portal-contingency-detail-label")
            ui.label(value).classes("portal-contingency-detail-value")


def render_contingencia_detail(user: dict, contingency_id: str) -> None:
    item = get_contingencia_detail(contingency_id)

    with portal_layout(user=user, active="contingencies"):
        if not item:
            _empty(
                "Contingência não encontrada.",
                "O registro pode ter sido removido ou o endereço está incorreto.",
            )
            return

        ui.button(
            "Voltar para Contingências",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/contingencias"),
        ).props("flat no-caps").classes("portal-contingency-back-button")

        with ui.element("section").classes(
            f"portal-contingency-detail-hero {_priority_class(item.priority)}"
        ):
            with ui.column().classes("portal-contingency-detail-copy"):
                with ui.row().classes("portal-contingency-detail-badges"):
                    _priority_badge(item)
                    _status_badge(item)
                ui.label("ORIENTAÇÃO DE CONTINGÊNCIA").classes("portal-contingency-detail-kicker")
                ui.label(item.title).classes("portal-contingency-detail-title")
                ui.label(item.operator_name).classes("portal-contingency-detail-operator")

            with ui.element("div").classes("portal-contingency-detail-shield"):
                ui.icon("shield")
                ui.element("span").classes("portal-contingency-detail-shield-ring")

        with ui.element("section").classes("portal-contingency-detail-grid"):
            _detail_item("business", "Operadora", item.operator_name)
            _detail_item("view_list", "Plano", item.plan_name)
            _detail_item("place", "Local", item.local_name)
            _detail_item("calendar_month", "Período", _period(item))
            _detail_item("priority_high", "Prioridade", item.priority)
            _detail_item("tag", "Código", item.code)

        with ui.element("section").classes("portal-contingency-response-detail"):
            with ui.element("article").classes("portal-contingency-detail-context"):
                with ui.row().classes("portal-contingency-detail-section-head"):
                    with ui.element("div").classes("portal-contingency-detail-section-icon"):
                        ui.icon("error_outline")
                    with ui.column().classes("portal-contingency-detail-section-copy"):
                        ui.label("01 · ENTENDA").classes("portal-contingency-detail-section-kicker")
                        ui.label("O que está acontecendo").classes("portal-contingency-detail-section-title")
                ui.label(
                    item.description or "Nenhuma descrição adicional foi informada."
                ).classes("portal-contingency-detail-section-text")

            with ui.element("article").classes("portal-contingency-detail-action"):
                with ui.row().classes("portal-contingency-detail-section-head"):
                    with ui.element("div").classes("portal-contingency-detail-section-icon"):
                        ui.icon("alt_route")
                    with ui.column().classes("portal-contingency-detail-section-copy"):
                        ui.label("02 · AJA").classes("portal-contingency-detail-section-kicker")
                        ui.label("Siga o fluxo alternativo").classes("portal-contingency-detail-section-title")
                ui.label(
                    item.alternative_guidance
                    or "Nenhuma orientação alternativa foi cadastrada para esta contingência."
                ).classes("portal-contingency-detail-section-text")

            with ui.element("aside").classes("portal-contingency-detail-support"):
                with ui.element("div").classes("portal-contingency-detail-support-icon"):
                    ui.icon("support_agent")
                ui.label("03 · ACIONE").classes("portal-contingency-detail-support-kicker")
                ui.label("Contato de apoio").classes("portal-contingency-detail-support-title")
                ui.label(
                    item.alternative_contact or "Contato alternativo não informado."
                ).classes("portal-contingency-detail-support-value")
                ui.label(
                    "Utilize este canal quando precisar de apoio para executar o fluxo alternativo."
                ).classes("portal-contingency-detail-support-note")

from __future__ import annotations
from datetime import date
from nicegui import ui
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
    return ""

def _status_class(item: ContingenciaPreview) -> str:
    return "is-active" if item.period_active and _norm(item.status) == "ativo" else ""

def _card(item: ContingenciaPreview) -> None:
    with ui.element("article").classes("portal-contingency-card"):
        with ui.row().classes("portal-contingency-card-top"):
            with ui.element("div").classes("portal-contingency-icon"):
                ui.icon("warning_amber")
            with ui.element("div").classes(
                f"portal-contingency-priority {_priority_class(item.priority)}"
            ):
                ui.label(item.priority)

        ui.label(item.title).classes("portal-contingency-title")
        ui.label(item.operator_name).classes("portal-contingency-operator")

        meta = " · ".join(v for v in (item.plan_name, item.local_name) if v)
        if meta:
            ui.label(meta).classes("portal-contingency-meta")

        ui.label(
            item.description or item.alternative_guidance or "Consulte os detalhes da contingência."
        ).classes("portal-contingency-description")

        with ui.column().classes("portal-contingency-info"):
            with ui.row().classes("portal-contingency-info-line"):
                ui.icon("calendar_month")
                ui.label(_period(item))
            if item.alternative_contact:
                with ui.row().classes("portal-contingency-info-line"):
                    ui.icon("contact_phone")
                    ui.label(item.alternative_contact)

        with ui.row().classes("portal-contingency-actions"):
            with ui.element("div").classes(
                f"portal-contingency-status {_status_class(item)}"
            ):
                ui.element("span").classes("portal-contingency-status-dot")
                ui.label("Ativa" if item.period_active else item.status)

            ui.button(
                "Ver orientação",
                icon="arrow_forward",
                on_click=lambda cid=item.contingency_id: ui.navigate.to(f"/contingencias/{cid}"),
            ).props("flat no-caps").classes("portal-contingency-button")

def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-contingencies-empty"):
        ui.icon("warning_amber")
        ui.label(title).classes("portal-contingencies-empty-title")
        ui.label(description).classes("portal-contingencies-empty-description")

def render_contingencias(user: dict) -> None:
    items = get_contingencias_preview()

    with portal_layout(
        user=user,
        active="contingencies",
        page_eyebrow="CENTRAL DE CONTINGÊNCIAS",
        page_title="Quando o fluxo muda, a orientação precisa estar clara.",
        page_description=(
            "Consulte indisponibilidades, caminhos alternativos, contatos de apoio "
            "e períodos de contingência."
        ),
    ):
        operators = sorted({i.operator_name for i in items if i.operator_name})
        priorities = sorted({i.priority for i in items if i.priority})

        with ui.element("section").classes("portal-contingencies-summary"):
            with ui.column().classes("portal-contingencies-summary-copy"):
                ui.label("INCIDENTES OPERACIONAIS").classes("portal-section-kicker")
                ui.label(f"{len(items):02d} contingências cadastradas").classes(
                    "portal-contingencies-summary-value"
                )
                ui.label(
                    "Fluxos alternativos e orientações para manter a operação."
                ).classes("portal-contingencies-summary-description")

            with ui.row().classes("portal-contingencies-summary-stats"):
                for value, label in (
                    (sum(1 for i in items if i.period_active), "Ativas agora"),
                    (sum(1 for i in items if _priority_class(i.priority) == "is-high"), "Alta prioridade"),
                ):
                    with ui.column().classes("portal-contingencies-mini-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-contingencies-mini-value"
                        )
                        ui.label(label).classes("portal-contingencies-mini-label")

        active_items = [i for i in items if i.period_active]
        if active_items:
            ui.label("ATIVAS AGORA").classes(
                "portal-section-kicker portal-contingencies-active-heading"
            )
            with ui.element("div").classes("portal-contingencies-grid"):
                for item in active_items[:3]:
                    _card(item)

        with ui.element("section").classes("portal-contingencies-toolbar"):
            search = ui.input(
                placeholder="Buscar evento, operadora, orientação ou contato"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-contingencies-search"
            )
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

        count = ui.label("").classes("portal-contingencies-count")
        grid = ui.element("div").classes("portal-contingencies-grid")

        def refresh() -> None:
            term = _norm(search.value or "")
            filtered: list[ContingenciaPreview] = []

            for item in items:
                haystack = _norm(
                    " ".join(
                        (
                            item.title,
                            item.description,
                            item.alternative_guidance,
                            item.alternative_contact,
                            item.operator_name,
                            item.plan_name,
                            item.local_name,
                            item.priority,
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

            count.set_text(f"{len(filtered)} contingência(s) encontrada(s)")
            grid.clear()

            with grid:
                if not filtered:
                    _empty(
                        "Nenhuma contingência encontrada.",
                        "Revise a pesquisa ou altere os filtros.",
                    )
                    return
                for item in filtered:
                    _card(item)

        for control in (search, operator, priority, period):
            control.on_value_change(lambda _: refresh())
        refresh()

def _detail_item(icon: str, label: str, value: str) -> None:
    if not value:
        return
    with ui.element("div").classes("portal-contingency-detail-item"):
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

        with ui.element("section").classes("portal-contingency-detail-hero"):
            with ui.element("div").classes("portal-contingency-detail-icon"):
                ui.icon("warning_amber")
            with ui.column().classes("portal-contingency-detail-copy"):
                ui.label("ORIENTAÇÃO DE CONTINGÊNCIA").classes("portal-section-kicker")
                ui.label(item.title).classes("portal-contingency-detail-title")
                ui.label(item.operator_name).classes("portal-contingency-detail-operator")
                with ui.row().classes("portal-contingency-detail-badges"):
                    with ui.element("div").classes(
                        f"portal-contingency-priority {_priority_class(item.priority)}"
                    ):
                        ui.label(item.priority)
                    with ui.element("div").classes(
                        f"portal-contingency-status {_status_class(item)}"
                    ):
                        ui.element("span").classes("portal-contingency-status-dot")
                        ui.label("Ativa" if item.period_active else item.status)

        with ui.element("section").classes("portal-contingency-detail-grid"):
            _detail_item("business", "Operadora", item.operator_name)
            _detail_item("view_list", "Plano", item.plan_name)
            _detail_item("place", "Local", item.local_name)
            _detail_item("calendar_month", "Período", _period(item))
            _detail_item("priority_high", "Prioridade", item.priority)
            _detail_item("tag", "Código", item.code)

        if item.description:
            with ui.element("section").classes("portal-contingency-content-card"):
                ui.label("O QUE ESTÁ ACONTECENDO").classes("portal-section-kicker")
                ui.label(item.description).classes("portal-contingency-content")

        if item.alternative_guidance:
            with ui.element("section").classes("portal-contingency-guidance-card"):
                with ui.row().classes("portal-contingency-guidance-head"):
                    ui.icon("alt_route")
                    ui.label("Fluxo alternativo").classes("portal-contingency-guidance-title")
                ui.label(item.alternative_guidance).classes("portal-contingency-guidance-text")

        if item.alternative_contact:
            with ui.element("section").classes("portal-contingency-contact-card"):
                ui.icon("contact_phone")
                with ui.column().classes("portal-contingency-contact-copy"):
                    ui.label("Contato alternativo").classes("portal-contingency-contact-label")
                    ui.label(item.alternative_contact).classes("portal-contingency-contact-value")

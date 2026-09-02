from __future__ import annotations

from urllib.parse import urlparse

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.operadoras_service import (
    OperadoraPreview,
    get_operadora_detail,
    get_operadoras_preview,
)


def _normalized(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _is_active(status: str) -> bool:
    return _normalized(status) == "ativo"


def _safe_external_url(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return None


def _operator_mark(operator: OperadoraPreview) -> None:
    if operator.logo_url:
        ui.image(operator.logo_url).classes("portal-operator-logo-image")
        return

    initials = "".join(
        word[0]
        for word in operator.short_name.split()
        if word
    )[:2].upper() or "OP"
    ui.label(initials).classes("portal-operator-initials")


def _operator_card(operator: OperadoraPreview) -> None:
    with ui.element("article").classes("portal-operator-card"):
        with ui.row().classes("portal-operator-card-top"):
            with ui.element("div").classes("portal-operator-mark"):
                _operator_mark(operator)

            with ui.element("div").classes(
                "portal-operator-status is-active"
                if _is_active(operator.status)
                else "portal-operator-status"
            ):
                ui.element("span").classes("portal-operator-status-dot")
                ui.label(operator.status)

        with ui.column().classes("portal-operator-card-copy"):
            ui.label(operator.short_name).classes("portal-operator-card-title")

            if operator.name != operator.short_name:
                ui.label(operator.name).classes("portal-operator-card-name")

            if operator.code:
                ui.label(f"Código {operator.code}").classes(
                    "portal-operator-card-code"
                )

            ui.label(
                operator.observations
                or "Consulte planos, portais, orientações e informações vinculadas."
            ).classes("portal-operator-card-description")

        with ui.row().classes("portal-operator-card-footer"):
            with ui.button(
                "Abrir operadora",
                icon="arrow_forward",
                on_click=lambda operator_id=operator.operator_id: ui.navigate.to(
                    f"/operadoras/{operator_id}"
                ),
            ).props("flat no-caps").classes("portal-operator-open-button"):
                pass


def render_operadoras(user: dict) -> None:
    operators = get_operadoras_preview()

    with portal_layout(
        user=user,
        active="operators",
        page_eyebrow="CENTRAL DE OPERADORAS",
        page_title="Encontre a operadora. Acesse a informação.",
        page_description=(
            "Consulte a base institucional de operadoras e avance para "
            "planos e demais informações relacionadas."
        ),
    ):
        active_count = sum(
            1 for operator in operators if _is_active(operator.status)
        )

        with ui.element("section").classes("portal-operators-summary"):
            with ui.element("div").classes("portal-operators-summary-main"):
                ui.label("BASE ATUAL").classes("portal-section-kicker")
                ui.label(f"{len(operators):02d} operadoras cadastradas").classes(
                    "portal-operators-summary-value"
                )
                ui.label(
                    "Dados carregados diretamente do Supabase."
                ).classes("portal-operators-summary-description")

            with ui.row().classes("portal-operators-summary-stats"):
                with ui.column().classes("portal-operators-mini-stat"):
                    ui.label(str(active_count).zfill(2)).classes(
                        "portal-operators-mini-value"
                    )
                    ui.label("Ativas").classes("portal-operators-mini-label")
                with ui.column().classes("portal-operators-mini-stat"):
                    ui.label(str(len(operators) - active_count).zfill(2)).classes(
                        "portal-operators-mini-value"
                    )
                    ui.label("Outros status").classes(
                        "portal-operators-mini-label"
                    )

        with ui.element("section").classes("portal-operators-toolbar"):
            search = ui.input(
                placeholder="Buscar por nome, nome curto ou código"
            ).props("outlined dense clearable").classes(
                "portal-operators-search"
            )
            search.props("prepend-icon=search")

            status = ui.select(
                options=["Todos", "Ativo", "Outros"],
                value="Todos",
                label="Status",
            ).props("outlined dense").classes("portal-operators-filter")

        results_label = ui.label("").classes("portal-operators-result-label")
        cards = ui.element("div").classes("portal-operators-grid")

        def refresh_cards() -> None:
            term = _normalized(search.value or "")
            selected_status = status.value or "Todos"

            filtered: list[OperadoraPreview] = []
            for operator in operators:
                haystack = _normalized(
                    " ".join(
                        (
                            operator.name,
                            operator.short_name,
                            operator.code,
                        )
                    )
                )
                matches_term = not term or term in haystack

                if selected_status == "Ativo":
                    matches_status = _is_active(operator.status)
                elif selected_status == "Outros":
                    matches_status = not _is_active(operator.status)
                else:
                    matches_status = True

                if matches_term and matches_status:
                    filtered.append(operator)

            results_label.set_text(
                f"{len(filtered)} operadora(s) encontrada(s)"
            )

            cards.clear()
            with cards:
                if not filtered:
                    with ui.element("div").classes("portal-operators-empty"):
                        ui.icon("search_off")
                        ui.label("Nenhuma operadora encontrada.").classes(
                            "portal-operators-empty-title"
                        )
                        ui.label(
                            "Revise a busca ou altere o filtro de status."
                        ).classes("portal-operators-empty-description")
                    return

                for operator in filtered:
                    _operator_card(operator)

        search.on_value_change(lambda _: refresh_cards())
        status.on_value_change(lambda _: refresh_cards())
        refresh_cards()


def _detail_metric(icon: str, label: str, value: str) -> None:
    with ui.element("div").classes("portal-operator-detail-metric"):
        ui.icon(icon)
        with ui.column().classes("portal-operator-detail-metric-copy"):
            ui.label(label).classes("portal-operator-detail-metric-label")
            ui.label(value).classes("portal-operator-detail-metric-value")


def render_operadora_detail(user: dict, operator_id: str) -> None:
    detail = get_operadora_detail(operator_id)

    with portal_layout(
        user=user,
        active="operators",
    ):
        if detail is None:
            with ui.element("section").classes("portal-operator-not-found"):
                ui.icon("domain_disabled")
                ui.label("Operadora não encontrada.").classes(
                    "portal-operators-empty-title"
                )
                ui.label(
                    "O registro pode ter sido removido ou o endereço está incorreto."
                ).classes("portal-operators-empty-description")
                ui.button(
                    "Voltar para Operadoras",
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/operadoras"),
                ).props("unelevated no-caps").classes("portal-button-primary")
            return

        operator = detail.operator
        external_url = _safe_external_url(operator.site_url)

        with ui.row().classes("portal-operator-detail-back-row"):
            ui.button(
                "Voltar para Operadoras",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/operadoras"),
            ).props("flat no-caps").classes("portal-operator-back-button")

        with ui.element("section").classes("portal-operator-detail-hero"):
            with ui.element("div").classes("portal-operator-detail-mark"):
                _operator_mark(operator)

            with ui.column().classes("portal-operator-detail-copy"):
                with ui.row().classes("portal-operator-detail-meta"):
                    ui.label("FICHA DA OPERADORA").classes(
                        "portal-section-kicker"
                    )
                    with ui.element("div").classes(
                        "portal-operator-status is-active"
                        if _is_active(operator.status)
                        else "portal-operator-status"
                    ):
                        ui.element("span").classes(
                            "portal-operator-status-dot"
                        )
                        ui.label(operator.status)

                ui.label(operator.short_name).classes(
                    "portal-operator-detail-title"
                )

                if operator.name != operator.short_name:
                    ui.label(operator.name).classes(
                        "portal-operator-detail-full-name"
                    )

                ui.label(
                    operator.observations
                    or "Informações institucionais vinculadas a esta operadora."
                ).classes("portal-operator-detail-description")

            if external_url:
                ui.link(
                    "Abrir site",
                    target=external_url,
                    new_tab=True,
                ).classes("portal-operator-site-link")

        with ui.element("section").classes("portal-operator-detail-metrics"):
            _detail_metric(
                "tag",
                "Código",
                operator.code or "Não informado",
            )
            _detail_metric(
                "fact_check",
                "Status",
                operator.status,
            )
            _detail_metric(
                "view_list",
                "Planos cadastrados",
                str(len(detail.plans)).zfill(2),
            )

        with ui.element("section").classes("portal-operator-plans-section"):
            with ui.row().classes("portal-operator-plans-heading"):
                with ui.column().classes("portal-operator-plans-heading-copy"):
                    ui.label("PLANOS VINCULADOS").classes(
                        "portal-section-kicker"
                    )
                    ui.label("Planos desta operadora").classes(
                        "portal-section-title"
                    )
                ui.label(f"{len(detail.plans):02d} registro(s)").classes(
                    "portal-db-count-badge"
                )

            if not detail.plans:
                with ui.element("div").classes("portal-operators-empty"):
                    ui.icon("inventory_2")
                    ui.label("Nenhum plano cadastrado.").classes(
                        "portal-operators-empty-title"
                    )
                    ui.label(
                        "A operadora está ativa na base, mas ainda não possui "
                        "planos vinculados."
                    ).classes("portal-operators-empty-description")
            else:
                with ui.element("div").classes("portal-operator-plans-list"):
                    for plan in detail.plans:
                        with ui.element("article").classes(
                            "portal-operator-plan-row"
                        ):
                            with ui.element("div").classes(
                                "portal-operator-plan-icon"
                            ):
                                ui.icon("description")

                            with ui.column().classes(
                                "portal-operator-plan-copy"
                            ):
                                ui.label(
                                    plan.standardized_name or plan.name
                                ).classes("portal-operator-plan-title")

                                meta = " · ".join(
                                    item for item in (
                                        f"Código {plan.code}" if plan.code else "",
                                        plan.plan_type,
                                    )
                                    if item
                                )
                                if meta:
                                    ui.label(meta).classes(
                                        "portal-operator-plan-meta"
                                    )

                                if plan.summary:
                                    ui.label(plan.summary).classes(
                                        "portal-operator-plan-summary"
                                    )

                            ui.label(plan.status).classes(
                                "portal-operator-plan-status"
                            )

from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.contingencias_admin_service import (
    AdminContingencia,
    get_admin_contingencias,
    get_contingency_reference_data,
    is_current,
    save_contingencia,
)


PRIORITIES = ["Baixa", "Normal", "Alta", "Crítica"]


def render_admin_contingencias(user: dict) -> None:
    contingencies = get_admin_contingencias()
    refs = get_contingency_reference_data()
    operators = refs["operators"]

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · CONTINGÊNCIAS",
        page_title="Gestão de Contingências",
        page_description=(
            "Mantenha visíveis os fluxos alternativos para indisponibilidades, "
            "mudanças temporárias e situações que exigem resposta rápida."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-contingencies-back")

        with ui.element("section").classes("portal-admin-contingencies-hero"):
            with ui.column().classes("portal-admin-contingencies-hero-copy"):
                ui.label("CONTINUIDADE OPERACIONAL").classes("portal-section-kicker")
                ui.label(
                    "Quando o fluxo normal falha, a orientação precisa estar pronta."
                ).classes("portal-admin-contingencies-hero-title")
                ui.label(
                    "Cadastre contingências por operadora, plano e local, com período, "
                    "prioridade, orientação alternativa e contato de apoio."
                ).classes("portal-admin-contingencies-hero-description")

            with ui.row().classes("portal-admin-contingencies-stats"):
                stats = (
                    (len(contingencies), "Cadastradas"),
                    (sum(1 for item in contingencies if is_current(item)), "Vigentes"),
                    (
                        sum(
                            1 for item in contingencies
                            if is_current(item) and item.priority in {"Alta", "Crítica"}
                        ),
                        "Alta prioridade",
                    ),
                )
                for value, label in stats:
                    with ui.column().classes("portal-admin-contingencies-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-admin-contingencies-stat-value"
                        )
                        ui.label(label).classes(
                            "portal-admin-contingencies-stat-label"
                        )

        with ui.row().classes("portal-admin-contingencies-toolbar"):
            search = ui.input(
                placeholder="Buscar título, operadora, plano, local ou código"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-admin-contingencies-search"
            )

            operator_filter = ui.select(
                {"Todos": "Todas as operadoras", **operators},
                value="Todos",
                label="Operadora",
            ).props("outlined dense").classes("portal-admin-contingencies-filter")

            status_filter = ui.select(
                ["Todos", "Rascunho", "Publicado", "Inativo"],
                value="Todos",
                label="Status",
            ).props("outlined dense").classes("portal-admin-contingencies-filter")

            ui.button(
                "Nova contingência",
                icon="warning_amber",
                on_click=lambda: _open_dialog(user, None, refs),
            ).props("unelevated no-caps").classes(
                "portal-admin-contingencies-primary"
            )

        count = ui.label("").classes("portal-admin-contingencies-count")
        container = ui.element("section").classes("portal-admin-contingencies-list")

        def refresh() -> None:
            term = str(search.value or "").strip().lower()
            filtered: list[AdminContingencia] = []

            for item in contingencies:
                haystack = (
                    item.title,
                    item.description,
                    item.operator_name,
                    item.plan_name,
                    item.location_name,
                    item.code,
                    item.alternative_contact,
                )
                text_ok = not term or any(term in value.lower() for value in haystack)
                operator_ok = (
                    operator_filter.value == "Todos"
                    or item.operator_id == operator_filter.value
                )
                status_ok = (
                    status_filter.value == "Todos"
                    or item.status == status_filter.value
                )
                if text_ok and operator_ok and status_ok:
                    filtered.append(item)

            count.set_text(f"{len(filtered)} contingência(s)")
            container.clear()

            with container:
                if not filtered:
                    with ui.element("div").classes("portal-admin-contingencies-empty"):
                        ui.icon("verified")
                        ui.label("Nenhuma contingência encontrada.")
                    return

                for item in filtered:
                    current = is_current(item)
                    with ui.element("article").classes(
                        "portal-admin-contingencies-row"
                    ):
                        with ui.element("div").classes(
                            "portal-admin-contingencies-icon"
                        ):
                            ui.icon("warning_amber")

                        with ui.column().classes("portal-admin-contingencies-copy"):
                            ui.label(item.title).classes(
                                "portal-admin-contingencies-title"
                            )
                            ui.label(item.description).classes(
                                "portal-admin-contingencies-summary"
                            )
                            meta = " · ".join(
                                value
                                for value in (
                                    item.operator_name,
                                    item.plan_name,
                                    item.location_name,
                                )
                                if value
                            )
                            ui.label(meta).classes(
                                "portal-admin-contingencies-meta"
                            )

                        with ui.element("div").classes(
                            "portal-admin-contingencies-priority "
                            + _priority_class(item.priority)
                        ):
                            ui.label(item.priority)

                        with ui.element("div").classes(
                            "portal-admin-contingencies-status "
                            + ("is-current" if current else "")
                        ):
                            ui.element("span").classes(
                                "portal-admin-contingencies-status-dot"
                            )
                            ui.label("Vigente" if current else item.status)

                        ui.button(
                            "Editar",
                            icon="edit",
                            on_click=lambda current_item=item: _open_dialog(
                                user, current_item, refs
                            ),
                        ).props("flat no-caps").classes(
                            "portal-admin-contingencies-edit"
                        )

        search.on_value_change(lambda _: refresh())
        operator_filter.on_value_change(lambda _: refresh())
        status_filter.on_value_change(lambda _: refresh())
        refresh()


def _priority_class(priority: str) -> str:
    value = priority.strip().lower()
    if value == "crítica":
        return "is-critical"
    if value == "alta":
        return "is-high"
    if value == "baixa":
        return "is-low"
    return "is-normal"


def _open_dialog(
    user: dict,
    item: AdminContingencia | None,
    refs: dict,
) -> None:
    operators = refs["operators"]
    plans = refs["plans"]
    locations = refs["locations"]

    def plan_options(operator_id: str) -> dict[str, str]:
        options = {"": "Todos / não se aplica"}
        for plan_id, plan in plans.items():
            if plan.get("operator_id") == operator_id:
                options[plan_id] = plan.get("name") or "Plano"
        return options

    current_operator = item.operator_id if item else ""
    initial_plans = plan_options(current_operator)

    with ui.dialog() as dialog, ui.card().classes(
        "portal-admin-contingencies-dialog"
    ):
        ui.label(
            "EDITAR CONTINGÊNCIA" if item else "NOVA CONTINGÊNCIA"
        ).classes("portal-section-kicker")
        ui.label(
            item.title if item else "Cadastrar contingência"
        ).classes("portal-admin-contingencies-dialog-title")

        code = ui.input(
            "Código",
            value=item.code if item else "",
        ).props("outlined")

        operator = ui.select(
            operators,
            value=current_operator or None,
            label="Operadora *",
        ).props("outlined")

        plan = ui.select(
            initial_plans,
            value=item.plan_id if item else "",
            label="Plano",
        ).props("outlined")

        location = ui.select(
            {"": "Todos / não se aplica", **locations},
            value=item.location_id if item else "",
            label="Local de atendimento",
        ).props("outlined")

        title = ui.input(
            "Título *",
            value=item.title if item else "",
        ).props("outlined")

        description = ui.textarea(
            "Descrição *",
            value=item.description if item else "",
        ).props("outlined autogrow")

        alternative_guidance = ui.textarea(
            "Orientação alternativa",
            value=item.alternative_guidance if item else "",
            placeholder="Descreva o fluxo que deve ser seguido durante a contingência.",
        ).props("outlined autogrow")

        alternative_contact = ui.input(
            "Contato alternativo",
            value=item.alternative_contact if item else "",
        ).props("outlined")

        priority = ui.select(
            PRIORITIES,
            value=(
                item.priority
                if item and item.priority in PRIORITIES
                else "Normal"
            ),
            label="Prioridade",
        ).props("outlined")

        start_date = ui.input(
            "Início",
            value=item.start_date if item else "",
        ).props("outlined type=date")

        end_date = ui.input(
            "Fim",
            value=item.end_date if item else "",
        ).props("outlined type=date")

        status = ui.select(
            ["Rascunho", "Publicado", "Inativo"],
            value=item.status if item else "Rascunho",
            label="Status",
        ).props("outlined")

        for field in (
            code, operator, plan, location, title, description,
            alternative_guidance, alternative_contact, priority,
            start_date, end_date, status,
        ):
            field.classes("portal-admin-contingencies-dialog-field")

        def operator_changed(event) -> None:
            selected = str(event.value or "")
            options = plan_options(selected)
            plan.set_options(options, value="")

        operator.on_value_change(operator_changed)

        def save() -> None:
            try:
                save_contingencia(
                    record_id=item.record_id if item else None,
                    code=code.value or "",
                    operator_id=operator.value or "",
                    plan_id=plan.value or "",
                    location_id=location.value or "",
                    title=title.value or "",
                    description=description.value or "",
                    alternative_guidance=alternative_guidance.value or "",
                    alternative_contact=alternative_contact.value or "",
                    priority=priority.value or "",
                    start_date=start_date.value or "",
                    end_date=end_date.value or "",
                    status=status.value or "",
                    actor=user,
                )
            except Exception as error:
                ui.notify(str(error), type="negative", position="top")
                return

            ui.notify(
                "Contingência salva com sucesso.",
                type="positive",
                position="top",
            )
            dialog.close()
            ui.navigate.to("/administracao/contingencias")

        with ui.row().classes("portal-admin-contingencies-dialog-actions"):
            ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
            ui.button(
                "Salvar contingência",
                icon="check",
                on_click=save,
            ).props("unelevated no-caps").classes(
                "portal-admin-contingencies-primary"
            )

    dialog.open()

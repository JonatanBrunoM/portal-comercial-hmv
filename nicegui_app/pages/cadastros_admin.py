from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.cadastros_admin_service import (
    AdminOperadora,
    AdminPlano,
    get_admin_operadoras,
    get_admin_planos,
    save_operadora,
    save_plano,
)


def _notify_error(error: Exception) -> None:
    ui.notify(str(error), type="negative", position="top")


def render_admin_cadastros(user: dict) -> None:
    operadoras = get_admin_operadoras()
    planos = get_admin_planos()

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · CADASTROS",
        page_title="Operadoras e Planos",
        page_description=(
            "Mantenha a estrutura principal do Portal Comercial atualizada sem "
            "alterar diretamente a base de dados."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-register-back")

        with ui.element("section").classes("portal-admin-register-hero"):
            with ui.column().classes("portal-admin-register-hero-copy"):
                ui.label("BASE ESTRUTURAL").classes("portal-section-kicker")
                ui.label("Cadastros que organizam todo o portal.").classes(
                    "portal-admin-register-hero-title"
                )
                ui.label(
                    "Operadoras e planos são referências para portais, documentos, "
                    "autorizações, contatos e demais conteúdos."
                ).classes("portal-admin-register-hero-description")
            with ui.row().classes("portal-admin-register-stats"):
                for value, label in (
                    (len(operadoras), "Operadoras"),
                    (len(planos), "Planos"),
                    (sum(1 for item in operadoras if item.status.lower() == "ativo"), "Operadoras ativas"),
                ):
                    with ui.column().classes("portal-admin-register-stat"):
                        ui.label(str(value).zfill(2)).classes("portal-admin-register-stat-value")
                        ui.label(label).classes("portal-admin-register-stat-label")

        with ui.tabs().classes("portal-admin-register-tabs") as tabs:
            operators_tab = ui.tab("Operadoras", icon="domain")
            plans_tab = ui.tab("Planos", icon="health_and_safety")

        with ui.tab_panels(tabs, value=operators_tab).classes("portal-admin-register-panels"):
            with ui.tab_panel(operators_tab).classes("portal-admin-register-panel"):
                _render_operadoras(user, operadoras)

            with ui.tab_panel(plans_tab).classes("portal-admin-register-panel"):
                _render_planos(user, operadoras, planos)


def _render_operadoras(user: dict, operadoras: list[AdminOperadora]) -> None:
    with ui.row().classes("portal-admin-register-toolbar"):
        search = ui.input(
            placeholder="Buscar operadora"
        ).props("outlined dense clearable prepend-icon=search").classes(
            "portal-admin-register-search"
        )
        status_filter = ui.select(
            ["Todos", "Ativo", "Inativo"],
            value="Todos",
            label="Status",
        ).props("outlined dense").classes("portal-admin-register-filter")
        ui.button(
            "Nova operadora",
            icon="add",
            on_click=lambda: _open_operadora_dialog(user, None),
        ).props("unelevated no-caps").classes("portal-admin-register-primary")

    count = ui.label("").classes("portal-admin-register-count")
    container = ui.element("div").classes("portal-admin-register-list")

    def refresh() -> None:
        term = str(search.value or "").lower().strip()
        filtered = [
            item for item in operadoras
            if (
                not term
                or term in item.name.lower()
                or term in item.short_name.lower()
                or term in item.code.lower()
            )
            and (status_filter.value == "Todos" or item.status == status_filter.value)
        ]
        count.set_text(f"{len(filtered)} operadora(s)")
        container.clear()

        with container:
            for item in filtered:
                with ui.element("article").classes("portal-admin-register-row"):
                    with ui.element("div").classes("portal-admin-register-row-icon"):
                        ui.icon("domain")
                    with ui.column().classes("portal-admin-register-row-copy"):
                        ui.label(item.short_name or item.name).classes("portal-admin-register-row-title")
                        ui.label(item.name).classes("portal-admin-register-row-subtitle")
                        if item.code:
                            ui.label(f"Código {item.code}").classes("portal-admin-register-row-meta")
                    with ui.element("div").classes(
                        f"portal-admin-register-status {'is-active' if item.status.lower() == 'ativo' else ''}"
                    ):
                        ui.element("span").classes("portal-admin-register-status-dot")
                        ui.label(item.status)
                    ui.button(
                        "Editar",
                        icon="edit",
                        on_click=lambda current=item: _open_operadora_dialog(user, current),
                    ).props("flat no-caps").classes("portal-admin-register-edit")

    search.on_value_change(lambda _: refresh())
    status_filter.on_value_change(lambda _: refresh())
    refresh()


def _open_operadora_dialog(user: dict, item: AdminOperadora | None) -> None:
    with ui.dialog() as dialog, ui.card().classes("portal-admin-register-dialog"):
        ui.label("EDITAR OPERADORA" if item else "NOVA OPERADORA").classes("portal-section-kicker")
        ui.label(item.short_name if item else "Cadastrar operadora").classes("portal-admin-register-dialog-title")

        code = ui.input("Código", value=item.code if item else "").props("outlined")
        name = ui.input("Nome completo", value=item.name if item else "").props("outlined")
        short_name = ui.input("Nome curto", value=item.short_name if item else "").props("outlined")
        status = ui.select(["Ativo", "Inativo"], value=item.status if item else "Ativo", label="Status").props("outlined")
        site = ui.input("Site", value=item.site_url if item else "").props("outlined")
        notes = ui.textarea("Observações", value=item.notes if item else "").props("outlined autogrow")

        for field in (code, name, short_name, status, site, notes):
            field.classes("portal-admin-register-dialog-field")

        def save() -> None:
            try:
                save_operadora(
                    record_id=item.record_id if item else None,
                    code=code.value or "",
                    name=name.value or "",
                    short_name=short_name.value or "",
                    status=status.value or "",
                    site_url=site.value or "",
                    notes=notes.value or "",
                    actor=user,
                )
            except Exception as error:
                _notify_error(error)
                return
            ui.notify("Operadora salva com sucesso.", type="positive", position="top")
            dialog.close()
            ui.navigate.to("/administracao/cadastros")

        with ui.row().classes("portal-admin-register-dialog-actions"):
            ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
            ui.button("Salvar", icon="check", on_click=save).props("unelevated no-caps").classes("portal-admin-register-primary")

    dialog.open()


def _render_planos(user: dict, operadoras: list[AdminOperadora], planos: list[AdminPlano]) -> None:
    operator_options = {item.record_id: item.short_name or item.name for item in operadoras}

    with ui.row().classes("portal-admin-register-toolbar"):
        search = ui.input(
            placeholder="Buscar plano"
        ).props("outlined dense clearable prepend-icon=search").classes(
            "portal-admin-register-search"
        )
        operator_filter = ui.select(
            {"Todos": "Todas as operadoras", **operator_options},
            value="Todos",
            label="Operadora",
        ).props("outlined dense").classes("portal-admin-register-filter-wide")
        ui.button(
            "Novo plano",
            icon="add",
            on_click=lambda: _open_plano_dialog(user, None, operator_options),
        ).props("unelevated no-caps").classes("portal-admin-register-primary")

    count = ui.label("").classes("portal-admin-register-count")
    container = ui.element("div").classes("portal-admin-register-list")

    def refresh() -> None:
        term = str(search.value or "").lower().strip()
        filtered = [
            item for item in planos
            if (
                not term
                or term in item.name.lower()
                or term in item.standardized_name.lower()
                or term in item.operator_name.lower()
                or term in item.code.lower()
            )
            and (operator_filter.value == "Todos" or item.operator_id == operator_filter.value)
        ]
        count.set_text(f"{len(filtered)} plano(s)")
        container.clear()

        with container:
            for item in filtered:
                with ui.element("article").classes("portal-admin-register-row"):
                    with ui.element("div").classes("portal-admin-register-row-icon"):
                        ui.icon("health_and_safety")
                    with ui.column().classes("portal-admin-register-row-copy"):
                        ui.label(item.standardized_name or item.name).classes("portal-admin-register-row-title")
                        ui.label(item.operator_name).classes("portal-admin-register-row-subtitle")
                        meta = " · ".join(v for v in (item.plan_type, item.code) if v)
                        if meta:
                            ui.label(meta).classes("portal-admin-register-row-meta")
                    with ui.element("div").classes(
                        f"portal-admin-register-status {'is-active' if item.status.lower() == 'ativo' else ''}"
                    ):
                        ui.element("span").classes("portal-admin-register-status-dot")
                        ui.label(item.status)
                    ui.button(
                        "Editar",
                        icon="edit",
                        on_click=lambda current=item: _open_plano_dialog(user, current, operator_options),
                    ).props("flat no-caps").classes("portal-admin-register-edit")

    search.on_value_change(lambda _: refresh())
    operator_filter.on_value_change(lambda _: refresh())
    refresh()


def _open_plano_dialog(user: dict, item: AdminPlano | None, operator_options: dict[str, str]) -> None:
    with ui.dialog() as dialog, ui.card().classes("portal-admin-register-dialog"):
        ui.label("EDITAR PLANO" if item else "NOVO PLANO").classes("portal-section-kicker")
        ui.label(item.standardized_name if item else "Cadastrar plano").classes("portal-admin-register-dialog-title")

        operator = ui.select(
            operator_options,
            value=item.operator_id if item else None,
            label="Operadora",
        ).props("outlined")
        code = ui.input("Código", value=item.code if item else "").props("outlined")
        name = ui.input("Nome", value=item.name if item else "").props("outlined")
        standardized = ui.input(
            "Nome padronizado",
            value=item.standardized_name if item else "",
        ).props("outlined")
        plan_type = ui.input("Tipo do plano", value=item.plan_type if item else "").props("outlined")
        status = ui.select(["Ativo", "Inativo"], value=item.status if item else "Ativo", label="Status").props("outlined")
        summary = ui.textarea(
            "Observação resumida",
            value=item.summary if item else "",
        ).props("outlined autogrow")

        for field in (operator, code, name, standardized, plan_type, status, summary):
            field.classes("portal-admin-register-dialog-field")

        def save() -> None:
            try:
                save_plano(
                    record_id=item.record_id if item else None,
                    operator_id=operator.value or "",
                    code=code.value or "",
                    name=name.value or "",
                    standardized_name=standardized.value or "",
                    plan_type=plan_type.value or "",
                    status=status.value or "",
                    summary=summary.value or "",
                    actor=user,
                )
            except Exception as error:
                _notify_error(error)
                return
            ui.notify("Plano salvo com sucesso.", type="positive", position="top")
            dialog.close()
            ui.navigate.to("/administracao/cadastros")

        with ui.row().classes("portal-admin-register-dialog-actions"):
            ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
            ui.button("Salvar", icon="check", on_click=save).props("unelevated no-caps").classes("portal-admin-register-primary")

    dialog.open()

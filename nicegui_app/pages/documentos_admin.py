from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.documentos_admin_service import (
    AdminDocumento,
    get_admin_documentos,
    get_document_reference_data,
    save_documento,
)


def render_admin_documentos(user: dict) -> None:
    documents = get_admin_documentos()
    operators, plans, locations, attendance_types = get_document_reference_data()

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · DOCUMENTOS",
        page_title="Gestão de Documentos",
        page_description=(
            "Cadastre documentos, exigências e orientações utilizadas "
            "no atendimento aos convênios."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-documents-back")

        with ui.element("section").classes("portal-admin-documents-hero"):
            with ui.column().classes("portal-admin-documents-hero-copy"):
                ui.label("BASE DOCUMENTAL").classes("portal-section-kicker")
                ui.label(
                    "Orientações documentais em um único lugar."
                ).classes("portal-admin-documents-hero-title")
                ui.label(
                    "Relacione cada documento à operadora, plano, local e tipo "
                    "de atendimento corretos, mantendo exigências e orientações atualizadas."
                ).classes("portal-admin-documents-hero-description")

            with ui.row().classes("portal-admin-documents-stats"):
                for value, label in (
                    (len(documents), "Documentos"),
                    (
                        sum(1 for item in documents if item.required),
                        "Obrigatórios",
                    ),
                    (
                        sum(
                            1
                            for item in documents
                            if item.status.lower() == "ativo"
                        ),
                        "Ativos",
                    ),
                ):
                    with ui.column().classes("portal-admin-documents-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-admin-documents-stat-value"
                        )
                        ui.label(label).classes(
                            "portal-admin-documents-stat-label"
                        )

        with ui.row().classes("portal-admin-documents-toolbar"):
            search = ui.input(
                placeholder="Buscar documento, operadora, plano ou atendimento"
            ).props(
                "outlined dense clearable prepend-icon=search"
            ).classes("portal-admin-documents-search")

            operator_filter = ui.select(
                {"Todos": "Todas as operadoras", **operators},
                value="Todos",
                label="Operadora",
            ).props("outlined dense").classes(
                "portal-admin-documents-filter"
            )

            requirement_filter = ui.select(
                ["Todos", "Obrigatório", "Opcional"],
                value="Todos",
                label="Exigência",
            ).props("outlined dense").classes(
                "portal-admin-documents-filter"
            )

            ui.button(
                "Novo documento",
                icon="add",
                on_click=lambda: _open_dialog(
                    user,
                    None,
                    operators,
                    plans,
                    locations,
                    attendance_types,
                ),
            ).props("unelevated no-caps").classes(
                "portal-admin-documents-primary"
            )

        count = ui.label("").classes("portal-admin-documents-count")
        container = ui.element("section").classes(
            "portal-admin-documents-list"
        )

        def refresh() -> None:
            term = str(search.value or "").strip().lower()
            filtered: list[AdminDocumento] = []

            for item in documents:
                text_ok = (
                    not term
                    or any(
                        term in value.lower()
                        for value in (
                            item.name,
                            item.operator_name,
                            item.plan_name,
                            item.location_name,
                            item.attendance_type_name,
                            item.code,
                            item.file_format,
                        )
                    )
                )
                operator_ok = (
                    operator_filter.value == "Todos"
                    or item.operator_id == operator_filter.value
                )
                requirement_ok = (
                    requirement_filter.value == "Todos"
                    or (
                        requirement_filter.value == "Obrigatório"
                        and item.required
                    )
                    or (
                        requirement_filter.value == "Opcional"
                        and not item.required
                    )
                )

                if text_ok and operator_ok and requirement_ok:
                    filtered.append(item)

            count.set_text(f"{len(filtered)} documento(s)")
            container.clear()

            with container:
                if not filtered:
                    with ui.element("div").classes(
                        "portal-admin-documents-empty"
                    ):
                        ui.icon("description")
                        ui.label("Nenhum documento encontrado.")
                    return

                for item in filtered:
                    with ui.element("article").classes(
                        "portal-admin-documents-row"
                    ):
                        with ui.element("div").classes(
                            "portal-admin-documents-icon"
                        ):
                            ui.icon("description")

                        with ui.column().classes(
                            "portal-admin-documents-copy"
                        ):
                            ui.label(item.name).classes(
                                "portal-admin-documents-title"
                            )
                            ui.label(item.operator_name).classes(
                                "portal-admin-documents-operator"
                            )

                            meta = " · ".join(
                                value
                                for value in (
                                    item.plan_name,
                                    item.attendance_type_name,
                                    item.location_name,
                                    item.file_format,
                                )
                                if value
                            )
                            if meta:
                                ui.label(meta).classes(
                                    "portal-admin-documents-meta"
                                )

                        with ui.element("div").classes(
                            "portal-admin-documents-requirement "
                            + ("is-required" if item.required else "")
                        ):
                            ui.icon(
                                "priority_high"
                                if item.required
                                else "check_circle_outline"
                            )
                            ui.label(
                                "Obrigatório"
                                if item.required
                                else "Opcional"
                            )

                        with ui.element("div").classes(
                            "portal-admin-documents-status "
                            + (
                                "is-active"
                                if item.status.lower() == "ativo"
                                else ""
                            )
                        ):
                            ui.element("span").classes(
                                "portal-admin-documents-status-dot"
                            )
                            ui.label(item.status)

                        ui.button(
                            "Editar",
                            icon="edit",
                            on_click=lambda current=item: _open_dialog(
                                user,
                                current,
                                operators,
                                plans,
                                locations,
                                attendance_types,
                            ),
                        ).props("flat no-caps").classes(
                            "portal-admin-documents-edit"
                        )

        search.on_value_change(lambda _: refresh())
        operator_filter.on_value_change(lambda _: refresh())
        requirement_filter.on_value_change(lambda _: refresh())
        refresh()


def _open_dialog(
    user: dict,
    item: AdminDocumento | None,
    operators: dict[str, str],
    plans: dict[str, tuple[str, str]],
    locations: dict[str, str],
    attendance_types: dict[str, str],
) -> None:
    with ui.dialog() as dialog, ui.card().classes(
        "portal-admin-documents-dialog"
    ):
        ui.label(
            "EDITAR DOCUMENTO" if item else "NOVO DOCUMENTO"
        ).classes("portal-section-kicker")
        ui.label(
            item.name if item else "Cadastrar documento"
        ).classes("portal-admin-documents-dialog-title")

        operator = ui.select(
            operators,
            value=item.operator_id if item else None,
            label="Operadora",
        ).props("outlined")

        plan = ui.select(
            {"": "Sem plano específico"},
            value=item.plan_id if item else "",
            label="Plano",
        ).props("outlined")

        location = ui.select(
            {"": "Todos / não específico", **locations},
            value=item.location_id if item else "",
            label="Local de atendimento",
        ).props("outlined")

        attendance_type = ui.select(
            {"": "Todos / não específico", **attendance_types},
            value=item.attendance_type_id if item else "",
            label="Tipo de atendimento",
        ).props("outlined")

        code = ui.input(
            "Código",
            value=item.code if item else "",
        ).props("outlined")

        name = ui.input(
            "Nome do documento",
            value=item.name if item else "",
        ).props("outlined")

        file_format = ui.input(
            "Formato",
            value=item.file_format if item else "",
            placeholder="Ex.: PDF, físico, original, cópia",
        ).props("outlined")

        validity_days = ui.number(
            "Validade (dias)",
            value=item.validity_days if item else None,
            min=0,
            precision=0,
        ).props("outlined")

        required = ui.switch(
            "Documento obrigatório",
            value=item.required if item else False,
        )

        status = ui.select(
            ["Ativo", "Inativo"],
            value=item.status if item else "Ativo",
            label="Status",
        ).props("outlined")

        file_url = ui.input(
            "Link do arquivo",
            value=item.file_url if item else "",
            placeholder="https://...",
        ).props("outlined")

        guidance = ui.textarea(
            "Orientação",
            value=item.guidance if item else "",
        ).props("outlined autogrow")

        notes = ui.textarea(
            "Observações",
            value=item.notes if item else "",
        ).props("outlined autogrow")

        for field in (
            operator,
            plan,
            location,
            attendance_type,
            code,
            name,
            file_format,
            validity_days,
            status,
            file_url,
            guidance,
            notes,
        ):
            field.classes("portal-admin-documents-dialog-field")

        required.classes("portal-admin-documents-dialog-switch")

        def refresh_plans() -> None:
            selected_operator = str(operator.value or "")
            options = {"": "Sem plano específico"}
            options.update(
                {
                    plan_id: plan_name
                    for plan_id, (operator_id, plan_name) in plans.items()
                    if not operator_id or operator_id == selected_operator
                }
            )

            current_value = str(plan.value or "")
            plan.set_options(
                options,
                value=current_value if current_value in options else "",
            )

        operator.on_value_change(lambda _: refresh_plans())
        refresh_plans()

        def save() -> None:
            try:
                save_documento(
                    record_id=item.record_id if item else None,
                    code=code.value or "",
                    operator_id=operator.value or "",
                    plan_id=plan.value or "",
                    location_id=location.value or "",
                    attendance_type_id=attendance_type.value or "",
                    name=name.value or "",
                    required=bool(required.value),
                    file_format=file_format.value or "",
                    validity_days=validity_days.value,
                    guidance=guidance.value or "",
                    notes=notes.value or "",
                    file_url=file_url.value or "",
                    status=status.value or "",
                    actor=user,
                )
            except Exception as error:
                ui.notify(
                    str(error),
                    type="negative",
                    position="top",
                )
                return

            ui.notify(
                "Documento salvo com sucesso.",
                type="positive",
                position="top",
            )
            dialog.close()
            ui.navigate.to("/administracao/documentos")

        with ui.row().classes(
            "portal-admin-documents-dialog-actions"
        ):
            ui.button(
                "Cancelar",
                on_click=dialog.close,
            ).props("flat no-caps")

            ui.button(
                "Salvar documento",
                icon="check",
                on_click=save,
            ).props("unelevated no-caps").classes(
                "portal-admin-documents-primary"
            )

    dialog.open()

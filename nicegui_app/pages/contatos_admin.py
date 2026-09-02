from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.contatos_admin_service import (
    AdminContato,
    get_admin_contatos,
    get_contact_reference_data,
    save_contato,
)


CONTACT_TYPES = [
    "Telefone",
    "E-mail",
    "WhatsApp",
    "Portal",
    "Ramal",
    "Outro",
]


def render_admin_contatos(user: dict) -> None:
    contacts = get_admin_contatos()
    operators, plans = get_contact_reference_data()

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · CONTATOS",
        page_title="Gestão de Contatos",
        page_description=(
            "Mantenha canais, responsáveis e horários de atendimento "
            "das operadoras organizados para consulta da equipe."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-contacts-back")

        with ui.element("section").classes("portal-admin-contacts-hero"):
            with ui.column().classes("portal-admin-contacts-hero-copy"):
                ui.label("REDE DE APOIO").classes("portal-section-kicker")
                ui.label(
                    "O contato certo, para a necessidade certa."
                ).classes("portal-admin-contacts-hero-title")
                ui.label(
                    "Centralize canais de atendimento, finalidades, responsáveis "
                    "e horários para reduzir buscas paralelas durante a operação."
                ).classes("portal-admin-contacts-hero-description")

            with ui.row().classes("portal-admin-contacts-stats"):
                for value, label in (
                    (len(contacts), "Contatos"),
                    (
                        len({item.operator_id for item in contacts if item.operator_id}),
                        "Operadoras",
                    ),
                    (
                        sum(
                            1
                            for item in contacts
                            if item.status.lower() == "ativo"
                        ),
                        "Ativos",
                    ),
                ):
                    with ui.column().classes("portal-admin-contacts-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-admin-contacts-stat-value"
                        )
                        ui.label(label).classes(
                            "portal-admin-contacts-stat-label"
                        )

        with ui.row().classes("portal-admin-contacts-toolbar"):
            search = ui.input(
                placeholder="Buscar setor, finalidade, contato ou responsável"
            ).props(
                "outlined dense clearable prepend-icon=search"
            ).classes("portal-admin-contacts-search")

            operator_filter = ui.select(
                {"Todos": "Todas as operadoras", **operators},
                value="Todos",
                label="Operadora",
            ).props("outlined dense").classes(
                "portal-admin-contacts-filter"
            )

            type_options = sorted(
                {
                    item.contact_type
                    for item in contacts
                    if item.contact_type
                }
            )
            type_filter = ui.select(
                ["Todos", *type_options],
                value="Todos",
                label="Tipo",
            ).props("outlined dense").classes(
                "portal-admin-contacts-filter"
            )

            ui.button(
                "Novo contato",
                icon="add",
                on_click=lambda: _open_dialog(
                    user,
                    None,
                    operators,
                    plans,
                ),
            ).props("unelevated no-caps").classes(
                "portal-admin-contacts-primary"
            )

        count = ui.label("").classes("portal-admin-contacts-count")
        container = ui.element("section").classes(
            "portal-admin-contacts-list"
        )

        def refresh() -> None:
            term = str(search.value or "").strip().lower()
            filtered: list[AdminContato] = []

            for item in contacts:
                text_ok = (
                    not term
                    or any(
                        term in value.lower()
                        for value in (
                            item.department,
                            item.purpose,
                            item.contact,
                            item.responsible,
                            item.operator_name,
                            item.plan_name,
                            item.code,
                        )
                    )
                )
                operator_ok = (
                    operator_filter.value == "Todos"
                    or item.operator_id == operator_filter.value
                )
                type_ok = (
                    type_filter.value == "Todos"
                    or item.contact_type == type_filter.value
                )

                if text_ok and operator_ok and type_ok:
                    filtered.append(item)

            count.set_text(f"{len(filtered)} contato(s)")
            container.clear()

            with container:
                if not filtered:
                    with ui.element("div").classes(
                        "portal-admin-contacts-empty"
                    ):
                        ui.icon("contact_phone")
                        ui.label("Nenhum contato encontrado.")
                    return

                for item in filtered:
                    with ui.element("article").classes(
                        "portal-admin-contacts-row"
                    ):
                        with ui.element("div").classes(
                            "portal-admin-contacts-icon"
                        ):
                            ui.icon(_contact_icon(item.contact_type))

                        with ui.column().classes(
                            "portal-admin-contacts-copy"
                        ):
                            ui.label(item.department).classes(
                                "portal-admin-contacts-title"
                            )
                            ui.label(item.purpose).classes(
                                "portal-admin-contacts-purpose"
                            )

                            meta = " · ".join(
                                value
                                for value in (
                                    item.operator_name,
                                    item.plan_name,
                                    item.responsible,
                                )
                                if value
                            )
                            if meta:
                                ui.label(meta).classes(
                                    "portal-admin-contacts-meta"
                                )

                        with ui.column().classes(
                            "portal-admin-contacts-channel"
                        ):
                            if item.contact_type:
                                ui.label(item.contact_type).classes(
                                    "portal-admin-contacts-channel-type"
                                )
                            ui.label(item.contact).classes(
                                "portal-admin-contacts-channel-value"
                            )

                        with ui.element("div").classes(
                            "portal-admin-contacts-status "
                            + (
                                "is-active"
                                if item.status.lower() == "ativo"
                                else ""
                            )
                        ):
                            ui.element("span").classes(
                                "portal-admin-contacts-status-dot"
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
                            ),
                        ).props("flat no-caps").classes(
                            "portal-admin-contacts-edit"
                        )

        search.on_value_change(lambda _: refresh())
        operator_filter.on_value_change(lambda _: refresh())
        type_filter.on_value_change(lambda _: refresh())
        refresh()


def _contact_icon(contact_type: str) -> str:
    value = contact_type.strip().lower()

    if "mail" in value:
        return "mail"
    if "whats" in value:
        return "chat"
    if "portal" in value or "site" in value:
        return "language"
    if "ramal" in value:
        return "dialpad"
    if "tel" in value or "fone" in value:
        return "phone"

    return "contact_phone"


def _open_dialog(
    user: dict,
    item: AdminContato | None,
    operators: dict[str, str],
    plans: dict[str, tuple[str, str]],
) -> None:
    with ui.dialog() as dialog, ui.card().classes(
        "portal-admin-contacts-dialog"
    ):
        ui.label(
            "EDITAR CONTATO" if item else "NOVO CONTATO"
        ).classes("portal-section-kicker")
        ui.label(
            item.department if item else "Cadastrar contato"
        ).classes("portal-admin-contacts-dialog-title")

        operator = ui.select(
            operators,
            value=item.operator_id if item else None,
            label="Operadora",
        ).props("outlined")

        selected_operator_id = item.operator_id if item else ""
        initial_plan_options = {"": "Sem plano específico"}
        initial_plan_options.update(
            {
                plan_id: plan_name
                for plan_id, (operator_id, plan_name) in plans.items()
                if not operator_id or operator_id == selected_operator_id
            }
        )

        initial_plan_value = item.plan_id if item else ""
        if initial_plan_value not in initial_plan_options:
            initial_plan_value = ""

        plan = ui.select(
            initial_plan_options,
            value=initial_plan_value,
            label="Plano",
        ).props("outlined")

        code = ui.input(
            "Código",
            value=item.code if item else "",
        ).props("outlined")

        department = ui.input(
            "Setor / área",
            value=item.department if item else "",
            placeholder="Ex.: Central de Autorizações",
        ).props("outlined")

        purpose = ui.input(
            "Finalidade",
            value=item.purpose if item else "",
            placeholder="Ex.: Solicitação de autorização",
        ).props("outlined")

        contact_type = ui.select(
            CONTACT_TYPES,
            value=(
                item.contact_type
                if item and item.contact_type in CONTACT_TYPES
                else "Telefone"
            ),
            label="Tipo de contato",
        ).props("outlined")

        contact = ui.input(
            "Contato",
            value=item.contact if item else "",
            placeholder="Telefone, e-mail, ramal ou endereço",
        ).props("outlined")

        responsible = ui.input(
            "Responsável",
            value=item.responsible if item else "",
        ).props("outlined")

        service_hours = ui.input(
            "Horário de atendimento",
            value=item.service_hours if item else "",
            placeholder="Ex.: Segunda a sexta, 08h às 18h",
        ).props("outlined")

        status = ui.select(
            ["Ativo", "Inativo"],
            value=item.status if item else "Ativo",
            label="Status",
        ).props("outlined")

        notes = ui.textarea(
            "Observações",
            value=item.notes if item else "",
        ).props("outlined autogrow")

        for field in (
            operator,
            plan,
            code,
            department,
            purpose,
            contact_type,
            contact,
            responsible,
            service_hours,
            status,
            notes,
        ):
            field.classes("portal-admin-contacts-dialog-field")

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

        def save() -> None:
            try:
                save_contato(
                    record_id=item.record_id if item else None,
                    code=code.value or "",
                    operator_id=operator.value or "",
                    plan_id=plan.value or "",
                    department=department.value or "",
                    purpose=purpose.value or "",
                    contact_type=contact_type.value or "",
                    contact=contact.value or "",
                    responsible=responsible.value or "",
                    service_hours=service_hours.value or "",
                    notes=notes.value or "",
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
                "Contato salvo com sucesso.",
                type="positive",
                position="top",
            )
            dialog.close()
            ui.navigate.to("/administracao/contatos")

        with ui.row().classes(
            "portal-admin-contacts-dialog-actions"
        ):
            ui.button(
                "Cancelar",
                on_click=dialog.close,
            ).props("flat no-caps")

            ui.button(
                "Salvar contato",
                icon="check",
                on_click=save,
            ).props("unelevated no-caps").classes(
                "portal-admin-contacts-primary"
            )

    dialog.open()

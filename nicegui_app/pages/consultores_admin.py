from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.consultores_admin_service import (
    AdminCarteira,
    AdminConsultor,
    get_admin_carteiras,
    get_admin_consultores,
    get_consultant_reference_data,
    save_carteira,
    save_consultor,
)


def render_admin_consultores(user: dict) -> None:
    consultants = get_admin_consultores()
    wallets = get_admin_carteiras(consultants)
    operators, plans = get_consultant_reference_data()

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · CONSULTORES",
        page_title="Consultores e Carteiras",
        page_description=(
            "Mantenha os consultores e seus vínculos com operadoras e planos."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-consultants-back")

        with ui.element("section").classes("portal-admin-consultants-hero"):
            with ui.column().classes("portal-admin-consultants-hero-copy"):
                ui.label("RELACIONAMENTO").classes("portal-section-kicker")
                ui.label(
                    "Quem cuida de cada carteira, sempre visível."
                ).classes("portal-admin-consultants-hero-title")
                ui.label(
                    "Gerencie consultores e relacione cada profissional às "
                    "operadoras e planos sob sua responsabilidade."
                ).classes("portal-admin-consultants-hero-description")

            with ui.row().classes("portal-admin-consultants-stats"):
                for value, label in (
                    (len(consultants), "Consultores"),
                    (
                        sum(
                            1
                            for item in consultants
                            if item.status.lower() == "ativo"
                        ),
                        "Ativos",
                    ),
                    (
                        sum(
                            1
                            for item in wallets
                            if item.status.lower() == "ativo"
                        ),
                        "Carteiras",
                    ),
                ):
                    with ui.column().classes("portal-admin-consultants-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-admin-consultants-stat-value"
                        )
                        ui.label(label).classes(
                            "portal-admin-consultants-stat-label"
                        )

        with ui.tabs().classes("portal-admin-consultants-tabs") as tabs:
            consultants_tab = ui.tab("Consultores", icon="support_agent")
            wallets_tab = ui.tab("Carteiras", icon="account_tree")

        with ui.tab_panels(
            tabs,
            value=consultants_tab,
        ).classes("portal-admin-consultants-panels"):
            with ui.tab_panel(consultants_tab):
                _render_consultants_panel(
                    user,
                    consultants,
                    wallets,
                    operators,
                    plans,
                )

            with ui.tab_panel(wallets_tab):
                _render_wallets_panel(
                    user,
                    consultants,
                    wallets,
                    operators,
                    plans,
                )


def _render_consultants_panel(
    user: dict,
    consultants: list[AdminConsultor],
    wallets: list[AdminCarteira],
    operators: dict[str, str],
    plans: dict[str, tuple[str, str]],
) -> None:
    with ui.row().classes("portal-admin-consultants-toolbar"):
        search = ui.input(
            placeholder="Buscar consultor, cargo, e-mail ou telefone"
        ).props(
            "outlined dense clearable prepend-icon=search"
        ).classes("portal-admin-consultants-search")

        status_filter = ui.select(
            ["Todos", "Ativo", "Inativo"],
            value="Todos",
            label="Status",
        ).props("outlined dense").classes(
            "portal-admin-consultants-filter"
        )

        ui.button(
            "Novo consultor",
            icon="person_add",
            on_click=lambda: _open_consultant_dialog(user, None),
        ).props("unelevated no-caps").classes(
            "portal-admin-consultants-primary"
        )

    count = ui.label("").classes("portal-admin-consultants-count")
    container = ui.element("section").classes(
        "portal-admin-consultants-list"
    )

    def refresh() -> None:
        term = str(search.value or "").strip().lower()
        filtered: list[AdminConsultor] = []

        for item in consultants:
            text_ok = (
                not term
                or any(
                    term in value.lower()
                    for value in (
                        item.name,
                        item.job_title,
                        item.email,
                        item.phone,
                        item.code,
                    )
                )
            )
            status_ok = (
                status_filter.value == "Todos"
                or item.status == status_filter.value
            )
            if text_ok and status_ok:
                filtered.append(item)

        count.set_text(f"{len(filtered)} consultor(es)")
        container.clear()

        with container:
            if not filtered:
                with ui.element("div").classes(
                    "portal-admin-consultants-empty"
                ):
                    ui.icon("support_agent")
                    ui.label("Nenhum consultor encontrado.")
                return

            for item in filtered:
                wallet_count = sum(
                    1
                    for wallet in wallets
                    if wallet.consultant_id == item.record_id
                    and wallet.status.lower() == "ativo"
                )

                with ui.element("article").classes(
                    "portal-admin-consultants-row"
                ):
                    with ui.element("div").classes(
                        "portal-admin-consultants-icon"
                    ):
                        ui.icon("support_agent")

                    with ui.column().classes(
                        "portal-admin-consultants-copy"
                    ):
                        ui.label(item.name).classes(
                            "portal-admin-consultants-title"
                        )
                        ui.label(
                            item.job_title or "Consultor"
                        ).classes(
                            "portal-admin-consultants-role"
                        )

                        meta = " · ".join(
                            value
                            for value in (
                                item.email,
                                item.phone,
                            )
                            if value
                        )
                        if meta:
                            ui.label(meta).classes(
                                "portal-admin-consultants-meta"
                            )

                    with ui.element("div").classes(
                        "portal-admin-consultants-wallet-count"
                    ):
                        ui.icon("account_tree")
                        ui.label(
                            f"{wallet_count} carteira(s)"
                        )

                    with ui.element("div").classes(
                        "portal-admin-consultants-status "
                        + (
                            "is-active"
                            if item.status.lower() == "ativo"
                            else ""
                        )
                    ):
                        ui.element("span").classes(
                            "portal-admin-consultants-status-dot"
                        )
                        ui.label(item.status)

                    ui.button(
                        "Editar",
                        icon="edit",
                        on_click=lambda current=item: _open_consultant_dialog(
                            user,
                            current,
                        ),
                    ).props("flat no-caps").classes(
                        "portal-admin-consultants-edit"
                    )

    search.on_value_change(lambda _: refresh())
    status_filter.on_value_change(lambda _: refresh())
    refresh()


def _render_wallets_panel(
    user: dict,
    consultants: list[AdminConsultor],
    wallets: list[AdminCarteira],
    operators: dict[str, str],
    plans: dict[str, tuple[str, str]],
) -> None:
    consultant_options = {
        item.record_id: item.name
        for item in consultants
    }

    with ui.row().classes("portal-admin-consultants-toolbar"):
        search = ui.input(
            placeholder="Buscar consultor, operadora, plano ou papel"
        ).props(
            "outlined dense clearable prepend-icon=search"
        ).classes("portal-admin-consultants-search")

        operator_filter = ui.select(
            {"Todos": "Todas as operadoras", **operators},
            value="Todos",
            label="Operadora",
        ).props("outlined dense").classes(
            "portal-admin-consultants-filter"
        )

        ui.button(
            "Nova carteira",
            icon="add_link",
            on_click=lambda: _open_wallet_dialog(
                user,
                None,
                consultant_options,
                operators,
                plans,
            ),
        ).props("unelevated no-caps").classes(
            "portal-admin-consultants-primary"
        )

    count = ui.label("").classes("portal-admin-consultants-count")
    container = ui.element("section").classes(
        "portal-admin-consultants-list"
    )

    def refresh() -> None:
        term = str(search.value or "").strip().lower()
        filtered: list[AdminCarteira] = []

        for item in wallets:
            text_ok = (
                not term
                or any(
                    term in value.lower()
                    for value in (
                        item.consultant_name,
                        item.operator_name,
                        item.plan_name,
                        item.role,
                    )
                )
            )
            operator_ok = (
                operator_filter.value == "Todos"
                or item.operator_id == operator_filter.value
            )
            if text_ok and operator_ok:
                filtered.append(item)

        count.set_text(f"{len(filtered)} carteira(s)")
        container.clear()

        with container:
            if not filtered:
                with ui.element("div").classes(
                    "portal-admin-consultants-empty"
                ):
                    ui.icon("account_tree")
                    ui.label("Nenhuma carteira encontrada.")
                return

            for item in filtered:
                with ui.element("article").classes(
                    "portal-admin-consultants-row"
                ):
                    with ui.element("div").classes(
                        "portal-admin-consultants-icon"
                    ):
                        ui.icon("account_tree")

                    with ui.column().classes(
                        "portal-admin-consultants-copy"
                    ):
                        ui.label(item.consultant_name).classes(
                            "portal-admin-consultants-title"
                        )
                        ui.label(item.operator_name).classes(
                            "portal-admin-consultants-role"
                        )

                        meta = " · ".join(
                            value
                            for value in (
                                item.plan_name,
                                item.role,
                            )
                            if value
                        )
                        if meta:
                            ui.label(meta).classes(
                                "portal-admin-consultants-meta"
                            )

                    with ui.element("div").classes(
                        "portal-admin-consultants-status "
                        + (
                            "is-active"
                            if item.status.lower() == "ativo"
                            else ""
                        )
                    ):
                        ui.element("span").classes(
                            "portal-admin-consultants-status-dot"
                        )
                        ui.label(item.status)

                    ui.button(
                        "Editar",
                        icon="edit",
                        on_click=lambda current=item: _open_wallet_dialog(
                            user,
                            current,
                            consultant_options,
                            operators,
                            plans,
                        ),
                    ).props("flat no-caps").classes(
                        "portal-admin-consultants-edit"
                    )

    search.on_value_change(lambda _: refresh())
    operator_filter.on_value_change(lambda _: refresh())
    refresh()


def _open_consultant_dialog(
    user: dict,
    item: AdminConsultor | None,
) -> None:
    with ui.dialog() as dialog, ui.card().classes(
        "portal-admin-consultants-dialog"
    ):
        ui.label(
            "EDITAR CONSULTOR" if item else "NOVO CONSULTOR"
        ).classes("portal-section-kicker")
        ui.label(
            item.name if item else "Cadastrar consultor"
        ).classes("portal-admin-consultants-dialog-title")

        code = ui.input(
            "Código",
            value=item.code if item else "",
        ).props("outlined")

        name = ui.input(
            "Nome",
            value=item.name if item else "",
        ).props("outlined")

        job_title = ui.input(
            "Cargo",
            value=item.job_title if item else "",
        ).props("outlined")

        email = ui.input(
            "E-mail",
            value=item.email if item else "",
        ).props("outlined")

        phone = ui.input(
            "Telefone",
            value=item.phone if item else "",
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
            code,
            name,
            job_title,
            email,
            phone,
            status,
            notes,
        ):
            field.classes("portal-admin-consultants-dialog-field")

        def save() -> None:
            try:
                save_consultor(
                    record_id=item.record_id if item else None,
                    code=code.value or "",
                    name=name.value or "",
                    job_title=job_title.value or "",
                    email=email.value or "",
                    phone=phone.value or "",
                    notes=notes.value or "",
                    status=status.value or "",
                    actor=user,
                )
            except Exception as error:
                ui.notify(str(error), type="negative", position="top")
                return

            ui.notify(
                "Consultor salvo com sucesso.",
                type="positive",
                position="top",
            )
            dialog.close()
            ui.navigate.to("/administracao/consultores")

        with ui.row().classes(
            "portal-admin-consultants-dialog-actions"
        ):
            ui.button(
                "Cancelar",
                on_click=dialog.close,
            ).props("flat no-caps")
            ui.button(
                "Salvar consultor",
                icon="check",
                on_click=save,
            ).props("unelevated no-caps").classes(
                "portal-admin-consultants-primary"
            )

    dialog.open()


def _open_wallet_dialog(
    user: dict,
    item: AdminCarteira | None,
    consultants: dict[str, str],
    operators: dict[str, str],
    plans: dict[str, tuple[str, str]],
) -> None:
    with ui.dialog() as dialog, ui.card().classes(
        "portal-admin-consultants-dialog"
    ):
        ui.label(
            "EDITAR CARTEIRA" if item else "NOVA CARTEIRA"
        ).classes("portal-section-kicker")
        ui.label(
            item.consultant_name if item else "Vincular consultor"
        ).classes("portal-admin-consultants-dialog-title")

        consultant = ui.select(
            consultants,
            value=item.consultant_id if item else None,
            label="Consultor",
        ).props("outlined")

        operator = ui.select(
            operators,
            value=item.operator_id if item else None,
            label="Operadora",
        ).props("outlined")

        selected_operator_id = item.operator_id if item else ""
        initial_plan_options = {"": "Todos os planos / não específico"}
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

        role = ui.input(
            "Papel / responsabilidade",
            value=item.role if item else "",
            placeholder="Ex.: Consultor comercial responsável",
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
            consultant,
            operator,
            plan,
            role,
            status,
            notes,
        ):
            field.classes("portal-admin-consultants-dialog-field")

        def refresh_plans() -> None:
            selected_operator = str(operator.value or "")
            options = {"": "Todos os planos / não específico"}
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
                save_carteira(
                    record_id=item.record_id if item else None,
                    consultant_id=consultant.value or "",
                    operator_id=operator.value or "",
                    plan_id=plan.value or "",
                    role=role.value or "",
                    notes=notes.value or "",
                    status=status.value or "",
                    actor=user,
                )
            except Exception as error:
                ui.notify(str(error), type="negative", position="top")
                return

            ui.notify(
                "Carteira salva com sucesso.",
                type="positive",
                position="top",
            )
            dialog.close()
            ui.navigate.to("/administracao/consultores")

        with ui.row().classes(
            "portal-admin-consultants-dialog-actions"
        ):
            ui.button(
                "Cancelar",
                on_click=dialog.close,
            ).props("flat no-caps")
            ui.button(
                "Salvar carteira",
                icon="check",
                on_click=save,
            ).props("unelevated no-caps").classes(
                "portal-admin-consultants-primary"
            )

    dialog.open()

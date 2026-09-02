from __future__ import annotations
from nicegui import ui
from nicegui_app.layout import portal_layout
from nicegui_app.services.portais_admin_service import (
    AdminPortal, get_admin_portais, get_portal_reference_data, save_portal,
)

def render_admin_portais(user: dict) -> None:
    portais = get_admin_portais()
    operators, plans, locations = get_portal_reference_data()

    with portal_layout(
        user=user, active="admin",
        page_eyebrow="ADMINISTRAÇÃO · PORTAIS",
        page_title="Gestão de Portais",
        page_description="Cadastre e mantenha os portais externos, vínculos e orientações de acesso.",
    ):
        ui.button("Voltar à Administração", icon="arrow_back",
                  on_click=lambda: ui.navigate.to("/administracao")).props(
            "flat no-caps").classes("portal-admin-portals-back")

        with ui.element("section").classes("portal-admin-portals-hero"):
            with ui.column().classes("portal-admin-portals-hero-copy"):
                ui.label("ACESSOS EXTERNOS").classes("portal-section-kicker")
                ui.label("Onde a operação encontra cada convênio.").classes("portal-admin-portals-hero-title")
                ui.label(
                    "Gerencie endereço, tipo, operadora, plano, local e orientações. "
                    "As senhas continuam fora desta tela e terão gestão protegida própria."
                ).classes("portal-admin-portals-hero-description")
            with ui.row().classes("portal-admin-portals-stats"):
                for value, label in (
                    (len(portais), "Portais"),
                    (sum(1 for p in portais if p.requires_login), "Com login"),
                    (sum(1 for p in portais if p.status.lower() == "ativo"), "Ativos"),
                ):
                    with ui.column().classes("portal-admin-portals-stat"):
                        ui.label(str(value).zfill(2)).classes("portal-admin-portals-stat-value")
                        ui.label(label).classes("portal-admin-portals-stat-label")

        with ui.row().classes("portal-admin-portals-toolbar"):
            search = ui.input(placeholder="Buscar portal, operadora ou tipo").props(
                "outlined dense clearable prepend-icon=search").classes("portal-admin-portals-search")
            operator_filter = ui.select(
                {"Todos": "Todas as operadoras", **operators},
                value="Todos", label="Operadora").props("outlined dense").classes("portal-admin-portals-filter")
            login_filter = ui.select(
                ["Todos", "Exige login", "Sem login"],
                value="Todos", label="Acesso").props("outlined dense").classes("portal-admin-portals-filter")
            ui.button("Novo portal", icon="add",
                      on_click=lambda: _open_dialog(user, None, operators, plans, locations)).props(
                "unelevated no-caps").classes("portal-admin-portals-primary")

        count = ui.label("").classes("portal-admin-portals-count")
        container = ui.element("section").classes("portal-admin-portals-list")

        def refresh() -> None:
            term = str(search.value or "").strip().lower()
            filtered = []
            for item in portais:
                text_ok = not term or any(term in value.lower() for value in (
                    item.name, item.operator_name, item.portal_type, item.code, item.plan_name
                ))
                operator_ok = operator_filter.value == "Todos" or item.operator_id == operator_filter.value
                login_ok = (
                    login_filter.value == "Todos"
                    or (login_filter.value == "Exige login" and item.requires_login)
                    or (login_filter.value == "Sem login" and not item.requires_login)
                )
                if text_ok and operator_ok and login_ok:
                    filtered.append(item)

            count.set_text(f"{len(filtered)} portal(is)")
            container.clear()
            with container:
                if not filtered:
                    with ui.element("div").classes("portal-admin-portals-empty"):
                        ui.icon("language")
                        ui.label("Nenhum portal encontrado.")
                    return
                for item in filtered:
                    with ui.element("article").classes("portal-admin-portals-row"):
                        with ui.element("div").classes("portal-admin-portals-icon"):
                            ui.icon("vpn_key" if item.requires_login else "language")
                        with ui.column().classes("portal-admin-portals-copy"):
                            ui.label(item.name).classes("portal-admin-portals-title")
                            ui.label(item.operator_name).classes("portal-admin-portals-operator")
                            meta = " · ".join(v for v in (item.portal_type, item.plan_name, item.location_name) if v)
                            if meta:
                                ui.label(meta).classes("portal-admin-portals-meta")
                        with ui.element("div").classes(
                            f"portal-admin-portals-access {'requires-login' if item.requires_login else ''}"
                        ):
                            ui.icon("lock" if item.requires_login else "lock_open")
                            ui.label("Login" if item.requires_login else "Livre")
                        with ui.element("div").classes(
                            f"portal-admin-portals-status {'is-active' if item.status.lower() == 'ativo' else ''}"
                        ):
                            ui.element("span").classes("portal-admin-portals-status-dot")
                            ui.label(item.status)
                        ui.button("Editar", icon="edit",
                                  on_click=lambda current=item: _open_dialog(
                                      user, current, operators, plans, locations
                                  )).props("flat no-caps").classes("portal-admin-portals-edit")

        search.on_value_change(lambda _: refresh())
        operator_filter.on_value_change(lambda _: refresh())
        login_filter.on_value_change(lambda _: refresh())
        refresh()

def _open_dialog(user: dict, item: AdminPortal | None, operators: dict[str, str],
                 plans: dict[str, tuple[str, str]], locations: dict[str, str]) -> None:
    with ui.dialog() as dialog, ui.card().classes("portal-admin-portals-dialog"):
        ui.label("EDITAR PORTAL" if item else "NOVO PORTAL").classes("portal-section-kicker")
        ui.label(item.name if item else "Cadastrar portal").classes("portal-admin-portals-dialog-title")

        operator = ui.select(operators, value=item.operator_id if item else None,
                             label="Operadora").props("outlined")
        plan_options = {"": "Sem plano específico"}
        location_options = {"": "Todos / não específico", **locations}
        plan = ui.select(plan_options, value=item.plan_id if item else "", label="Plano").props("outlined")
        location = ui.select(location_options, value=item.location_id if item else "", label="Local").props("outlined")
        code = ui.input("Código", value=item.code if item else "").props("outlined")
        name = ui.input("Nome do portal", value=item.name if item else "").props("outlined")
        portal_type = ui.input("Tipo", value=item.portal_type if item else "").props("outlined")
        url = ui.input("URL", value=item.url if item else "").props("outlined")
        requires_login = ui.switch("Exige login", value=item.requires_login if item else False)
        status = ui.select(["Ativo", "Inativo"], value=item.status if item else "Ativo",
                           label="Status").props("outlined")
        instruction = ui.textarea("Instrução de acesso",
                                  value=item.access_instruction if item else "").props("outlined autogrow")
        tip = ui.textarea("Dica geral de acesso",
                          value=item.general_tip if item else "").props("outlined autogrow")
        notes = ui.textarea("Observações", value=item.notes if item else "").props("outlined autogrow")

        fields = (operator, plan, location, code, name, portal_type, url, status, instruction, tip, notes)
        for field in fields:
            field.classes("portal-admin-portals-dialog-field")
        requires_login.classes("portal-admin-portals-dialog-switch")

        def refresh_plans() -> None:
            selected = str(operator.value or "")
            options = {"": "Sem plano específico"}
            options.update({
                pid: pname for pid, (oid, pname) in plans.items()
                if not oid or oid == selected
            })
            current = str(plan.value or "")
            plan.set_options(options, value=current if current in options else "")

        operator.on_value_change(lambda _: refresh_plans())
        refresh_plans()

        def save() -> None:
            try:
                save_portal(
                    record_id=item.record_id if item else None,
                    code=code.value or "", operator_id=operator.value or "",
                    plan_id=plan.value or "", location_id=location.value or "",
                    name=name.value or "", portal_type=portal_type.value or "",
                    url=url.value or "", requires_login=bool(requires_login.value),
                    access_instruction=instruction.value or "", general_tip=tip.value or "",
                    notes=notes.value or "", status=status.value or "", actor=user,
                )
            except Exception as error:
                ui.notify(str(error), type="negative", position="top")
                return
            ui.notify("Portal salvo com sucesso.", type="positive", position="top")
            dialog.close()
            ui.navigate.to("/administracao/portais")

        with ui.row().classes("portal-admin-portals-dialog-actions"):
            ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
            ui.button("Salvar portal", icon="check", on_click=save).props(
                "unelevated no-caps").classes("portal-admin-portals-primary")
    dialog.open()

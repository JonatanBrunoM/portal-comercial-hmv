from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.usuarios_admin_service import (
    ManagedProfile,
    get_managed_profiles,
    save_profile_access,
)


def _initials(name: str) -> str:
    parts = [part for part in name.split() if part]
    if not parts:
        return "HM"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def render_admin_usuarios(user: dict) -> None:
    profiles = get_managed_profiles()

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · ACESSOS",
        page_title="Usuários e Permissões",
        page_description=(
            "Gerencie quem acessa o Portal Comercial e quais usuários possuem "
            "permissão administrativa."
        ),
    ):
        with ui.row().classes("portal-admin-users-back-row"):
            ui.button(
                "Voltar à Administração",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/administracao"),
            ).props("flat no-caps").classes("portal-admin-users-back")

        with ui.element("section").classes("portal-admin-users-summary"):
            with ui.column().classes("portal-admin-users-summary-copy"):
                ui.label("CONTROLE DE ACESSO").classes("portal-section-kicker")
                ui.label("Permissões simples e rastreáveis.").classes(
                    "portal-admin-users-summary-title"
                )
                ui.label(
                    "Usuários são criados automaticamente no primeiro login institucional. "
                    "Aqui o administrador controla apenas função e status."
                ).classes("portal-admin-users-summary-description")

            with ui.row().classes("portal-admin-users-summary-stats"):
                for value, label in (
                    (len(profiles), "Usuários"),
                    (sum(1 for p in profiles if p.status.lower() == "ativo"), "Ativos"),
                    (sum(1 for p in profiles if p.role.lower() == "admin"), "Admins"),
                ):
                    with ui.column().classes("portal-admin-users-summary-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-admin-users-summary-value"
                        )
                        ui.label(label).classes("portal-admin-users-summary-label")

        with ui.row().classes("portal-admin-users-toolbar"):
            search = ui.input(
                placeholder="Buscar por nome ou e-mail"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-admin-users-search"
            )
            role_filter = ui.select(
                ["Todos", "Administrador", "Usuário"],
                value="Todos",
                label="Perfil",
            ).props("outlined dense").classes("portal-admin-users-filter")
            status_filter = ui.select(
                ["Todos", "Ativo", "Inativo"],
                value="Todos",
                label="Status",
            ).props("outlined dense").classes("portal-admin-users-filter")

        count = ui.label("").classes("portal-admin-users-count")
        table_container = ui.element("section").classes("portal-admin-users-table")

        def open_editor(profile: ManagedProfile) -> None:
            current_actor_id = str(user.get("id") or "")
            current_actor_email = str(user.get("email") or "").lower()
            is_self = (
                (current_actor_id and current_actor_id == profile.profile_id)
                or (current_actor_email and current_actor_email == profile.email.lower())
            )

            with ui.dialog() as dialog, ui.card().classes("portal-admin-user-dialog"):
                with ui.row().classes("portal-admin-user-dialog-head"):
                    with ui.element("div").classes("portal-admin-user-dialog-avatar"):
                        ui.label(_initials(profile.name))
                    with ui.column().classes("portal-admin-user-dialog-copy"):
                        ui.label("EDITAR ACESSO").classes("portal-section-kicker")
                        ui.label(profile.name).classes("portal-admin-user-dialog-title")
                        ui.label(profile.email).classes("portal-admin-user-dialog-email")

                role = ui.select(
                    {
                        "usuario": "Usuário",
                        "admin": "Administrador",
                    },
                    value=profile.role.lower() if profile.role.lower() in {"usuario", "admin"} else "usuario",
                    label="Perfil de acesso",
                ).props("outlined").classes("portal-admin-user-dialog-field")

                status = ui.select(
                    ["Ativo", "Inativo"],
                    value=profile.status if profile.status in {"Ativo", "Inativo"} else "Ativo",
                    label="Status",
                ).props("outlined").classes("portal-admin-user-dialog-field")

                if is_self:
                    ui.label(
                        "Por segurança, seu próprio usuário deve permanecer Administrador e Ativo."
                    ).classes("portal-admin-user-self-warning")

                feedback = ui.label("").classes("portal-admin-user-dialog-feedback")

                def save() -> None:
                    feedback.set_text("")
                    try:
                        save_profile_access(
                            profile_id=profile.profile_id,
                            role=role.value,
                            status=status.value,
                            actor=user,
                        )
                    except Exception as error:
                        feedback.set_text(str(error))
                        ui.notify(
                            str(error),
                            type="negative",
                            position="top",
                        )
                        return

                    ui.notify(
                        "Permissões atualizadas com sucesso.",
                        type="positive",
                        position="top",
                    )
                    dialog.close()
                    ui.navigate.to("/administracao/usuarios")

                with ui.row().classes("portal-admin-user-dialog-actions"):
                    ui.button(
                        "Cancelar",
                        on_click=dialog.close,
                    ).props("flat no-caps").classes("portal-admin-user-dialog-cancel")
                    ui.button(
                        "Salvar alterações",
                        icon="check",
                        on_click=save,
                    ).props("unelevated no-caps").classes("portal-admin-user-dialog-save")

            dialog.open()

        def render_rows(filtered: list[ManagedProfile]) -> None:
            table_container.clear()

            with table_container:
                if not filtered:
                    with ui.element("div").classes("portal-admin-users-empty"):
                        ui.icon("person_search")
                        ui.label("Nenhum usuário encontrado.").classes(
                            "portal-admin-users-empty-title"
                        )
                        ui.label(
                            "Revise a pesquisa ou os filtros selecionados."
                        ).classes("portal-admin-users-empty-description")
                    return

                with ui.element("div").classes("portal-admin-users-table-head"):
                    ui.label("USUÁRIO")
                    ui.label("PERFIL")
                    ui.label("STATUS")
                    ui.label("ÚLTIMO LOGIN")
                    ui.label("")

                for profile in filtered:
                    with ui.element("div").classes("portal-admin-users-row"):
                        with ui.row().classes("portal-admin-users-identity"):
                            with ui.element("div").classes("portal-admin-users-avatar"):
                                ui.label(_initials(profile.name))
                            with ui.column().classes("portal-admin-users-identity-copy"):
                                ui.label(profile.name).classes("portal-admin-users-name")
                                ui.label(profile.email).classes("portal-admin-users-email")

                        role_label = (
                            "Administrador"
                            if profile.role.lower() == "admin"
                            else "Usuário"
                        )
                        with ui.element("div").classes(
                            f"portal-admin-users-role {'is-admin' if profile.role.lower() == 'admin' else ''}"
                        ):
                            ui.label(role_label)

                        with ui.element("div").classes(
                            f"portal-admin-users-status {'is-active' if profile.status.lower() == 'ativo' else ''}"
                        ):
                            ui.element("span").classes("portal-admin-users-status-dot")
                            ui.label(profile.status)

                        ui.label(profile.last_login).classes(
                            "portal-admin-users-last-login"
                        )

                        ui.button(
                            "Editar",
                            icon="edit",
                            on_click=lambda p=profile: open_editor(p),
                        ).props("flat no-caps").classes("portal-admin-users-edit")

        def refresh() -> None:
            term = str(search.value or "").strip().lower()
            role_value = role_filter.value
            status_value = status_filter.value

            filtered: list[ManagedProfile] = []
            for profile in profiles:
                role_label = (
                    "Administrador"
                    if profile.role.lower() == "admin"
                    else "Usuário"
                )
                text_ok = (
                    not term
                    or term in profile.name.lower()
                    or term in profile.email.lower()
                )
                role_ok = role_value == "Todos" or role_label == role_value
                status_ok = status_value == "Todos" or profile.status == status_value

                if text_ok and role_ok and status_ok:
                    filtered.append(profile)

            count.set_text(f"{len(filtered)} usuário(s) encontrado(s)")
            render_rows(filtered)

        search.on_value_change(lambda _: refresh())
        role_filter.on_value_change(lambda _: refresh())
        status_filter.on_value_change(lambda _: refresh())
        refresh()

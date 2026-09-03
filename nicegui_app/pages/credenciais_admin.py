from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.credenciais_service import (
    CredentialPreview,
    get_admin_credentials,
    get_admin_history,
    save_credential,
)
from nicegui_app.services.portais_admin_service import get_admin_portais


def render_admin_credenciais(user: dict) -> None:
    portals = get_admin_portais()
    portal_options = {
        portal.record_id: f"{portal.operator_name} · {portal.name}"
        for portal in portals
        if portal.requires_login
    }

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · CREDENCIAIS",
        page_title="Credenciais protegidas",
        page_description=(
            "Gerencie logins e senhas dos portais. Senhas são armazenadas criptografadas "
            "e o histórico fica restrito à Administração."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-credentials-back")

        if not portal_options:
            ui.label("Nenhum portal marcado como 'Exige login'.").classes(
                "portal-admin-credentials-empty"
            )
            return

        portal_select = ui.select(
            portal_options,
            value=next(iter(portal_options)),
            label="Portal",
        ).props("outlined").classes("portal-admin-credentials-select")

        toolbar = ui.row().classes("portal-admin-credentials-toolbar")
        content = ui.column().classes("portal-admin-credentials-list")

        def refresh() -> None:
            content.clear()
            portal_id = str(portal_select.value or "")
            items = get_admin_credentials(portal_id, user)

            with toolbar:
                toolbar.clear()
                ui.button(
                    "Nova credencial",
                    icon="add",
                    on_click=lambda: open_editor(None),
                ).props("unelevated no-caps").classes("portal-admin-credentials-primary")

            with content:
                if not items:
                    ui.label("Nenhuma credencial cadastrada para este portal.").classes(
                        "portal-admin-credentials-empty"
                    )
                    return

                for item in items:
                    with ui.element("article").classes("portal-admin-credential-card"):
                        with ui.column().classes("portal-admin-credential-main"):
                            ui.label(item.identification).classes("portal-admin-credential-title")
                            ui.label(item.login).classes("portal-admin-credential-login")
                            ui.label(
                                f"Status: {item.status} · Senhas bloqueadas: {item.blocked_passwords}"
                            ).classes("portal-admin-credential-meta")
                        with ui.row().classes("portal-admin-credential-actions"):
                            ui.button(
                                "Histórico",
                                icon="history",
                                on_click=lambda current=item: open_history(current),
                            ).props("flat no-caps")
                            ui.button(
                                "Editar",
                                icon="edit",
                                on_click=lambda current=item: open_editor(current),
                            ).props("flat no-caps")

        def open_history(item: CredentialPreview) -> None:
            rows = get_admin_history(item.credential_id, user)
            with ui.dialog() as dialog, ui.card().classes("portal-admin-credentials-dialog"):
                ui.label("HISTÓRICO PROTEGIDO").classes("portal-section-kicker")
                ui.label(item.identification).classes("portal-admin-credentials-dialog-title")
                ui.label(
                    "O histórico mantém versões criptografadas. Senhas anteriores não são exibidas nesta tela."
                ).classes("portal-admin-credentials-help")
                if not rows:
                    ui.label("Nenhuma troca de senha registrada.")
                else:
                    for row in rows:
                        with ui.element("div").classes("portal-admin-history-row"):
                            ui.label(str(row.get("alterado_em") or "Data não informada")).classes(
                                "portal-admin-history-date"
                            )
                            ui.label(str(row.get("login") or "Login não informado")).classes(
                                "portal-admin-history-login"
                            )
                            if row.get("motivo_alteracao"):
                                ui.label(str(row["motivo_alteracao"])).classes(
                                    "portal-admin-history-reason"
                                )
                ui.button("Fechar", on_click=dialog.close).props("flat no-caps")
            dialog.open()

        def open_editor(item: CredentialPreview | None) -> None:
            with ui.dialog() as dialog, ui.card().classes("portal-admin-credentials-dialog"):
                ui.label("EDITAR CREDENCIAL" if item else "NOVA CREDENCIAL").classes(
                    "portal-section-kicker"
                )
                ui.label(
                    item.identification if item else "Cadastrar acesso"
                ).classes("portal-admin-credentials-dialog-title")

                identification = ui.input(
                    "Identificação",
                    value=item.identification if item else "Acesso principal",
                ).props("outlined")
                login = ui.input("Login", value=item.login if item else "").props("outlined")
                password = ui.input(
                    "Nova senha" if item else "Senha",
                    password=True,
                    password_toggle_button=True,
                ).props("outlined")
                if item:
                    ui.label(
                        "Deixe a nova senha em branco para manter a senha atual."
                    ).classes("portal-admin-credentials-help")
                access_tip = ui.textarea(
                    "Dica de acesso",
                    value=item.access_tip if item else "",
                ).props("outlined autogrow")
                notes = ui.textarea(
                    "Observações",
                    value=item.notes if item else "",
                ).props("outlined autogrow")
                password_rule = ui.textarea(
                    "Regra/observação de senha",
                    value=item.password_rule if item else "",
                ).props("outlined autogrow")
                blocked = ui.number(
                    "Quantidade de senhas bloqueadas",
                    value=item.blocked_passwords if item else 0,
                    min=0,
                    precision=0,
                ).props("outlined")
                status = ui.select(
                    ["Ativo", "Inativo"],
                    value=item.status if item else "Ativo",
                    label="Status",
                ).props("outlined")
                reason = ui.input(
                    "Motivo da troca de senha",
                    value="",
                ).props("outlined")
                if item:
                    ui.label(
                        "Se informar uma nova senha, o motivo passa a ser obrigatório. "
                        "A senha também será comparada com a atual e com todo o histórico "
                        "antes de qualquer alteração."
                    ).classes("portal-admin-credentials-help")

                def save() -> None:
                    try:
                        save_credential(
                            credential_id=item.credential_id if item else None,
                            portal_id=str(portal_select.value or ""),
                            identification=identification.value or "",
                            login=login.value or "",
                            password=password.value or "",
                            access_tip=access_tip.value or "",
                            notes=notes.value or "",
                            status=status.value or "",
                            blocked_passwords=int(blocked.value or 0),
                            password_rule=password_rule.value or "",
                            change_reason=reason.value or "",
                            actor=user,
                        )
                    except Exception as error:
                        ui.notify(str(error), type="negative", position="top")
                        return
                    ui.notify("Credencial salva com segurança.", type="positive", position="top")
                    dialog.close()
                    refresh()

                with ui.row().classes("portal-admin-credentials-dialog-actions"):
                    ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
                    ui.button(
                        "Salvar credencial",
                        icon="shield",
                        on_click=save,
                    ).props("unelevated no-caps").classes("portal-admin-credentials-primary")
            dialog.open()

        portal_select.on_value_change(lambda _: refresh())
        refresh()

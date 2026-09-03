from __future__ import annotations

from urllib.parse import urlparse

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.portais_service import (
    PortalPreview,
    get_portal_detail,
    get_portais_preview,
)
from nicegui_app.services.credenciais_service import (
    format_credential_datetime,
    get_public_credentials,
    password_policy_label,
    reveal_password,
)


def _normalized(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _safe_url(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return None


def _is_active(status: str) -> bool:
    return _normalized(status) == "ativo"


def _portal_card(portal: PortalPreview) -> None:
    with ui.element("article").classes("portal-system-card"):
        with ui.row().classes("portal-system-card-top"):
            with ui.element("div").classes("portal-system-card-icon"):
                ui.icon("vpn_key")
            with ui.element("div").classes(
                "portal-system-status is-active"
                if _is_active(portal.status)
                else "portal-system-status"
            ):
                ui.element("span").classes("portal-system-status-dot")
                ui.label(portal.status)

        ui.label(portal.name).classes("portal-system-card-title")
        ui.label(portal.operator_name).classes("portal-system-card-operator")

        meta = " · ".join(
            value for value in (
                portal.portal_type,
                portal.local_name,
                portal.plan_name,
            )
            if value
        )
        if meta:
            ui.label(meta).classes("portal-system-card-meta")

        if portal.requires_login:
            with ui.row().classes("portal-system-login-badge"):
                ui.icon("lock")
                ui.label("Exige autenticação")

        ui.label(
            portal.general_tip
            or portal.instruction
            or "Acesse o portal para consultar orientações e informações disponíveis."
        ).classes("portal-system-card-description")

        with ui.row().classes("portal-system-card-actions"):
            ui.button(
                "Ver detalhes",
                icon="arrow_forward",
                on_click=lambda pid=portal.portal_id: ui.navigate.to(
                    f"/portais/{pid}"
                ),
            ).props("flat no-caps").classes("portal-system-detail-button")

            external = _safe_url(portal.url)
            if external:
                ui.link(
                    "Abrir portal",
                    target=external,
                    new_tab=True,
                ).classes("portal-system-external-link")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-systems-empty"):
        ui.icon("vpn_key_off")
        ui.label(title).classes("portal-systems-empty-title")
        ui.label(description).classes("portal-systems-empty-description")


def render_portais(user: dict) -> None:
    portals = get_portais_preview()

    with portal_layout(
        user=user,
        active="portals",
        page_eyebrow="CENTRAL DE PORTAIS",
        page_title="Acesse os sistemas utilizados pela operação.",
        page_description=(
            "Encontre portais de operadoras, instruções de acesso, "
            "links e informações relacionadas."
        ),
    ):
        operators = sorted(
            {portal.operator_name for portal in portals if portal.operator_name}
        )

        with ui.element("section").classes("portal-systems-summary"):
            with ui.column().classes("portal-systems-summary-copy"):
                ui.label("BASE DE ACESSOS").classes("portal-section-kicker")
                ui.label(f"{len(portals):02d} portais cadastrados").classes(
                    "portal-systems-summary-value"
                )
                ui.label(
                    "Concentrando os acessos externos usados pela operação."
                ).classes("portal-systems-summary-description")

            with ui.row().classes("portal-systems-summary-stats"):
                with ui.column().classes("portal-systems-mini-stat"):
                    ui.label(
                        str(sum(1 for p in portals if p.requires_login)).zfill(2)
                    ).classes("portal-systems-mini-value")
                    ui.label("Com login").classes("portal-systems-mini-label")
                with ui.column().classes("portal-systems-mini-stat"):
                    ui.label(
                        str(sum(1 for p in portals if _is_active(p.status))).zfill(2)
                    ).classes("portal-systems-mini-value")
                    ui.label("Ativos").classes("portal-systems-mini-label")

        with ui.element("section").classes("portal-systems-toolbar"):
            search = ui.input(
                placeholder="Buscar portal, operadora, tipo ou plano"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-systems-search"
            )

            operator = ui.select(
                options=["Todas"] + operators,
                value="Todas",
                label="Operadora",
            ).props("outlined dense").classes("portal-systems-filter")

            auth_filter = ui.select(
                options=["Todos", "Exige login", "Sem login"],
                value="Todos",
                label="Acesso",
            ).props("outlined dense").classes("portal-systems-filter")

        result_label = ui.label("").classes("portal-systems-result-label")
        cards = ui.element("div").classes("portal-systems-grid")

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_operator = operator.value or "Todas"
            selected_auth = auth_filter.value or "Todos"

            filtered: list[PortalPreview] = []

            for portal in portals:
                haystack = _normalized(
                    " ".join(
                        (
                            portal.name,
                            portal.operator_name,
                            portal.portal_type,
                            portal.plan_name,
                            portal.local_name,
                            portal.code,
                        )
                    )
                )

                operator_ok = (
                    selected_operator == "Todas"
                    or portal.operator_name == selected_operator
                )

                if selected_auth == "Exige login":
                    auth_ok = portal.requires_login
                elif selected_auth == "Sem login":
                    auth_ok = not portal.requires_login
                else:
                    auth_ok = True

                if (not term or term in haystack) and operator_ok and auth_ok:
                    filtered.append(portal)

            result_label.set_text(f"{len(filtered)} portal(is) encontrado(s)")
            cards.clear()

            with cards:
                if not filtered:
                    _empty(
                        "Nenhum portal encontrado.",
                        "Revise a pesquisa ou altere os filtros.",
                    )
                    return

                for portal in filtered:
                    _portal_card(portal)

        search.on_value_change(lambda _: refresh())
        operator.on_value_change(lambda _: refresh())
        auth_filter.on_value_change(lambda _: refresh())
        refresh()


def _detail_item(icon: str, label: str, value: str) -> None:
    if not value:
        return
    with ui.element("div").classes("portal-system-detail-item"):
        ui.icon(icon)
        with ui.column().classes("portal-system-detail-item-copy"):
            ui.label(label).classes("portal-system-detail-label")
            ui.label(value).classes("portal-system-detail-value")


def render_portal_detail(user: dict, portal_id: str) -> None:
    portal = get_portal_detail(portal_id)

    with portal_layout(
        user=user,
        active="portals",
    ):
        if portal is None:
            _empty(
                "Portal não encontrado.",
                "O registro pode ter sido removido ou o endereço está incorreto.",
            )
            return

        ui.button(
            "Voltar para Portais",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/portais"),
        ).props("flat no-caps").classes("portal-system-back-button")

        with ui.element("section").classes("portal-system-detail-hero"):
            with ui.element("div").classes("portal-system-detail-icon"):
                ui.icon("vpn_key")

            with ui.column().classes("portal-system-detail-copy"):
                ui.label("FICHA DO PORTAL").classes("portal-section-kicker")
                ui.label(portal.name).classes("portal-system-detail-title")
                ui.label(portal.operator_name).classes(
                    "portal-system-detail-operator"
                )

                if portal.general_tip:
                    ui.label(portal.general_tip).classes(
                        "portal-system-detail-tip"
                    )

            external = _safe_url(portal.url)
            if external:
                ui.link(
                    "Abrir portal",
                    target=external,
                    new_tab=True,
                ).classes("portal-system-open-link")

        with ui.element("section").classes("portal-system-detail-grid"):
            _detail_item("business", "Operadora", portal.operator_name)
            _detail_item("category", "Tipo", portal.portal_type or "Não informado")
            _detail_item("place", "Local", portal.local_name)
            _detail_item("view_list", "Plano", portal.plan_name)
            _detail_item(
                "lock",
                "Autenticação",
                "Exige login" if portal.requires_login else "Não exige login",
            )
            _detail_item("fact_check", "Status", portal.status)
            _detail_item("tag", "Código", portal.code)

        if portal.instruction:
            with ui.element("section").classes("portal-system-guidance-card"):
                with ui.row().classes("portal-system-guidance-head"):
                    ui.icon("route")
                    ui.label("Como acessar").classes(
                        "portal-system-guidance-title"
                    )
                ui.label(portal.instruction).classes(
                    "portal-system-guidance-text"
                )

        if portal.observations:
            with ui.element("section").classes("portal-system-guidance-card"):
                with ui.row().classes("portal-system-guidance-head"):
                    ui.icon("info")
                    ui.label("Observações").classes(
                        "portal-system-guidance-title"
                    )
                ui.label(portal.observations).classes(
                    "portal-system-guidance-text"
                )

        if portal.requires_login:
            credentials = get_public_credentials(portal.portal_id)

            with ui.element("section").classes("portal-system-credentials-panel"):
                with ui.row().classes("portal-system-credentials-head"):
                    with ui.element("div").classes("portal-system-credentials-icon"):
                        ui.icon("shield_lock")
                    with ui.column().classes("portal-system-credentials-copy"):
                        ui.label("Credenciais de acesso").classes("portal-system-credentials-title")
                        ui.label(
                            "A senha permanece protegida e só é descriptografada no servidor "
                            "quando você solicita revelar ou copiar."
                        ).classes("portal-system-credentials-description")

                if not credentials:
                    ui.label(
                        "Nenhuma credencial ativa está cadastrada para este portal."
                    ).classes("portal-system-credentials-empty")
                else:
                    with ui.column().classes("portal-system-credentials-list"):
                        for credential in credentials:
                            with ui.element("article").classes("portal-system-credential-card"):
                                with ui.row().classes("portal-system-credential-card-head"):
                                    with ui.column().classes("portal-system-credential-heading"):
                                        ui.label(credential.identification).classes(
                                            "portal-system-credential-name"
                                        )
                                        ui.label(
                                            f"Senha atualizada: "
                                            f"{format_credential_datetime(credential.password_changed_at)}"
                                        ).classes("portal-system-credential-updated")

                                    with ui.element("div").classes(
                                        "portal-system-credential-secure-badge"
                                    ):
                                        ui.icon("verified_user")
                                        ui.label("Acesso protegido")

                                with ui.element("div").classes(
                                    "portal-system-credential-access-box"
                                ):
                                    with ui.row().classes("portal-system-credential-field"):
                                        with ui.column().classes(
                                            "portal-system-credential-field-copy"
                                        ):
                                            ui.label("Login").classes(
                                                "portal-system-credential-label"
                                            )
                                            ui.label(credential.login).classes(
                                                "portal-system-credential-value"
                                            )

                                        async def copy_login(
                                            login=credential.login,
                                        ) -> None:
                                            import json

                                            try:
                                                await ui.run_javascript(
                                                    "navigator.clipboard.writeText("
                                                    f"{json.dumps(login)})"
                                                )
                                                ui.notify(
                                                    "Login copiado.",
                                                    type="positive",
                                                    position="top",
                                                )
                                            except Exception:
                                                ui.notify(
                                                    "Não foi possível copiar o login.",
                                                    type="negative",
                                                    position="top",
                                                )

                                        ui.button(
                                            icon="content_copy",
                                            on_click=copy_login,
                                        ).props(
                                            "flat round dense"
                                        ).classes(
                                            "portal-system-credential-icon-action"
                                        ).tooltip("Copiar login")

                                    password_value = ui.label(
                                        "••••••••••••"
                                    ).classes("portal-system-credential-password")
                                    state = {"visible": False, "generation": 0}

                                    def hide_password(
                                        label=password_value,
                                        state=state,
                                    ) -> None:
                                        label.set_text("••••••••••••")
                                        state["visible"] = False

                                    def toggle_password(
                                        cid=credential.credential_id,
                                        label=password_value,
                                        state=state,
                                    ) -> None:
                                        try:
                                            if state["visible"]:
                                                state["generation"] += 1
                                                hide_password(label, state)
                                                return

                                            secret = reveal_password(cid, user)
                                            state["generation"] += 1
                                            generation = state["generation"]
                                            label.set_text(secret)
                                            state["visible"] = True

                                            def auto_hide(
                                                label=label,
                                                state=state,
                                                generation=generation,
                                            ) -> None:
                                                if (
                                                    state["visible"]
                                                    and state["generation"] == generation
                                                ):
                                                    hide_password(label, state)

                                            ui.timer(20.0, auto_hide, once=True)
                                        except Exception as error:
                                            ui.notify(
                                                str(error),
                                                type="negative",
                                                position="top",
                                            )

                                    async def copy_password(
                                        cid=credential.credential_id,
                                    ) -> None:
                                        import json

                                        try:
                                            secret = reveal_password(
                                                cid,
                                                user,
                                                action="Cópia de senha",
                                            )
                                            await ui.run_javascript(
                                                "navigator.clipboard.writeText("
                                                f"{json.dumps(secret)})"
                                            )
                                            ui.notify(
                                                "Senha copiada.",
                                                type="positive",
                                                position="top",
                                            )
                                        except Exception as error:
                                            ui.notify(
                                                str(error),
                                                type="negative",
                                                position="top",
                                            )

                                    with ui.row().classes(
                                        "portal-system-credential-password-row"
                                    ):
                                        with ui.column().classes(
                                            "portal-system-credential-password-copy"
                                        ):
                                            ui.label("Senha").classes(
                                                "portal-system-credential-label"
                                            )
                                            password_value

                                        ui.button(
                                            "Revelar",
                                            icon="visibility",
                                            on_click=toggle_password,
                                        ).props(
                                            "flat no-caps"
                                        ).classes(
                                            "portal-system-credential-action"
                                        )

                                        ui.button(
                                            "Copiar",
                                            icon="content_copy",
                                            on_click=copy_password,
                                        ).props(
                                            "flat no-caps"
                                        ).classes(
                                            "portal-system-credential-action"
                                        )

                                ui.label(
                                    "Por segurança, uma senha revelada volta a ser ocultada "
                                    "automaticamente após 20 segundos."
                                ).classes("portal-system-credential-security-note")

                                if credential.access_tip:
                                    with ui.element("div").classes(
                                        "portal-system-credential-info"
                                    ):
                                        ui.icon("lightbulb")
                                        ui.label(credential.access_tip)

                                if credential.password_rule or credential.blocked_passwords:
                                    with ui.element("div").classes(
                                        "portal-system-credential-info"
                                    ):
                                        ui.icon("password")
                                        with ui.column().classes(
                                            "portal-system-credential-info-copy"
                                        ):
                                            ui.label(
                                                password_policy_label(
                                                    credential.blocked_passwords
                                                )
                                            )
                                            if credential.password_rule:
                                                ui.label(
                                                    credential.password_rule
                                                ).classes(
                                                    "portal-system-credential-info-secondary"
                                                )

                                if credential.notes:
                                    with ui.element("div").classes(
                                        "portal-system-credential-info"
                                    ):
                                        ui.icon("info")
                                        ui.label(credential.notes)

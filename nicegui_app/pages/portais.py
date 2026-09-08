from __future__ import annotations

import json
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
    get_public_credentials_for_portals,
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


def _portal_context(portal: PortalPreview) -> str:
    values = [
        portal.portal_type,
        portal.plan_name,
        portal.local_name,
    ]
    return " · ".join(value for value in values if value)



def _compact_credential(
    credential,
    user: dict,
) -> None:
    with ui.element("section").classes("portal-access-card-credential"):
        with ui.row().classes("portal-access-card-credential-head"):
            with ui.row().classes("portal-access-card-credential-title-wrap"):
                ui.icon("shield_lock")
                ui.label(
                    credential.identification or "Acesso principal"
                ).classes("portal-access-card-credential-title")

            if credential.password_changed_at:
                ui.label(
                    "Atualizada em "
                    f"{format_credential_datetime(credential.password_changed_at)}"
                ).classes("portal-access-card-credential-date")

        with ui.element("div").classes("portal-access-card-credential-grid"):
            with ui.element("div").classes("portal-access-card-field"):
                ui.label("LOGIN").classes("portal-access-card-field-label")

                with ui.row().classes("portal-access-card-field-value-row"):
                    ui.label(credential.login).classes(
                        "portal-access-card-login-value"
                    )

                    async def copy_login(login=credential.login) -> None:
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
                    ).props("flat round dense").classes(
                        "portal-access-card-copy-icon"
                    ).tooltip("Copiar login")

            password_value = ui.label("••••••••••").classes(
                "portal-access-card-password-value"
            )
            password_status = ui.label("").classes(
                "portal-access-card-password-status"
            )
            state = {"visible": False, "generation": 0}

            def hide_password(
                label=password_value,
                state=state,
            ) -> None:
                label.set_text("••••••••••")
                state["visible"] = False

            def toggle_password(
                cid=credential.credential_id,
                label=password_value,
                status=password_status,
                state=state,
            ) -> None:
                try:
                    if state["visible"]:
                        state["generation"] += 1
                        hide_password(label, state)
                        status.set_text("")
                        return

                    secret = reveal_password(cid, user)
                    state["generation"] += 1
                    generation = state["generation"]
                    label.set_text(secret)
                    status.set_text("Visível por 20 segundos")
                    state["visible"] = True

                    def auto_hide(
                        label=label,
                        status=status,
                        state=state,
                        generation=generation,
                    ) -> None:
                        if (
                            state["visible"]
                            and state["generation"] == generation
                        ):
                            hide_password(label, state)
                            status.set_text("")

                    ui.timer(20.0, auto_hide, once=True)
                except Exception as error:
                    hide_password(label, state)
                    status.set_text("Senha indisponível")
                    ui.notify(
                        str(error),
                        type="warning",
                        position="top",
                        timeout=6000,
                    )

            async def copy_password(
                cid=credential.credential_id,
                status=password_status,
            ) -> None:
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
                    status.set_text("Senha copiada")
                    ui.notify(
                        "Senha copiada.",
                        type="positive",
                        position="top",
                    )
                except Exception as error:
                    status.set_text("Senha indisponível")
                    ui.notify(
                        str(error),
                        type="warning",
                        position="top",
                        timeout=6000,
                    )

            with ui.element("div").classes("portal-access-card-field"):
                ui.label("SENHA").classes("portal-access-card-field-label")

                with ui.row().classes("portal-access-card-field-value-row"):
                    password_value

                    with ui.row().classes("portal-access-card-password-actions"):
                        ui.button(
                            icon="visibility",
                            on_click=toggle_password,
                        ).props("flat round dense").classes(
                            "portal-access-card-copy-icon"
                        ).tooltip("Revelar / ocultar senha")

                        ui.button(
                            icon="content_copy",
                            on_click=copy_password,
                        ).props("flat round dense").classes(
                            "portal-access-card-copy-icon"
                        ).tooltip("Copiar senha")

                password_status

        if credential.access_tip:
            with ui.row().classes("portal-access-card-credential-tip"):
                ui.icon("lightbulb")
                ui.label(credential.access_tip)

        with ui.row().classes("portal-access-card-security-note"):
            ui.icon("verified_user")
            ui.label(
                "Uso institucional. Não compartilhe ou salve estas credenciais "
                "fora dos ambientes autorizados."
            )



def _portal_card(
    portal: PortalPreview,
    user: dict,
    credentials: list,
) -> None:
    external = _safe_url(portal.url)

    with ui.element("article").classes("portal-access-card"):
        with ui.row().classes("portal-access-card-head"):
            with ui.element("div").classes("portal-access-card-icon"):
                ui.icon("vpn_key")

            with ui.row().classes("portal-access-card-head-badges"):
                if portal.requires_login:
                    with ui.element("span").classes("portal-access-auth-badge"):
                        ui.icon("lock")
                        ui.label("Login necessário")

                with ui.element("span").classes(
                    "portal-access-status is-active"
                    if _is_active(portal.status)
                    else "portal-access-status"
                ):
                    ui.element("span").classes("portal-access-status-dot")
                    ui.label(portal.status)

        with ui.column().classes("portal-access-card-copy"):
            ui.label(portal.operator_name).classes("portal-access-card-operator")
            ui.label(portal.name).classes("portal-access-card-title")

            context = _portal_context(portal)
            if context:
                ui.label(context).classes("portal-access-card-context")

            if portal.requires_login and credentials:
                _compact_credential(credentials[0], user)

                if len(credentials) > 1:
                    ui.label(
                        f"+ {len(credentials) - 1} outra"
                        f"{'s' if len(credentials) - 1 != 1 else ''} credencial"
                        f"{'is' if len(credentials) - 1 != 1 else ''} disponível"
                        f"{'is' if len(credentials) - 1 != 1 else ''} nos detalhes"
                    ).classes("portal-access-card-more-credentials")

            elif portal.requires_login:
                with ui.element("div").classes(
                    "portal-access-card-credential is-empty"
                ):
                    with ui.row().classes("portal-access-card-credential-head"):
                        with ui.row().classes(
                            "portal-access-card-credential-title-wrap"
                        ):
                            ui.icon("shield_lock")
                            ui.label("Credencial de acesso").classes(
                                "portal-access-card-credential-title"
                            )
                    ui.label(
                        "Nenhuma credencial ativa está cadastrada para este portal."
                    ).classes("portal-access-card-credential-empty")

            else:
                with ui.element("div").classes("portal-access-card-guidance"):
                    with ui.row().classes("portal-access-card-guidance-head"):
                        ui.icon("route")
                        ui.label("ACESSO")
                    ui.label(
                        portal.instruction
                        or portal.general_tip
                        or "Este portal não possui login obrigatório cadastrado."
                    ).classes("portal-access-card-guidance-text")

        with ui.element("div").classes("portal-access-card-footer"):
            ui.button(
                "Ver acesso completo",
                icon="arrow_forward",
                on_click=lambda pid=portal.portal_id: ui.navigate.to(
                    f"/portais/{pid}"
                ),
            ).props("flat no-caps").classes("portal-access-detail-action")

            if external:
                ui.link(
                    "Abrir portal",
                    target=external,
                    new_tab=True,
                ).classes("portal-access-open-action")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-access-empty"):
        ui.icon("vpn_key_off")
        ui.label(title).classes("portal-access-empty-title")
        ui.label(description).classes("portal-access-empty-description")


def render_portais(user: dict) -> None:
    portals = get_portais_preview()
    operators = sorted(
        {portal.operator_name for portal in portals if portal.operator_name}
    )
    credentials_by_portal = get_public_credentials_for_portals(
        [portal.portal_id for portal in portals if portal.requires_login]
    )

    with portal_layout(user=user, active="portals"):
        with ui.element("section").classes("portal-access-hero"):
            with ui.column().classes("portal-access-hero-copy"):
                ui.label("CENTRAL DE PORTAIS").classes("portal-access-hero-kicker")
                ui.label(
                    "Entre no sistema certo, com a orientação certa."
                ).classes("portal-access-hero-title")
                ui.label(
                    "Localize rapidamente o portal da operadora, entenda como acessar "
                    "e consulte as credenciais protegidas quando necessário."
                ).classes("portal-access-hero-description")

            with ui.element("div").classes("portal-access-hero-flow"):
                for icon, title, subtitle in (
                    ("search", "Localize", "o portal correto"),
                    ("route", "Confira", "como acessar"),
                    ("shield_lock", "Acesse", "com segurança"),
                ):
                    with ui.element("div").classes("portal-access-hero-step"):
                        with ui.element("div").classes("portal-access-hero-step-icon"):
                            ui.icon(icon)
                        with ui.column().classes("portal-access-hero-step-copy"):
                            ui.label(title).classes("portal-access-hero-step-title")
                            ui.label(subtitle).classes("portal-access-hero-step-subtitle")

        filter_state = {"operator": "Todas", "auth": "Todos"}
        operator_buttons: dict[str, object] = {}
        auth_buttons: dict[str, object] = {}

        with ui.element("section").classes("portal-access-toolbar"):
            with ui.element("div").classes("portal-access-search-wrap"):
                ui.icon("search")
                search = ui.input(
                    placeholder="Buscar portal, operadora, tipo, plano ou local..."
                ).props(
                    "borderless dense clearable autocomplete='off'"
                ).classes("portal-access-search")
                ui.button(
                    "Pesquisar",
                    icon="arrow_forward",
                    on_click=lambda: refresh(),
                ).props("unelevated no-caps").classes("portal-access-search-button")

            with ui.element("div").classes("portal-access-filter-panel"):
                ui.label("ACESSO").classes("portal-access-filter-label")
                with ui.element("div").classes("portal-access-filter-actions"):
                    for value, label in (
                        ("Todos", "Todos"),
                        ("Exige login", "Com login"),
                        ("Sem login", "Sem login"),
                    ):
                        button = ui.button(
                            label,
                            on_click=lambda selected=value: set_auth(selected),
                        ).props("flat no-caps").classes("portal-access-filter-button")
                        auth_buttons[value] = button

        with ui.element("section").classes("portal-access-operator-strip"):
            ui.label("OPERADORA").classes("portal-access-filter-label")
            with ui.element("div").classes("portal-access-operator-actions"):
                for value in ["Todas", *operators]:
                    button = ui.button(
                        value,
                        on_click=lambda selected=value: set_operator(selected),
                    ).props("flat no-caps").classes("portal-access-operator-button")
                    operator_buttons[value] = button

        with ui.element("section").classes("portal-access-credentials-warning"):
            with ui.element("div").classes("portal-access-credentials-warning-icon"):
                ui.icon("security")
            with ui.column().classes("portal-access-credentials-warning-copy"):
                ui.label("USO DAS CREDENCIAIS").classes(
                    "portal-access-credentials-warning-kicker"
                )
                ui.label(
                    "Utilize login e senha somente para atividades institucionais "
                    "autorizadas. Não compartilhe credenciais fora do ambiente de "
                    "trabalho e evite salvá-las em navegadores, arquivos pessoais ou "
                    "anotações não protegidas."
                ).classes("portal-access-credentials-warning-text")
            ui.label(
                "Revelação e cópia de senha ficam registradas na auditoria do Portal."
            ).classes("portal-access-credentials-warning-audit")

        with ui.row().classes("portal-access-results-head"):
            with ui.column().classes("portal-access-results-copy"):
                ui.label("PORTAIS DISPONÍVEIS").classes("portal-section-kicker")
                result_label = ui.label("").classes("portal-access-results-count")
            ui.label(
                "A orientação principal já aparece no card para reduzir cliques."
            ).classes("portal-access-results-note")

        cards = ui.element("div").classes("portal-access-grid")

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_operator = filter_state["operator"]
            selected_auth = filter_state["auth"]

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
                            portal.instruction,
                            portal.general_tip,
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

            for value, button in auth_buttons.items():
                button.classes(
                    add="is-selected" if value == selected_auth else "",
                    remove="" if value == selected_auth else "is-selected",
                )

            for value, button in operator_buttons.items():
                button.classes(
                    add="is-selected" if value == selected_operator else "",
                    remove="" if value == selected_operator else "is-selected",
                )

            count = len(filtered)
            result_label.set_text(
                f"{count} portal{'ais' if count != 1 else ''} encontrado"
                f"{'s' if count != 1 else ''}"
            )

            cards.clear()
            with cards:
                if not filtered:
                    _empty(
                        "Nenhum portal encontrado.",
                        "Revise a pesquisa ou altere os filtros.",
                    )
                    return

                for portal in filtered:
                    _portal_card(
                        portal,
                        user,
                        credentials_by_portal.get(portal.portal_id, []),
                    )

        def set_auth(value: str) -> None:
            filter_state["auth"] = value
            refresh()

        def set_operator(value: str) -> None:
            filter_state["operator"] = value
            refresh()

        search.on_value_change(lambda _: refresh())
        refresh()


def _detail_fact(icon: str, label: str, value: str) -> None:
    if not value:
        return
    with ui.element("div").classes("portal-access-fact"):
        with ui.element("div").classes("portal-access-fact-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-access-fact-copy"):
            ui.label(label).classes("portal-access-fact-label")
            ui.label(value).classes("portal-access-fact-value")


def _credential_card(credential, user: dict) -> None:
    with ui.element("article").classes("portal-system-credential-card"):
        with ui.row().classes("portal-system-credential-card-head"):
            with ui.column().classes("portal-system-credential-heading"):
                ui.label(credential.identification).classes(
                    "portal-system-credential-name"
                )
                ui.label(
                    "Senha atualizada: "
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
                    ui.label("Login").classes("portal-system-credential-label")
                    ui.label(credential.login).classes(
                        "portal-system-credential-value"
                    )

                async def copy_login(login=credential.login) -> None:
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
                ).props("flat round dense").classes(
                    "portal-system-credential-icon-action"
                ).tooltip("Copiar login")

            password_value = ui.label("••••••••••••").classes(
                "portal-system-credential-password"
            )
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

            async def copy_password(cid=credential.credential_id) -> None:
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
                ).props("flat no-caps").classes(
                    "portal-system-credential-action"
                )

                ui.button(
                    "Copiar",
                    icon="content_copy",
                    on_click=copy_password,
                ).props("flat no-caps").classes(
                    "portal-system-credential-action"
                )

        ui.label(
            "Por segurança, uma senha revelada volta a ser ocultada "
            "automaticamente após 20 segundos."
        ).classes("portal-system-credential-security-note")

        if credential.access_tip:
            with ui.element("div").classes("portal-system-credential-info"):
                ui.icon("lightbulb")
                ui.label(credential.access_tip)

        if credential.password_rule or credential.blocked_passwords:
            with ui.element("div").classes("portal-system-credential-info"):
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
            with ui.element("div").classes("portal-system-credential-info"):
                ui.icon("info")
                ui.label(credential.notes)


def render_portal_detail(user: dict, portal_id: str) -> None:
    portal = get_portal_detail(portal_id)

    with portal_layout(user=user, active="portals"):
        if portal is None:
            _empty(
                "Portal não encontrado.",
                "O registro pode ter sido removido ou o endereço está incorreto.",
            )
            return

        external = _safe_url(portal.url)
        credentials = (
            get_public_credentials(portal.portal_id)
            if portal.requires_login
            else []
        )

        with ui.row().classes("portal-access-detail-nav"):
            ui.button(
                "Todos os portais",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/portais"),
            ).props("flat no-caps").classes("portal-access-back-action")

            if external:
                ui.link(
                    "Abrir portal",
                    target=external,
                    new_tab=True,
                ).classes("portal-access-detail-open")

        with ui.element("section").classes("portal-access-detail-hero"):
            with ui.element("div").classes("portal-access-detail-hero-icon"):
                ui.icon("vpn_key")

            with ui.column().classes("portal-access-detail-hero-copy"):
                with ui.row().classes("portal-access-detail-meta"):
                    ui.label("ACESSO OPERACIONAL").classes(
                        "portal-access-detail-kicker"
                    )

                    if portal.requires_login:
                        with ui.element("span").classes(
                            "portal-access-detail-auth-badge"
                        ):
                            ui.icon("lock")
                            ui.label("Login necessário")

                ui.label(portal.name).classes("portal-access-detail-title")
                ui.label(portal.operator_name).classes(
                    "portal-access-detail-operator"
                )

                context = _portal_context(portal)
                if context:
                    ui.label(context).classes("portal-access-detail-context")

            with ui.element("div").classes("portal-access-detail-status"):
                ui.label("STATUS").classes("portal-access-detail-status-kicker")
                ui.label(portal.status).classes("portal-access-detail-status-value")
                ui.label(portal.code or "Sem código").classes(
                    "portal-access-detail-code"
                )

        with ui.element("section").classes("portal-access-detail-workspace"):
            with ui.element("article").classes("portal-access-route-card"):
                with ui.row().classes("portal-access-section-head"):
                    with ui.element("div").classes("portal-access-section-icon"):
                        ui.icon("route")
                    with ui.column().classes("portal-access-section-head-copy"):
                        ui.label("COMO ACESSAR").classes(
                            "portal-access-section-kicker"
                        )
                        ui.label("Orientação principal").classes(
                            "portal-access-section-title"
                        )

                ui.label(
                    portal.instruction
                    or portal.general_tip
                    or "Nenhuma instrução específica foi cadastrada para este portal."
                ).classes("portal-access-route-text")

                if portal.general_tip and portal.general_tip != portal.instruction:
                    with ui.row().classes("portal-access-route-tip"):
                        ui.icon("lightbulb")
                        ui.label(portal.general_tip)

                if external:
                    ui.link(
                        "Ir para o portal",
                        target=external,
                        new_tab=True,
                    ).classes("portal-access-route-primary")

            with ui.element("article").classes("portal-access-context-card"):
                with ui.row().classes("portal-access-section-head"):
                    with ui.element("div").classes("portal-access-section-icon"):
                        ui.icon("info")
                    with ui.column().classes("portal-access-section-head-copy"):
                        ui.label("CONTEXTO").classes("portal-access-section-kicker")
                        ui.label("Onde este acesso se aplica").classes(
                            "portal-access-section-title"
                        )

                with ui.element("div").classes("portal-access-facts-grid"):
                    _detail_fact("business", "Operadora", portal.operator_name)
                    _detail_fact(
                        "category",
                        "Tipo",
                        portal.portal_type or "Não informado",
                    )
                    _detail_fact("view_list", "Plano", portal.plan_name)
                    _detail_fact("place", "Local", portal.local_name)
                    _detail_fact(
                        "lock",
                        "Autenticação",
                        "Exige login" if portal.requires_login else "Sem login",
                    )

                if portal.observations:
                    with ui.element("div").classes("portal-access-observation"):
                        ui.label("OBSERVAÇÕES").classes(
                            "portal-access-observation-label"
                        )
                        ui.label(portal.observations).classes(
                            "portal-access-observation-text"
                        )

        if portal.requires_login:
            with ui.element("section").classes("portal-system-credentials-panel"):
                with ui.row().classes("portal-system-credentials-head"):
                    with ui.element("div").classes(
                        "portal-system-credentials-icon"
                    ):
                        ui.icon("shield_lock")
                    with ui.column().classes("portal-system-credentials-copy"):
                        ui.label("Credenciais de acesso").classes(
                            "portal-system-credentials-title"
                        )
                        ui.label(
                            "Use as credenciais institucionais abaixo. A senha só é "
                            "descriptografada no servidor quando você solicita revelar "
                            "ou copiar."
                        ).classes("portal-system-credentials-description")

                if not credentials:
                    ui.label(
                        "Nenhuma credencial ativa está cadastrada para este portal."
                    ).classes("portal-system-credentials-empty")
                else:
                    with ui.column().classes("portal-system-credentials-list"):
                        for credential in credentials:
                            _credential_card(credential, user)

from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.contatos_service import (
    ContatoPreview,
    get_contato_detail,
    get_contatos_preview,
)


def _normalized(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _is_active(status: str) -> bool:
    return _normalized(status) == "ativo"


def _contact_icon(contact_type: str) -> str:
    value = _normalized(contact_type)
    if "mail" in value or "email" in value or "e-mail" in value:
        return "mail"
    if "whats" in value:
        return "chat"
    if "site" in value or "portal" in value:
        return "language"
    return "phone"


def _contact_action(contact: ContatoPreview) -> tuple[str, str] | None:
    value = contact.contact.strip()
    kind = _normalized(contact.contact_type)

    if not value:
        return None

    if "mail" in kind or "email" in kind or "e-mail" in kind:
        return "Enviar e-mail", f"mailto:{value}"

    if "whats" in kind:
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return "Abrir WhatsApp", f"https://wa.me/{digits}"

    if "tel" in kind or "fone" in kind or "phone" in kind or "ramal" in kind:
        dial = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        if dial:
            return "Ligar", f"tel:{dial}"

    return None


def _contact_title(contact: ContatoPreview) -> str:
    return contact.sector or contact.purpose or "Contato"


def _hero_step(icon: str, title: str, subtitle: str) -> None:
    with ui.element("div").classes("portal-contacts-hero-step"):
        with ui.element("div").classes("portal-contacts-hero-step-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-contacts-hero-step-copy"):
            ui.label(title).classes("portal-contacts-hero-step-title")
            ui.label(subtitle).classes("portal-contacts-hero-step-subtitle")


def _hero_art() -> None:
    """Ilustração decorativa própria de Contatos, sem arquivo de imagem externo."""
    with ui.element("div").classes("portal-contacts-hero-art").props("aria-hidden=true"):
        ui.element("div").classes("portal-contacts-art-ring portal-contacts-art-ring-one")
        ui.element("div").classes("portal-contacts-art-ring portal-contacts-art-ring-two")

        with ui.element("div").classes("portal-contacts-art-center"):
            ui.icon("support_agent")

        for position, icon in (
            ("one", "mail"),
            ("two", "phone"),
            ("three", "chat"),
            ("four", "person"),
        ):
            with ui.element("div").classes(
                f"portal-contacts-art-node portal-contacts-art-node-{position}"
            ):
                ui.icon(icon)


def _contact_card(contact: ContatoPreview) -> None:
    action = _contact_action(contact)

    with ui.element("article").classes("portal-contact-card"):
        with ui.row().classes("portal-contact-card-head"):
            with ui.element("div").classes("portal-contact-card-identity"):
                with ui.element("div").classes("portal-contact-card-icon"):
                    ui.icon(_contact_icon(contact.contact_type))

                with ui.column().classes("portal-contact-card-heading"):
                    ui.label(contact.operator_name).classes(
                        "portal-contact-card-operator"
                    )
                    ui.label(_contact_title(contact)).classes(
                        "portal-contact-card-title"
                    )

            with ui.element("div").classes(
                "portal-contact-status is-active"
                if _is_active(contact.status)
                else "portal-contact-status"
            ):
                ui.element("span").classes("portal-contact-status-dot")
                ui.label(contact.status)

        if contact.purpose and contact.purpose != _contact_title(contact):
            ui.label(contact.purpose).classes("portal-contact-card-purpose")

        if contact.plan_name:
            with ui.row().classes("portal-contact-card-scope"):
                ui.icon("view_list")
                ui.label(contact.plan_name)

        with ui.element("div").classes("portal-contact-channel"):
            with ui.row().classes("portal-contact-channel-head"):
                ui.icon(_contact_icon(contact.contact_type))
                ui.label(contact.contact_type or "Contato").classes(
                    "portal-contact-channel-label"
                )
            ui.label(contact.contact or "Não informado").classes(
                "portal-contact-channel-value"
            )

        with ui.element("div").classes("portal-contact-card-facts"):
            if contact.responsible:
                with ui.element("div").classes("portal-contact-fact"):
                    ui.icon("person")
                    with ui.column().classes("portal-contact-fact-copy"):
                        ui.label("Responsável").classes("portal-contact-fact-label")
                        ui.label(contact.responsible).classes("portal-contact-fact-value")

            if contact.schedule:
                with ui.element("div").classes("portal-contact-fact"):
                    ui.icon("schedule")
                    with ui.column().classes("portal-contact-fact-copy"):
                        ui.label("Atendimento").classes("portal-contact-fact-label")
                        ui.label(contact.schedule).classes("portal-contact-fact-value")

        with ui.row().classes("portal-contact-card-actions"):
            ui.button(
                "Ver detalhes",
                icon="arrow_forward",
                on_click=lambda cid=contact.contact_id: ui.navigate.to(
                    f"/contatos/{cid}"
                ),
            ).props("flat no-caps").classes("portal-contact-detail-button")

            if action:
                label, target = action
                ui.link(label, target=target).classes("portal-contact-action-link")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-contacts-empty"):
        ui.icon("contact_phone")
        ui.label(title).classes("portal-contacts-empty-title")
        ui.label(description).classes("portal-contacts-empty-description")


def render_contatos(user: dict) -> None:
    contacts = [
        contact
        for contact in get_contatos_preview()
        if _is_active(contact.status)
    ]

    with portal_layout(user=user, active="contacts"):
        operators = sorted(
            {contact.operator_name for contact in contacts if contact.operator_name}
        )
        contact_types = sorted(
            {contact.contact_type for contact in contacts if contact.contact_type}
        )

        with ui.element("section").classes("portal-contacts-hero"):
            with ui.column().classes("portal-contacts-hero-copy"):
                ui.label("CENTRAL DE CONTATOS").classes("portal-contacts-hero-kicker")
                ui.label(
                    "Fale com a pessoa certa, pelo canal certo."
                ).classes("portal-contacts-hero-title")
                ui.label(
                    "Localize setores, responsáveis e canais oficiais das operadoras "
                    "sem interromper o fluxo do atendimento."
                ).classes("portal-contacts-hero-description")

            _hero_art()

            with ui.element("div").classes("portal-contacts-hero-flow"):
                _hero_step("search", "LOCALIZE", "o contato certo")
                _hero_step("person_search", "CONFIRA", "quem pode ajudar")
                _hero_step("forum", "CONTATE", "pelo canal oficial")

        with ui.element("section").classes("portal-contacts-searchbar"):
            search = ui.input(
                placeholder=(
                    "Buscar operadora, setor, finalidade, responsável, telefone ou e-mail..."
                )
            ).props("borderless clearable").classes("portal-contacts-search")
            search.props("prepend-icon=search")

            ui.button(
                "Pesquisar",
                icon="arrow_forward",
            ).props("unelevated no-caps").classes("portal-contacts-search-button")

        with ui.element("section").classes("portal-contacts-filterbar"):
            with ui.row().classes("portal-contacts-operator-filter"):
                ui.label("OPERADORA").classes("portal-contacts-filter-caption")
                operator_buttons: dict[str, object] = {}

                for name in ["Todas"] + operators:
                    button = ui.button(name).props("flat no-caps").classes(
                        "portal-contacts-chip"
                    )
                    operator_buttons[name] = button

            with ui.row().classes("portal-contacts-selects"):
                contact_type = ui.select(
                    options=["Todos"] + contact_types,
                    value="Todos",
                    label="Canal",
                ).props("outlined dense").classes("portal-contacts-filter")

        with ui.element("section").classes("portal-contacts-guidance"):
            with ui.element("div").classes("portal-contacts-guidance-icon"):
                ui.icon("verified_user")
            with ui.column().classes("portal-contacts-guidance-copy"):
                ui.label("CANAIS OFICIAIS").classes("portal-contacts-guidance-title")
                ui.label(
                    "Utilize os contatos cadastrados no Portal Comercial e confira "
                    "a finalidade e o horário antes de acionar a operadora."
                ).classes("portal-contacts-guidance-text")
            ui.label("Base institucional de consulta").classes(
                "portal-contacts-guidance-side"
            )

        with ui.row().classes("portal-contacts-results-head"):
            with ui.column().classes("portal-contacts-results-copy"):
                ui.label("CONTATOS DISPONÍVEIS").classes(
                    "portal-contacts-results-kicker"
                )
                result_label = ui.label("").classes("portal-contacts-result-label")
            ui.label(
                "Os principais dados já aparecem no card para reduzir cliques."
            ).classes("portal-contacts-results-note")

        cards = ui.element("div").classes("portal-contacts-grid")
        selected_operator = {"value": "Todas"}

        def update_operator_buttons() -> None:
            for name, button in operator_buttons.items():
                button.classes(
                    add="is-active" if name == selected_operator["value"] else "",
                    remove="" if name == selected_operator["value"] else "is-active",
                )

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_type = contact_type.value or "Todos"
            filtered: list[ContatoPreview] = []

            for contact in contacts:
                haystack = _normalized(
                    " ".join(
                        (
                            contact.sector,
                            contact.purpose,
                            contact.contact_type,
                            contact.contact,
                            contact.responsible,
                            contact.operator_name,
                            contact.plan_name,
                            contact.schedule,
                        )
                    )
                )

                operator_ok = (
                    selected_operator["value"] == "Todas"
                    or contact.operator_name == selected_operator["value"]
                )
                type_ok = (
                    selected_type == "Todos"
                    or contact.contact_type == selected_type
                )

                if (not term or term in haystack) and operator_ok and type_ok:
                    filtered.append(contact)

            result_label.set_text(f"{len(filtered)} contato(s) encontrado(s)")
            cards.clear()

            with cards:
                if not filtered:
                    _empty(
                        "Nenhum contato encontrado.",
                        "Revise a pesquisa ou altere os filtros.",
                    )
                    return

                for contact in filtered:
                    _contact_card(contact)

        def choose_operator(name: str) -> None:
            selected_operator["value"] = name
            update_operator_buttons()
            refresh()

        for name, button in operator_buttons.items():
            button.on_click(lambda _, value=name: choose_operator(value))

        search.on_value_change(lambda _: refresh())
        contact_type.on_value_change(lambda _: refresh())
        update_operator_buttons()
        refresh()


def _detail_item(icon: str, label: str, value: str) -> None:
    if not value:
        return

    with ui.element("div").classes("portal-contact-detail-item"):
        ui.icon(icon)
        with ui.column().classes("portal-contact-detail-item-copy"):
            ui.label(label).classes("portal-contact-detail-label")
            ui.label(value).classes("portal-contact-detail-value")


def render_contato_detail(user: dict, contact_id: str) -> None:
    contact = get_contato_detail(contact_id)

    with portal_layout(user=user, active="contacts"):
        if contact is None:
            _empty(
                "Contato não encontrado.",
                "O registro pode ter sido removido ou o endereço está incorreto.",
            )
            return

        ui.button(
            "Voltar para Contatos",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/contatos"),
        ).props("flat no-caps").classes("portal-contact-back-button")

        with ui.element("section").classes("portal-contact-detail-hero"):
            with ui.element("div").classes("portal-contact-detail-icon"):
                ui.icon(_contact_icon(contact.contact_type))

            with ui.column().classes("portal-contact-detail-copy"):
                ui.label("FICHA DO CONTATO").classes("portal-section-kicker")
                ui.label(_contact_title(contact)).classes("portal-contact-detail-title")

                if contact.purpose and contact.purpose != _contact_title(contact):
                    ui.label(contact.purpose).classes("portal-contact-detail-purpose")

                ui.label(contact.operator_name).classes(
                    "portal-contact-detail-operator"
                )

            action = _contact_action(contact)
            if action:
                label, target = action
                ui.link(label, target=target).classes(
                    "portal-contact-primary-action"
                )

        with ui.element("section").classes("portal-contact-main-highlight"):
            ui.icon(_contact_icon(contact.contact_type))
            with ui.column().classes("portal-contact-main-highlight-copy"):
                ui.label(contact.contact_type or "Contato").classes(
                    "portal-contact-main-highlight-label"
                )
                ui.label(contact.contact or "Não informado").classes(
                    "portal-contact-main-highlight-value"
                )

        with ui.element("section").classes("portal-contact-detail-grid"):
            _detail_item("business", "Operadora", contact.operator_name)
            _detail_item("view_list", "Plano", contact.plan_name)
            _detail_item("apartment", "Setor", contact.sector)
            _detail_item("flag", "Finalidade", contact.purpose)
            _detail_item("person", "Responsável", contact.responsible)
            _detail_item("schedule", "Horário", contact.schedule)
            _detail_item("tag", "Código", contact.code)
            _detail_item("fact_check", "Status", contact.status)

        if contact.observations:
            with ui.element("section").classes("portal-contact-notes-card"):
                with ui.row().classes("portal-contact-notes-head"):
                    ui.icon("info")
                    ui.label("Observações").classes("portal-contact-notes-title")
                ui.label(contact.observations).classes("portal-contact-notes-text")

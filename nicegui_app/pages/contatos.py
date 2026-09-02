from __future__ import annotations

from urllib.parse import quote

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


def _contact_card(contact: ContatoPreview) -> None:
    with ui.element("article").classes("portal-contact-card"):
        with ui.row().classes("portal-contact-card-top"):
            with ui.element("div").classes("portal-contact-card-icon"):
                ui.icon(_contact_icon(contact.contact_type))

            with ui.element("div").classes(
                "portal-contact-status is-active"
                if _is_active(contact.status)
                else "portal-contact-status"
            ):
                ui.element("span").classes("portal-contact-status-dot")
                ui.label(contact.status)

        ui.label(_contact_title(contact)).classes("portal-contact-card-title")

        if contact.purpose and contact.purpose != _contact_title(contact):
            ui.label(contact.purpose).classes("portal-contact-card-purpose")

        ui.label(contact.operator_name).classes("portal-contact-card-operator")

        if contact.plan_name:
            ui.label(contact.plan_name).classes("portal-contact-card-plan")

        with ui.element("div").classes("portal-contact-highlight"):
            ui.label(contact.contact_type or "Contato").classes(
                "portal-contact-highlight-label"
            )
            ui.label(contact.contact or "Não informado").classes(
                "portal-contact-highlight-value"
            )

        if contact.responsible:
            with ui.row().classes("portal-contact-detail-line"):
                ui.icon("person")
                ui.label(contact.responsible)

        if contact.schedule:
            with ui.row().classes("portal-contact-detail-line"):
                ui.icon("schedule")
                ui.label(contact.schedule)

        with ui.row().classes("portal-contact-card-actions"):
            ui.button(
                "Ver detalhes",
                icon="arrow_forward",
                on_click=lambda cid=contact.contact_id: ui.navigate.to(
                    f"/contatos/{cid}"
                ),
            ).props("flat no-caps").classes("portal-contact-detail-button")

            action = _contact_action(contact)
            if action:
                label, target = action
                ui.link(label, target=target).classes(
                    "portal-contact-action-link"
                )


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-contacts-empty"):
        ui.icon("contact_phone")
        ui.label(title).classes("portal-contacts-empty-title")
        ui.label(description).classes("portal-contacts-empty-description")


def render_contatos(user: dict) -> None:
    contacts = get_contatos_preview()

    with portal_layout(
        user=user,
        active="contacts",
        page_eyebrow="CENTRAL DE CONTATOS",
        page_title="Encontre rapidamente quem pode ajudar.",
        page_description=(
            "Consulte telefones, e-mails, setores, responsáveis e horários "
            "de atendimento vinculados às operadoras."
        ),
    ):
        operators = sorted(
            {contact.operator_name for contact in contacts if contact.operator_name}
        )
        contact_types = sorted(
            {contact.contact_type for contact in contacts if contact.contact_type}
        )

        with ui.element("section").classes("portal-contacts-summary"):
            with ui.column().classes("portal-contacts-summary-copy"):
                ui.label("RELACIONAMENTO").classes("portal-section-kicker")
                ui.label(f"{len(contacts):02d} contatos cadastrados").classes(
                    "portal-contacts-summary-value"
                )
                ui.label(
                    "Canais e responsáveis disponíveis para a operação."
                ).classes("portal-contacts-summary-description")

            with ui.row().classes("portal-contacts-summary-stats"):
                with ui.column().classes("portal-contacts-mini-stat"):
                    ui.label(
                        str(sum(1 for c in contacts if _is_active(c.status))).zfill(2)
                    ).classes("portal-contacts-mini-value")
                    ui.label("Ativos").classes("portal-contacts-mini-label")

                with ui.column().classes("portal-contacts-mini-stat"):
                    ui.label(str(len(operators)).zfill(2)).classes(
                        "portal-contacts-mini-value"
                    )
                    ui.label("Operadoras").classes("portal-contacts-mini-label")

        with ui.element("section").classes("portal-contacts-toolbar"):
            search = ui.input(
                placeholder="Buscar setor, finalidade, telefone, e-mail ou responsável"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-contacts-search"
            )

            operator = ui.select(
                options=["Todas"] + operators,
                value="Todas",
                label="Operadora",
            ).props("outlined dense").classes("portal-contacts-filter")

            contact_type = ui.select(
                options=["Todos"] + contact_types,
                value="Todos",
                label="Tipo",
            ).props("outlined dense").classes("portal-contacts-filter")

        result_label = ui.label("").classes("portal-contacts-result-label")
        cards = ui.element("div").classes("portal-contacts-grid")

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_operator = operator.value or "Todas"
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
                    selected_operator == "Todas"
                    or contact.operator_name == selected_operator
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

        search.on_value_change(lambda _: refresh())
        operator.on_value_change(lambda _: refresh())
        contact_type.on_value_change(lambda _: refresh())
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
                ui.label(_contact_title(contact)).classes(
                    "portal-contact-detail-title"
                )

                if contact.purpose and contact.purpose != _contact_title(contact):
                    ui.label(contact.purpose).classes(
                        "portal-contact-detail-purpose"
                    )

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
                    ui.label("Observações").classes(
                        "portal-contact-notes-title"
                    )
                ui.label(contact.observations).classes(
                    "portal-contact-notes-text"
                )

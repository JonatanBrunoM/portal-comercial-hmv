from __future__ import annotations

from urllib.parse import urlparse

from nicegui import ui

from nicegui_app.hero_art import render_hero_art
from nicegui_app.layout import portal_layout
from nicegui_app.services.documentos_service import (
    DocumentoPreview,
    get_documento_detail,
    get_documentos_preview,
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


def _validity_label(document: DocumentoPreview) -> str:
    if document.validity_days is None:
        return "Sem validade informada"
    if document.validity_days == 1:
        return "1 dia"
    return f"{document.validity_days} dias"


def _scope_label(document: DocumentoPreview) -> str:
    parts = [document.plan_name, document.attendance_type, document.local_name]
    return " · ".join(part for part in parts if part) or "Aplicação geral"


def _document_card(document: DocumentoPreview) -> None:
    external = _safe_url(document.file_url)

    with ui.element("article").classes("portal-document-card"):
        with ui.row().classes("portal-document-card-head"):
            with ui.element("div").classes("portal-document-card-icon"):
                ui.icon("description")
            with ui.column().classes("portal-document-card-identity"):
                ui.label(document.operator_name.upper()).classes("portal-document-card-operator")
                ui.label(document.name).classes("portal-document-card-title")
                ui.label(_scope_label(document)).classes("portal-document-card-scope")

        with ui.row().classes("portal-document-badges"):
            with ui.element("div").classes(
                "portal-document-badge is-required" if document.required else "portal-document-badge"
            ):
                ui.icon("priority_high" if document.required else "check_circle_outline")
                ui.label("Obrigatório" if document.required else "Opcional")

            if document.file_format:
                with ui.element("div").classes("portal-document-badge"):
                    ui.icon("draft")
                    ui.label(document.file_format)

            if document.validity_days is not None:
                with ui.element("div").classes("portal-document-badge"):
                    ui.icon("event")
                    ui.label(_validity_label(document))

        with ui.element("div").classes("portal-document-guidance-preview"):
            with ui.row().classes("portal-document-guidance-preview-head"):
                ui.icon("route")
                ui.label("ORIENTAÇÃO PRINCIPAL")
            ui.label(
                document.guidance
                or document.observations
                or "Nenhuma orientação complementar foi cadastrada para este documento."
            ).classes("portal-document-card-description")

        with ui.row().classes("portal-document-card-actions"):
            ui.button(
                "Ver ficha completa",
                icon="arrow_forward",
                on_click=lambda did=document.document_id: ui.navigate.to(f"/documentos/{did}"),
            ).props("flat no-caps").classes("portal-document-detail-button")

            if external:
                ui.link("Abrir documento", target=external, new_tab=True).classes(
                    "portal-document-file-link portal-document-file-link-primary"
                )
            else:
                with ui.element("div").classes("portal-document-no-file"):
                    ui.icon("link_off")
                    ui.label("Arquivo não vinculado")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-documents-empty"):
        ui.icon("description_off")
        ui.label(title).classes("portal-documents-empty-title")
        ui.label(description).classes("portal-documents-empty-description")


def render_documentos(user: dict) -> None:
    documents = [document for document in get_documentos_preview() if _is_active(document.status)]
    operators = sorted({doc.operator_name for doc in documents if doc.operator_name})
    attendance_types = sorted({doc.attendance_type for doc in documents if doc.attendance_type})

    with portal_layout(user=user, active="documents"):
        with ui.element("section").classes("portal-documents-hero"):
            with ui.column().classes("portal-documents-hero-copy"):
                ui.label("CENTRAL DE DOCUMENTOS").classes("portal-documents-hero-kicker")
                ui.label("Encontre o documento certo, sem perder tempo.").classes(
                    "portal-documents-hero-title"
                )
                ui.label(
                    "Consulte exigências, validade, formato e a orientação de uso antes de seguir com o atendimento."
                ).classes("portal-documents-hero-description")

            with ui.element("div").classes("portal-documents-hero-flow"):
                for icon, title, text in (
                    ("search", "LOCALIZE", "o documento"),
                    ("fact_check", "CONFIRA", "a exigência"),
                    ("description", "UTILIZE", "a versão correta"),
                ):
                    with ui.row().classes("portal-documents-hero-step"):
                        with ui.element("div").classes("portal-documents-hero-step-icon"):
                            ui.icon(icon)
                        with ui.column().classes("portal-documents-hero-step-copy"):
                            ui.label(title)
                            ui.label(text)

            render_hero_art(variant="documents", icon="description")

        with ui.element("section").classes("portal-documents-searchbar"):
            search = ui.input(
                placeholder="Buscar documento, operadora, plano, atendimento ou orientação..."
            ).props("borderless dense clearable").classes("portal-documents-search")
            with search.add_slot("prepend"):
                ui.icon("search")
            ui.button("Pesquisar", icon="arrow_forward", on_click=lambda: refresh()).props(
                "no-caps unelevated"
            ).classes("portal-documents-search-button")

        with ui.row().classes("portal-documents-filter-row"):
            with ui.row().classes("portal-documents-operator-chips"):
                ui.label("OPERADORA").classes("portal-documents-filter-caption")
                operator_buttons: dict[str, object] = {}
                operator_state = {"value": "Todas"}

                def choose_operator(value: str) -> None:
                    operator_state["value"] = value
                    for key, button in operator_buttons.items():
                        button.classes(
                            "portal-documents-chip is-active" if key == value else "portal-documents-chip",
                            replace=True,
                        )
                    refresh()

                for option in ["Todas"] + operators:
                    button = ui.button(option, on_click=lambda _, value=option: choose_operator(value)).props(
                        "flat no-caps dense"
                    ).classes("portal-documents-chip" + (" is-active" if option == "Todas" else ""))
                    operator_buttons[option] = button

            with ui.row().classes("portal-documents-secondary-filters"):
                attendance = ui.select(
                    options=["Todos"] + attendance_types,
                    value="Todos",
                    label="Atendimento",
                ).props("outlined dense options-dense").classes("portal-documents-filter")
                requirement = ui.select(
                    options=["Todos", "Obrigatórios", "Opcionais"],
                    value="Todos",
                    label="Exigência",
                ).props("outlined dense options-dense").classes("portal-documents-filter")

        with ui.element("section").classes("portal-documents-alert"):
            with ui.element("div").classes("portal-documents-alert-icon"):
                ui.icon("verified_user")
            with ui.column().classes("portal-documents-alert-copy"):
                ui.label("ANTES DE UTILIZAR").classes("portal-documents-alert-title")
                ui.label(
                    "Confira a operadora, o plano, o tipo de atendimento e a validade. A orientação cadastrada no Portal Comercial deve ser considerada junto ao documento disponível."
                ).classes("portal-documents-alert-text")
            ui.label("Base institucional de consulta").classes("portal-documents-alert-note")

        with ui.row().classes("portal-documents-results-head"):
            with ui.column().classes("portal-documents-results-copy"):
                ui.label("DOCUMENTOS DISPONÍVEIS").classes("portal-section-kicker")
                result_label = ui.label("").classes("portal-documents-result-label")
            ui.label("A orientação principal já aparece no card para reduzir cliques.").classes(
                "portal-documents-results-hint"
            )

        cards = ui.element("div").classes("portal-documents-grid")

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_operator = operator_state["value"]
            selected_attendance = attendance.value or "Todos"
            selected_requirement = requirement.value or "Todos"
            filtered: list[DocumentoPreview] = []

            for document in documents:
                haystack = _normalized(" ".join((
                    document.name,
                    document.operator_name,
                    document.plan_name,
                    document.local_name,
                    document.attendance_type,
                    document.file_format,
                    document.code,
                    document.guidance,
                    document.observations,
                )))
                operator_ok = selected_operator == "Todas" or document.operator_name == selected_operator
                attendance_ok = selected_attendance == "Todos" or document.attendance_type == selected_attendance
                requirement_ok = (
                    document.required if selected_requirement == "Obrigatórios"
                    else not document.required if selected_requirement == "Opcionais"
                    else True
                )
                if (not term or term in haystack) and operator_ok and attendance_ok and requirement_ok:
                    filtered.append(document)

            result_label.set_text(f"{len(filtered)} documento(s) encontrado(s)")
            cards.clear()
            with cards:
                if not filtered:
                    _empty("Nenhum documento encontrado.", "Revise a pesquisa ou altere os filtros.")
                    return
                for document in filtered:
                    _document_card(document)

        search.on("keydown.enter", lambda _: refresh())
        search.on_value_change(lambda _: refresh())
        attendance.on_value_change(lambda _: refresh())
        requirement.on_value_change(lambda _: refresh())
        refresh()


def _detail_item(icon: str, label: str, value: str) -> None:
    if not value:
        return
    with ui.element("div").classes("portal-document-detail-item"):
        ui.icon(icon)
        with ui.column().classes("portal-document-detail-item-copy"):
            ui.label(label).classes("portal-document-detail-label")
            ui.label(value).classes("portal-document-detail-value")


def render_documento_detail(user: dict, document_id: str) -> None:
    document = get_documento_detail(document_id)

    with portal_layout(user=user, active="documents"):
        if document is None or not _is_active(document.status):
            _empty("Documento não encontrado.", "O registro pode estar indisponível ou o endereço está incorreto.")
            return

        ui.button(
            "Voltar para Documentos",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/documentos"),
        ).props("flat no-caps").classes("portal-document-back-button")

        with ui.element("section").classes("portal-document-detail-hero"):
            with ui.element("div").classes("portal-document-detail-icon"):
                ui.icon("description")
            with ui.column().classes("portal-document-detail-copy"):
                ui.label("FICHA DO DOCUMENTO").classes("portal-section-kicker")
                ui.label(document.name).classes("portal-document-detail-title")
                ui.label(document.operator_name).classes("portal-document-detail-operator")
                with ui.row().classes("portal-document-detail-badges"):
                    with ui.element("div").classes(
                        "portal-document-badge is-required" if document.required else "portal-document-badge"
                    ):
                        ui.icon("priority_high" if document.required else "check_circle_outline")
                        ui.label("Obrigatório" if document.required else "Opcional")
                    with ui.element("div").classes("portal-document-badge"):
                        ui.icon("event")
                        ui.label(_validity_label(document))

            external = _safe_url(document.file_url)
            if external:
                ui.link("Abrir documento", target=external, new_tab=True).classes(
                    "portal-document-open-link"
                )

        with ui.element("section").classes("portal-document-detail-grid"):
            _detail_item("business", "Operadora", document.operator_name)
            _detail_item("view_list", "Plano", document.plan_name)
            _detail_item("medical_services", "Atendimento", document.attendance_type)
            _detail_item("place", "Local", document.local_name)
            _detail_item("insert_drive_file", "Formato", document.file_format)
            _detail_item("event", "Validade", _validity_label(document))
            _detail_item("tag", "Código", document.code)
            _detail_item("fact_check", "Status", document.status)

        if document.guidance:
            with ui.element("section").classes("portal-document-guidance-card is-primary"):
                with ui.row().classes("portal-document-guidance-head"):
                    ui.icon("route")
                    ui.label("Orientação de uso").classes("portal-document-guidance-title")
                ui.label(document.guidance).classes("portal-document-guidance-text")

        if document.observations:
            with ui.element("section").classes("portal-document-guidance-card"):
                with ui.row().classes("portal-document-guidance-head"):
                    ui.icon("info")
                    ui.label("Observações").classes("portal-document-guidance-title")
                ui.label(document.observations).classes("portal-document-guidance-text")

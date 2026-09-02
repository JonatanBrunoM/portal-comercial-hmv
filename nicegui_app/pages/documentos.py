from __future__ import annotations

from urllib.parse import urlparse

from nicegui import ui

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
        return "Validade não informada"
    if document.validity_days == 1:
        return "Validade: 1 dia"
    return f"Validade: {document.validity_days} dias"


def _document_card(document: DocumentoPreview) -> None:
    with ui.element("article").classes("portal-document-card"):
        with ui.row().classes("portal-document-card-top"):
            with ui.element("div").classes("portal-document-card-icon"):
                ui.icon("description")
            with ui.element("div").classes(
                "portal-document-status is-active"
                if _is_active(document.status)
                else "portal-document-status"
            ):
                ui.element("span").classes("portal-document-status-dot")
                ui.label(document.status)

        ui.label(document.name).classes("portal-document-card-title")
        ui.label(document.operator_name).classes("portal-document-card-operator")

        meta = " · ".join(
            item for item in (
                document.attendance_type,
                document.file_format,
                document.plan_name,
                document.local_name,
            )
            if item
        )
        if meta:
            ui.label(meta).classes("portal-document-card-meta")

        with ui.row().classes("portal-document-badges"):
            with ui.element("div").classes(
                "portal-document-badge is-required"
                if document.required
                else "portal-document-badge"
            ):
                ui.icon("priority_high" if document.required else "info")
                ui.label("Obrigatório" if document.required else "Opcional")

            if document.validity_days is not None:
                with ui.element("div").classes("portal-document-badge"):
                    ui.icon("event")
                    ui.label(_validity_label(document))

        ui.label(
            document.guidance
            or document.observations
            or "Consulte os detalhes para orientações de uso deste documento."
        ).classes("portal-document-card-description")

        with ui.row().classes("portal-document-card-actions"):
            ui.button(
                "Ver detalhes",
                icon="arrow_forward",
                on_click=lambda did=document.document_id: ui.navigate.to(
                    f"/documentos/{did}"
                ),
            ).props("flat no-caps").classes("portal-document-detail-button")

            external = _safe_url(document.file_url)
            if external:
                ui.link(
                    "Abrir arquivo",
                    target=external,
                    new_tab=True,
                ).classes("portal-document-file-link")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-documents-empty"):
        ui.icon("description_off")
        ui.label(title).classes("portal-documents-empty-title")
        ui.label(description).classes("portal-documents-empty-description")


def render_documentos(user: dict) -> None:
    documents = get_documentos_preview()

    with portal_layout(
        user=user,
        active="documents",
        page_eyebrow="CENTRAL DE DOCUMENTOS",
        page_title="Documentos certos para cada atendimento.",
        page_description=(
            "Consulte documentos exigidos, validade, formato, orientações "
            "e arquivos vinculados às operadoras."
        ),
    ):
        operators = sorted(
            {doc.operator_name for doc in documents if doc.operator_name}
        )
        attendance_types = sorted(
            {doc.attendance_type for doc in documents if doc.attendance_type}
        )

        with ui.element("section").classes("portal-documents-summary"):
            with ui.column().classes("portal-documents-summary-copy"):
                ui.label("BASE DOCUMENTAL").classes("portal-section-kicker")
                ui.label(f"{len(documents):02d} documentos cadastrados").classes(
                    "portal-documents-summary-value"
                )
                ui.label(
                    "Requisitos e orientações vinculados ao atendimento."
                ).classes("portal-documents-summary-description")

            with ui.row().classes("portal-documents-summary-stats"):
                for value, label in (
                    (sum(1 for d in documents if d.required), "Obrigatórios"),
                    (sum(1 for d in documents if _is_active(d.status)), "Ativos"),
                ):
                    with ui.column().classes("portal-documents-mini-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-documents-mini-value"
                        )
                        ui.label(label).classes("portal-documents-mini-label")

        with ui.element("section").classes("portal-documents-toolbar"):
            search = ui.input(
                placeholder="Buscar documento, operadora, tipo ou plano"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-documents-search"
            )

            operator = ui.select(
                options=["Todas"] + operators,
                value="Todas",
                label="Operadora",
            ).props("outlined dense").classes("portal-documents-filter")

            attendance = ui.select(
                options=["Todos"] + attendance_types,
                value="Todos",
                label="Atendimento",
            ).props("outlined dense").classes("portal-documents-filter")

            requirement = ui.select(
                options=["Todos", "Obrigatórios", "Opcionais"],
                value="Todos",
                label="Exigência",
            ).props("outlined dense").classes("portal-documents-filter")

        result_label = ui.label("").classes("portal-documents-result-label")
        cards = ui.element("div").classes("portal-documents-grid")

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_operator = operator.value or "Todas"
            selected_attendance = attendance.value or "Todos"
            selected_requirement = requirement.value or "Todos"

            filtered: list[DocumentoPreview] = []

            for document in documents:
                haystack = _normalized(
                    " ".join(
                        (
                            document.name,
                            document.operator_name,
                            document.plan_name,
                            document.local_name,
                            document.attendance_type,
                            document.file_format,
                            document.code,
                            document.guidance,
                        )
                    )
                )

                operator_ok = (
                    selected_operator == "Todas"
                    or document.operator_name == selected_operator
                )
                attendance_ok = (
                    selected_attendance == "Todos"
                    or document.attendance_type == selected_attendance
                )

                if selected_requirement == "Obrigatórios":
                    requirement_ok = document.required
                elif selected_requirement == "Opcionais":
                    requirement_ok = not document.required
                else:
                    requirement_ok = True

                if (
                    (not term or term in haystack)
                    and operator_ok
                    and attendance_ok
                    and requirement_ok
                ):
                    filtered.append(document)

            result_label.set_text(f"{len(filtered)} documento(s) encontrado(s)")
            cards.clear()

            with cards:
                if not filtered:
                    _empty(
                        "Nenhum documento encontrado.",
                        "Revise a pesquisa ou altere os filtros.",
                    )
                    return

                for document in filtered:
                    _document_card(document)

        search.on_value_change(lambda _: refresh())
        operator.on_value_change(lambda _: refresh())
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
        if document is None:
            _empty(
                "Documento não encontrado.",
                "O registro pode ter sido removido ou o endereço está incorreto.",
            )
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
                ui.label(document.operator_name).classes(
                    "portal-document-detail-operator"
                )

                with ui.row().classes("portal-document-detail-badges"):
                    with ui.element("div").classes(
                        "portal-document-badge is-required"
                        if document.required
                        else "portal-document-badge"
                    ):
                        ui.icon("priority_high" if document.required else "info")
                        ui.label(
                            "Obrigatório" if document.required else "Opcional"
                        )

                    with ui.element("div").classes("portal-document-badge"):
                        ui.icon("event")
                        ui.label(_validity_label(document))

            external = _safe_url(document.file_url)
            if external:
                ui.link(
                    "Abrir arquivo",
                    target=external,
                    new_tab=True,
                ).classes("portal-document-open-link")

        with ui.element("section").classes("portal-document-detail-grid"):
            _detail_item("business", "Operadora", document.operator_name)
            _detail_item("view_list", "Plano", document.plan_name)
            _detail_item("medical_services", "Atendimento", document.attendance_type)
            _detail_item("place", "Local", document.local_name)
            _detail_item("insert_drive_file", "Formato", document.file_format)
            _detail_item(
                "event",
                "Validade",
                _validity_label(document),
            )
            _detail_item("tag", "Código", document.code)
            _detail_item("fact_check", "Status", document.status)

        if document.guidance:
            with ui.element("section").classes("portal-document-guidance-card"):
                with ui.row().classes("portal-document-guidance-head"):
                    ui.icon("route")
                    ui.label("Orientação").classes(
                        "portal-document-guidance-title"
                    )
                ui.label(document.guidance).classes(
                    "portal-document-guidance-text"
                )

        if document.observations:
            with ui.element("section").classes("portal-document-guidance-card"):
                with ui.row().classes("portal-document-guidance-head"):
                    ui.icon("info")
                    ui.label("Observações").classes(
                        "portal-document-guidance-title"
                    )
                ui.label(document.observations).classes(
                    "portal-document-guidance-text"
                )

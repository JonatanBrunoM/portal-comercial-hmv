from __future__ import annotations

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.comunicados_admin_service import (
    AdminComunicado,
    get_admin_comunicados,
    get_communication_reference_data,
    is_current,
    save_comunicado,
)


CATEGORIES = [
    "Geral",
    "Operacional",
    "Autorização",
    "Elegibilidade",
    "Cobertura",
    "Documentação",
    "Financeiro",
    "Contingência",
]

PRIORITIES = ["Baixa", "Normal", "Alta", "Crítica"]


def render_admin_comunicados(user: dict) -> None:
    communications = get_admin_comunicados()
    operators = get_communication_reference_data()

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · COMUNICADOS",
        page_title="Gestão de Comunicados",
        page_description=(
            "Publique orientações temporárias, mudanças operacionais e avisos "
            "relevantes para as equipes que utilizam o Portal Comercial."
        ),
    ):
        ui.button(
            "Voltar à Administração",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/administracao"),
        ).props("flat no-caps").classes("portal-admin-communications-back")

        with ui.element("section").classes("portal-admin-communications-hero"):
            with ui.column().classes("portal-admin-communications-hero-copy"):
                ui.label("INFORMAÇÃO EM DESTAQUE").classes("portal-section-kicker")
                ui.label(
                    "Comunicados que chegam à equipe no momento certo."
                ).classes("portal-admin-communications-hero-title")
                ui.label(
                    "Controle período de exibição, prioridade, público e destaque "
                    "de cada comunicado publicado no portal."
                ).classes("portal-admin-communications-hero-description")

            with ui.row().classes("portal-admin-communications-stats"):
                for value, label in (
                    (len(communications), "Comunicados"),
                    (sum(1 for item in communications if is_current(item)), "Vigentes"),
                    (
                        sum(
                            1
                            for item in communications
                            if item.featured and is_current(item)
                        ),
                        "Destaques",
                    ),
                ):
                    with ui.column().classes("portal-admin-communications-stat"):
                        ui.label(str(value).zfill(2)).classes(
                            "portal-admin-communications-stat-value"
                        )
                        ui.label(label).classes(
                            "portal-admin-communications-stat-label"
                        )

        with ui.row().classes("portal-admin-communications-toolbar"):
            search = ui.input(
                placeholder="Buscar título, categoria, operadora ou responsável"
            ).props(
                "outlined dense clearable prepend-icon=search"
            ).classes("portal-admin-communications-search")

            operator_filter = ui.select(
                {"Todos": "Todas / institucional", **operators},
                value="Todos",
                label="Operadora",
            ).props("outlined dense").classes(
                "portal-admin-communications-filter"
            )

            status_filter = ui.select(
                ["Todos", "Rascunho", "Publicado", "Inativo"],
                value="Todos",
                label="Status",
            ).props("outlined dense").classes(
                "portal-admin-communications-filter"
            )

            ui.button(
                "Novo comunicado",
                icon="campaign",
                on_click=lambda: _open_dialog(user, None, operators),
            ).props("unelevated no-caps").classes(
                "portal-admin-communications-primary"
            )

        count = ui.label("").classes("portal-admin-communications-count")
        container = ui.element("section").classes(
            "portal-admin-communications-list"
        )

        def refresh() -> None:
            term = str(search.value or "").strip().lower()
            filtered: list[AdminComunicado] = []

            for item in communications:
                text_ok = (
                    not term
                    or any(
                        term in value.lower()
                        for value in (
                            item.title,
                            item.summary,
                            item.category,
                            item.operator_name,
                            item.responsible,
                            item.code,
                        )
                    )
                )
                operator_ok = (
                    operator_filter.value == "Todos"
                    or item.operator_id == operator_filter.value
                )
                status_ok = (
                    status_filter.value == "Todos"
                    or item.status == status_filter.value
                )

                if text_ok and operator_ok and status_ok:
                    filtered.append(item)

            count.set_text(f"{len(filtered)} comunicado(s)")
            container.clear()

            with container:
                if not filtered:
                    with ui.element("div").classes(
                        "portal-admin-communications-empty"
                    ):
                        ui.icon("campaign")
                        ui.label("Nenhum comunicado encontrado.")
                    return

                for item in filtered:
                    current = is_current(item)
                    with ui.element("article").classes(
                        "portal-admin-communications-row"
                    ):
                        with ui.element("div").classes(
                            "portal-admin-communications-icon"
                        ):
                            ui.icon(
                                "priority_high"
                                if item.priority in {"Alta", "Crítica"}
                                else "campaign"
                            )

                        with ui.column().classes(
                            "portal-admin-communications-copy"
                        ):
                            with ui.row().classes(
                                "portal-admin-communications-title-line"
                            ):
                                ui.label(item.title).classes(
                                    "portal-admin-communications-title"
                                )
                                if item.featured:
                                    ui.icon("star").classes(
                                        "portal-admin-communications-star"
                                    )

                            ui.label(
                                item.summary or "Sem resumo"
                            ).classes(
                                "portal-admin-communications-summary"
                            )

                            meta = " · ".join(
                                value
                                for value in (
                                    item.operator_name,
                                    item.category,
                                    item.responsible,
                                )
                                if value
                            )
                            if meta:
                                ui.label(meta).classes(
                                    "portal-admin-communications-meta"
                                )

                        with ui.element("div").classes(
                            "portal-admin-communications-priority "
                            + _priority_class(item.priority)
                        ):
                            ui.label(item.priority)

                        with ui.element("div").classes(
                            "portal-admin-communications-status "
                            + ("is-current" if current else "")
                        ):
                            ui.element("span").classes(
                                "portal-admin-communications-status-dot"
                            )
                            ui.label("Vigente" if current else item.status)

                        ui.button(
                            "Editar",
                            icon="edit",
                            on_click=lambda current_item=item: _open_dialog(
                                user,
                                current_item,
                                operators,
                            ),
                        ).props("flat no-caps").classes(
                            "portal-admin-communications-edit"
                        )

        search.on_value_change(lambda _: refresh())
        operator_filter.on_value_change(lambda _: refresh())
        status_filter.on_value_change(lambda _: refresh())
        refresh()


def _priority_class(priority: str) -> str:
    value = priority.strip().lower()
    if value == "crítica":
        return "is-critical"
    if value == "alta":
        return "is-high"
    if value == "baixa":
        return "is-low"
    return "is-normal"


def _open_dialog(
    user: dict,
    item: AdminComunicado | None,
    operators: dict[str, str],
) -> None:
    with ui.dialog() as dialog, ui.card().classes(
        "portal-admin-communications-dialog"
    ):
        ui.label(
            "EDITAR COMUNICADO" if item else "NOVO COMUNICADO"
        ).classes("portal-section-kicker")
        ui.label(
            item.title if item else "Publicar comunicado"
        ).classes("portal-admin-communications-dialog-title")

        code = ui.input(
            "Código",
            value=item.code if item else "",
        ).props("outlined")

        operator = ui.select(
            {"": "Geral / institucional", **operators},
            value=item.operator_id if item else "",
            label="Operadora",
        ).props("outlined")

        title = ui.input(
            "Título",
            value=item.title if item else "",
        ).props("outlined")

        summary = ui.textarea(
            "Resumo",
            value=item.summary if item else "",
        ).props("outlined autogrow")

        content = ui.textarea(
            "Conteúdo",
            value=item.content if item else "",
        ).props("outlined autogrow")

        category = ui.select(
            CATEGORIES,
            value=(
                item.category
                if item and item.category in CATEGORIES
                else "Geral"
            ),
            label="Categoria",
        ).props("outlined")

        priority = ui.select(
            PRIORITIES,
            value=(
                item.priority
                if item and item.priority in PRIORITIES
                else "Normal"
            ),
            label="Prioridade",
        ).props("outlined")

        target_audience = ui.input(
            "Público-alvo",
            value=item.target_audience if item else "",
            placeholder="Ex.: Recepção, Autorizações, Comercial",
        ).props("outlined")

        start_date = ui.input(
            "Início da publicação",
            value=item.start_date if item else "",
        ).props("outlined type=date")

        end_date = ui.input(
            "Fim da publicação",
            value=item.end_date if item else "",
        ).props("outlined type=date")

        featured = ui.switch(
            "Destacar este comunicado",
            value=item.featured if item else False,
        )

        status = ui.select(
            ["Rascunho", "Publicado", "Inativo"],
            value=item.status if item else "Rascunho",
            label="Status",
        ).props("outlined")

        responsible = ui.input(
            "Responsável",
            value=item.responsible if item else "",
        ).props("outlined")

        for field in (
            code,
            operator,
            title,
            summary,
            content,
            category,
            priority,
            target_audience,
            start_date,
            end_date,
            status,
            responsible,
        ):
            field.classes("portal-admin-communications-dialog-field")

        featured.classes("portal-admin-communications-dialog-switch")

        def save() -> None:
            try:
                save_comunicado(
                    record_id=item.record_id if item else None,
                    code=code.value or "",
                    operator_id=operator.value or "",
                    title=title.value or "",
                    summary=summary.value or "",
                    content=content.value or "",
                    category=category.value or "",
                    priority=priority.value or "",
                    target_audience=target_audience.value or "",
                    start_date=start_date.value or "",
                    end_date=end_date.value or "",
                    featured=bool(featured.value),
                    status=status.value or "",
                    responsible=responsible.value or "",
                    actor=user,
                )
            except Exception as error:
                ui.notify(str(error), type="negative", position="top")
                return

            ui.notify(
                "Comunicado salvo com sucesso.",
                type="positive",
                position="top",
            )
            dialog.close()
            ui.navigate.to("/administracao/comunicados")

        with ui.row().classes(
            "portal-admin-communications-dialog-actions"
        ):
            ui.button(
                "Cancelar",
                on_click=dialog.close,
            ).props("flat no-caps")

            ui.button(
                "Salvar comunicado",
                icon="check",
                on_click=save,
            ).props("unelevated no-caps").classes(
                "portal-admin-communications-primary"
            )

    dialog.open()

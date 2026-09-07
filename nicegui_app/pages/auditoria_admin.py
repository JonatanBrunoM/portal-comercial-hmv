from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.auditoria_service import (
    AuditEntry,
    filter_audit_entries,
    get_audit_data,
)


_SP_TZ = ZoneInfo("America/Sao_Paulo")


def _initials(name: str) -> str:
    parts = [part for part in name.split() if part]
    if not parts:
        return "HM"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _is_today(entry: AuditEntry) -> bool:
    if not entry.created_at_iso:
        return False
    try:
        value = datetime.fromisoformat(entry.created_at_iso).astimezone(_SP_TZ)
    except ValueError:
        return False
    return value.date() == datetime.now(_SP_TZ).date()


def _detail_dialog(entry: AuditEntry) -> None:
    with ui.dialog() as dialog, ui.card().classes("portal-audit-dialog"):
        with ui.row().classes("portal-audit-dialog-head"):
            with ui.element("div").classes("portal-audit-dialog-icon"):
                ui.icon("manage_history")
            with ui.column().classes("portal-audit-dialog-title-copy"):
                ui.label("REGISTRO DE AUDITORIA").classes("portal-section-kicker")
                ui.label(entry.action).classes("portal-audit-dialog-title")
                ui.label(
                    f"{entry.entity_label} · {entry.created_at}"
                ).classes("portal-audit-dialog-subtitle")
            ui.button(
                icon="close",
                on_click=dialog.close,
            ).props("flat round dense").classes("portal-audit-dialog-close")

        with ui.element("div").classes("portal-audit-dialog-meta-grid"):
            for label, value in (
                ("Responsável", entry.actor_name),
                ("E-mail", entry.actor_email or "Não informado"),
                ("Entidade", entry.entity_label),
                ("ID do registro", entry.entity_id or "Não informado"),
            ):
                with ui.column().classes("portal-audit-dialog-meta"):
                    ui.label(label).classes("portal-audit-dialog-meta-label")
                    ui.label(value).classes("portal-audit-dialog-meta-value")

        if entry.description:
            with ui.element("div").classes("portal-audit-dialog-description"):
                ui.label("Descrição").classes("portal-audit-dialog-section-label")
                ui.label(entry.description)

        if entry.before_json or entry.after_json:
            with ui.element("div").classes("portal-audit-diff-grid"):
                with ui.element("section").classes("portal-audit-diff-card"):
                    ui.label("ANTES").classes("portal-audit-dialog-section-label")
                    if entry.before_json:
                        ui.code(entry.before_json).classes("portal-audit-code")
                    else:
                        ui.label("Sem estado anterior registrado.").classes(
                            "portal-audit-empty-copy"
                        )

                with ui.element("section").classes("portal-audit-diff-card"):
                    ui.label("DEPOIS").classes("portal-audit-dialog-section-label")
                    if entry.after_json:
                        ui.code(entry.after_json).classes("portal-audit-code")
                    else:
                        ui.label("Sem estado posterior registrado.").classes(
                            "portal-audit-empty-copy"
                        )

        with ui.row().classes("portal-audit-dialog-security"):
            ui.icon("shield")
            ui.label(
                "Campos sensíveis, como senhas, tokens e segredos, são ocultados "
                "automaticamente nesta visualização."
            )

    dialog.open()


def _audit_row(entry: AuditEntry) -> None:
    with ui.button(
        on_click=lambda item=entry: _detail_dialog(item),
    ).props("flat no-caps").classes("portal-audit-row"):
        with ui.element("div").classes("portal-audit-row-avatar"):
            ui.label(_initials(entry.actor_name))

        with ui.column().classes("portal-audit-row-main"):
            with ui.row().classes("portal-audit-row-title-line"):
                ui.label(entry.action).classes("portal-audit-row-action")
                ui.label(entry.entity_label).classes("portal-audit-row-entity")

            if entry.description:
                ui.label(entry.description).classes("portal-audit-row-description")

            ui.label(
                entry.actor_email or entry.actor_name
            ).classes("portal-audit-row-actor")

        with ui.column().classes("portal-audit-row-time"):
            ui.label(entry.created_at).classes("portal-audit-row-date")
            ui.icon("chevron_right").classes("portal-audit-row-chevron")


def render_admin_auditoria(user: dict) -> None:
    data = get_audit_data()

    today_count = sum(1 for entry in data.entries if _is_today(entry))
    actor_count = len({entry.actor_id for entry in data.entries if entry.actor_id})
    entity_count = len({entry.entity for entry in data.entries})

    with portal_layout(
        user=user,
        active="admin",
        page_eyebrow="ADMINISTRAÇÃO · RASTREABILIDADE",
        page_title="Auditoria do Portal",
        page_description=(
            "Consulte alterações administrativas, responsáveis, datas e estados "
            "registrados antes e depois de cada mudança."
        ),
    ):
        with ui.element("section").classes("portal-audit-overview"):
            with ui.column().classes("portal-audit-overview-copy"):
                ui.label("TRILHA DE AUDITORIA").classes("portal-section-kicker")
                ui.label(
                    "Cada mudança importante deixa um rastro."
                ).classes("portal-audit-overview-title")
                ui.label(
                    "A auditoria ajuda a entender quem alterou, o que foi modificado "
                    "e quando a ação aconteceu — sem expor conteúdo sensível."
                ).classes("portal-audit-overview-description")

            with ui.row().classes("portal-audit-overview-stats"):
                for value, label in (
                    (len(data.entries), "eventos carregados"),
                    (today_count, "eventos hoje"),
                    (actor_count, "responsáveis"),
                    (entity_count, "áreas auditadas"),
                ):
                    with ui.column().classes("portal-audit-overview-stat"):
                        ui.label(str(value)).classes("portal-audit-overview-value")
                        ui.label(label).classes("portal-audit-overview-label")

        with ui.element("section").classes("portal-audit-toolbar"):
            search = ui.input(
                placeholder="Buscar por ação, usuário, entidade ou descrição..."
            ).props("outlined dense clearable").classes("portal-audit-search")

            action = ui.select(
                ["Todas", *data.actions],
                value="Todas",
                label="Ação",
            ).props("outlined dense").classes("portal-audit-filter")

            entity_labels = {
                entry.entity: entry.entity_label
                for entry in data.entries
            }
            entity_options = {
                "Todas": "Todas as áreas",
                **{
                    entity: entity_labels.get(entity, entity)
                    for entity in data.entities
                },
            }
            entity = ui.select(
                entity_options,
                value="Todas",
                label="Área",
            ).props("outlined dense emit-value map-options").classes(
                "portal-audit-filter"
            )

            actor_options = {
                "Todos": "Todos os responsáveis",
                **{
                    item.profile_id: item.name
                    for item in data.actors
                },
            }
            actor = ui.select(
                actor_options,
                value="Todos",
                label="Responsável",
            ).props("outlined dense emit-value map-options").classes(
                "portal-audit-filter is-actor"
            )

        count_label = ui.label("").classes("portal-audit-result-count")
        results = ui.element("section").classes("portal-audit-list")

        def refresh() -> None:
            filtered = filter_audit_entries(
                data.entries,
                query=str(search.value or ""),
                action=str(action.value or "Todas"),
                entity=str(entity.value or "Todas"),
                actor_id=str(actor.value or "Todos"),
            )

            count_label.set_text(
                f"{len(filtered)} evento{'s' if len(filtered) != 1 else ''} encontrado"
                f"{'s' if len(filtered) != 1 else ''}"
            )
            results.clear()

            with results:
                if not filtered:
                    with ui.element("div").classes("portal-audit-empty"):
                        ui.icon("manage_search")
                        ui.label("Nenhum evento corresponde aos filtros.").classes(
                            "portal-audit-empty-title"
                        )
                        ui.label(
                            "Altere os filtros ou remova parte do texto pesquisado."
                        ).classes("portal-audit-empty-copy")
                    return

                for entry in filtered:
                    _audit_row(entry)

        search.on_value_change(lambda _: refresh())
        action.on_value_change(lambda _: refresh())
        entity.on_value_change(lambda _: refresh())
        actor.on_value_change(lambda _: refresh())

        refresh()

        with ui.element("section").classes("portal-audit-security-note"):
            with ui.element("div").classes("portal-audit-security-note-icon"):
                ui.icon("lock")
            with ui.column().classes("portal-audit-security-note-copy"):
                ui.label("VISUALIZAÇÃO SEGURA").classes("portal-section-kicker")
                ui.label(
                    "A auditoria nunca deve ser usada para recuperar senhas."
                ).classes("portal-audit-security-note-title")
                ui.label(
                    "A tela mascara automaticamente chaves que indiquem senha, token, "
                    "segredo, conteúdo criptografado ou credenciais técnicas."
                ).classes("portal-audit-security-note-description")

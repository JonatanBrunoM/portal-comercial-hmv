"""Aviso de comunicado recente na entrada do Portal Comercial."""
from __future__ import annotations

import logging

from nicegui import app, ui

from nicegui_app.services.comunicados_service import get_comunicados_preview

logger = logging.getLogger(__name__)


def show_latest_communication_notice(user: dict) -> None:
    """Exibe somente o comunicado publicado mais recente ainda não reconhecido."""
    try:
        items = get_comunicados_preview()
        latest = next((item for item in items if item.period_active), None)
    except Exception:
        logger.exception("Não foi possível consultar o aviso de comunicados.")
        return

    if latest is None:
        return

    user_id = str(user.get("profile_id") or user.get("email") or "anonymous")
    storage_key = f"portal_last_communication_seen:{user_id}"
    if app.storage.user.get(storage_key) == latest.communication_id:
        return

    with ui.dialog().props("persistent") as notice:
        with ui.card().classes("w-full max-w-xl p-0 overflow-hidden rounded-2xl"):
            with ui.column().classes("w-full gap-3 p-6"):
                with ui.row().classes("w-full items-center gap-2"):
                    ui.icon("campaign", size="md").classes("text-primary")
                    ui.label("NOVO COMUNICADO").classes(
                        "text-xs font-bold tracking-widest text-primary"
                    )
                ui.label(latest.title).classes("text-2xl font-bold text-slate-900")
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.badge(latest.operator_name, color="blue").props("outline")
                    if latest.priority:
                        ui.badge(f"Prioridade: {latest.priority}", color="grey").props("outline")
                ui.label(latest.content or "Confira as informações do comunicado.").classes(
                    "text-base text-slate-700 whitespace-pre-line"
                )
                if latest.audience:
                    ui.label(f"Público-alvo: {latest.audience}").classes(
                        "text-sm text-slate-500"
                    )

            def acknowledge() -> None:
                app.storage.user[storage_key] = latest.communication_id
                notice.close()

            def view_details() -> None:
                acknowledge()
                ui.navigate.to(f"/comunicados/{latest.communication_id}")

            with ui.row().classes(
                "w-full justify-end items-center gap-2 px-6 pb-6 flex-wrap"
            ):
                ui.button("Entendi", on_click=acknowledge).props(
                    "flat no-caps"
                )
                ui.button(
                    "Ver comunicado completo",
                    icon="arrow_forward",
                    on_click=view_details,
                ).props("unelevated no-caps color=primary")

    notice.open()

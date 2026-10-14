"""Banner de até três comunicados vigentes na entrada do Portal Comercial."""
from __future__ import annotations

import logging

from nicegui import app, ui

from nicegui_app.services.comunicados_service import get_comunicados_preview

logger = logging.getLogger(__name__)

_PRIORITY = {"crítica": 0, "critica": 0, "alta": 1, "normal": 2, "baixa": 3}


def show_latest_communication_notice(user: dict) -> None:
    """Apresenta até três avisos ativos, priorizados, uma vez por seleção."""
    try:
        # O repositório já entrega os comunicados em ordem de criação decrescente.
        items = [item for item in get_comunicados_preview() if item.period_active]
        # sort estável: prioridade primeiro, publicação mais recente no desempate.
        items.sort(key=lambda item: _PRIORITY.get(item.priority.strip().lower(), 2))
        selected = items[:3]
    except Exception:
        logger.exception("Não foi possível consultar os avisos de comunicados.")
        return

    if not selected:
        return

    user_id = str(user.get("profile_id") or user.get("email") or "anonymous")
    storage_key = f"portal_communications_seen_v2:{user_id}"
    selection = "|".join(item.communication_id for item in selected)
    if app.storage.user.get(storage_key) == selection:
        return

    with ui.dialog().props("persistent") as notice:
        with ui.card().classes("w-full max-w-2xl p-0 overflow-hidden rounded-2xl"):
            with ui.column().classes("w-full gap-1 px-6 pt-6 pb-3"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("campaign", size="md").classes("text-primary")
                    ui.label("COMUNICADOS EM DESTAQUE").classes(
                        "text-xs font-bold tracking-widest text-primary"
                    )
                ui.label("Avisos importantes para sua operação").classes(
                    "text-2xl font-bold text-slate-900"
                )
                ui.label(
                    f"{len(selected)} comunicado(s) vigente(s), organizados por prioridade."
                ).classes("text-sm text-slate-500")

            with ui.column().classes("w-full gap-3 px-6 pb-4").style(
                "max-height: 55vh; overflow-y: auto;"
            ):
                for item in selected:
                    with ui.element("section").classes(
                        "w-full rounded-xl border border-slate-200 p-4"
                    ):
                        with ui.row().classes("w-full items-center justify-between gap-2"):
                            ui.label(item.title).classes(
                                "text-lg font-bold text-slate-900"
                            )
                            if item.priority:
                                badge_color = (
                                    "red" if item.priority.strip().lower() in {"crítica", "critica"}
                                    else "orange" if item.priority.strip().lower() == "alta"
                                    else "blue"
                                )
                                ui.badge(item.priority, color=badge_color).props("outline")
                        ui.label(item.operator_name).classes(
                            "text-sm font-semibold text-primary"
                        )
                        ui.label(
                            item.content or "Confira as informações do comunicado."
                        ).classes("text-sm text-slate-700 whitespace-pre-line")
                        if item.audience:
                            ui.label(f"Público-alvo: {item.audience}").classes(
                                "text-xs text-slate-500"
                            )
                        ui.button(
                            "Ver comunicado completo",
                            icon="arrow_forward",
                            on_click=lambda cid=item.communication_id: view_details(cid),
                        ).props("flat no-caps").classes("mt-1")

            def acknowledge() -> None:
                app.storage.user[storage_key] = selection
                notice.close()

            def view_details(communication_id: str) -> None:
                acknowledge()
                ui.navigate.to(f"/comunicados/{communication_id}")

            with ui.row().classes(
                "w-full justify-end items-center gap-2 px-6 pb-6"
            ):
                ui.button("Entendi", icon="check", on_click=acknowledge).props(
                    "unelevated no-caps color=primary"
                )

    notice.open()

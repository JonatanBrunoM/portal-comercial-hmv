from __future__ import annotations

import logging
from datetime import date, datetime

from nicegui import ui

from nicegui_app.components.particular_mv_dialog import (
    open_particular_mv_dialog,
)
from nicegui_app.components.particular_sheet_budget_search import (
    render_particular_sheet_budget_search,
)
from nicegui_app.components.particular_sheet_budget_dialog import (
    open_particular_sheet_budget_dialog,
)
from nicegui_app.services.particular_service import (
    ParticularAccess,
    list_particular_operational_budgets,
)

logger = logging.getLogger(__name__)

PAGE_SIZE = 20


def _format_budget_date(value: object) -> str:
    if not value:
        return "—"

    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "—"


def render_particular_operational_budgets(
    *,
    access: ParticularAccess,
) -> None:
    """Exibe a consulta operacional de orçamentos do Particular."""

    if not access.can_read:
        ui.label("Você não possui acesso à consulta de orçamentos.")
        return

    search_value = ""
    current_offset = 0

    with ui.column().classes("w-full gap-4"):
        render_particular_sheet_budget_search(access=access)

        ui.label("Operação de orçamentos").classes(
            "text-xl font-semibold"
        )

        ui.label(
            "Consulte os orçamentos e abra os detalhes para conferir "
            "as informações no MV."
        ).classes("text-sm text-gray-600")

        with ui.row().classes("w-full items-end gap-3"):
            search_input = ui.input(
                label="Número do orçamento",
                placeholder="Ex.: 84600",
            ).props("clearable").classes("w-64")

            search_button = ui.button(
                "Buscar",
                icon="search",
            )

        result_label = ui.label("").classes("text-sm text-gray-600")

        results_container = ui.column().classes("w-full gap-2")

        with ui.row().classes("items-center gap-3"):
            previous_button = ui.button(
                "Anterior",
                icon="chevron_left",
            ).props("outline")

            page_label = ui.label("Página 1")

            next_button = ui.button(
                "Próxima",
                icon="chevron_right",
            ).props("outline")

    def load_page() -> None:
        nonlocal current_offset

        previous_button.disable()
        next_button.disable()
        results_container.clear()
        result_label.set_text("Carregando orçamentos...")

        try:
            result = list_particular_operational_budgets(
                access=access,
                budget_number=search_value or None,
                limit=PAGE_SIZE,
                offset=current_offset,
            )

            rows = result["rows"]
            total = result["total"]

        except Exception:
            logger.exception(
                "Falha ao consultar a listagem operacional do Particular."
            )
            result_label.set_text(
                "Não foi possível carregar os orçamentos."
            )
            page_label.set_text("—")
            ui.notify(
                "Não foi possível consultar os orçamentos.",
                type="negative",
            )
            return

        result_label.set_text(
            f"{total} orçamento(s) encontrado(s)."
        )

        page_number = (current_offset // PAGE_SIZE) + 1
        total_pages = max(
            1,
            (total + PAGE_SIZE - 1) // PAGE_SIZE,
        )
        page_label.set_text(
            f"Página {page_number} de {total_pages}"
        )

        with results_container:
            if not rows:
                ui.label(
                    "Nenhum orçamento encontrado."
                ).classes("text-gray-600")
            else:
                with ui.row().classes(
                    "w-full items-center gap-3 "
                    "rounded-lg bg-gray-100 p-3 font-semibold"
                ):
                    ui.label("Orçamento").classes("w-40")
                    ui.label("Data de confecção").classes("w-48")
                    ui.label("Ação")

                for budget in rows:
                    budget_id = str(budget["id"])
                    budget_number = str(budget["budget_number"])
                    budget_date = _format_budget_date(
                        budget.get("budget_date")
                    )

                    with ui.row().classes(
                        "w-full items-center gap-3 "
                        "rounded-lg border p-3"
                    ):
                        ui.label(budget_number).classes("w-40")
                        ui.label(budget_date).classes("w-48")

                        ui.button(
                            "Abrir detalhes",
                            icon="open_in_new",
                            on_click=lambda _=None, bid=budget_id: (
                                open_particular_mv_dialog(
                                    access=access,
                                    budget_id=bid,
                                )
                            ),
                        ).props("outline")

                        ui.button(
                            "Consultar nas grades",
                            icon="table_view",
                            on_click=lambda _=None, number=budget_number: (
                                open_particular_sheet_budget_dialog(
                                    access=access,
                                    budget_number=number,
                                )
                            ),
                        ).props("outline")

        if current_offset > 0:
            previous_button.enable()

        if current_offset + PAGE_SIZE < total:
            next_button.enable()

    def search() -> None:
        nonlocal search_value, current_offset

        candidate = str(search_input.value or "").strip()

        if candidate and (
            not candidate.isascii()
            or not candidate.isdecimal()
        ):
            ui.notify(
                "Informe somente números na busca por orçamento.",
                type="warning",
            )
            return

        search_value = candidate
        current_offset = 0
        load_page()

    def previous_page() -> None:
        nonlocal current_offset

        if current_offset < PAGE_SIZE:
            return

        current_offset -= PAGE_SIZE
        load_page()

    def next_page() -> None:
        nonlocal current_offset

        current_offset += PAGE_SIZE
        load_page()

    search_button.on("click", search)
    search_input.on("keydown.enter", search)
    previous_button.on("click", previous_page)
    next_button.on("click", next_page)

    load_page()
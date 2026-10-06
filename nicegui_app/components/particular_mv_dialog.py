from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from nicegui import run, ui

from nicegui_app.services.particular_service import (
    get_particular_mv_check_context,
    register_particular_mv_check,
)

logger = logging.getLogger(__name__)

OUTCOME_OPTIONS = {
    "PENDING": "Pendente",
    "REALIZED": "Realizado",
    "NOT_PERFORMED": "Não realizado",
    "CANCELLED": "Cancelado",
}


def _text(value: Any) -> str:
    return "—" if value is None or str(value).strip() == "" else str(value).strip()


def _money(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _text(value)
    return "R$ " + f"{amount:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def open_particular_mv_dialog(
    *,
    access: Any,
    budget_id: str,
    attendance_number: str | None = None,
    notice_number: str | None = None,
    on_saved: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Conferência operacional compacta no MV; detalhes técnicos ficam na auditoria."""
    try:
        context = get_particular_mv_check_context(access=access, budget_id=budget_id)
    except Exception:
        logger.exception("Falha ao carregar a conferência MV.")
        ui.notify("Não foi possível carregar a conferência MV.", type="negative")
        return

    budget = context["budget"]
    latest = context.get("latest_mv_check") or {}
    can_register = access.can_write and str(access.module_role).upper() == "MANAGER"

    prefill_attendance = str(
        attendance_number or latest.get("attendance_number") or ""
    ).strip()
    prefill_notice = str(notice_number or latest.get("notice_number") or "").strip()

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[650px] p-0"):
        with ui.row().classes("w-full items-start justify-between px-5 py-4"):
            with ui.column().classes("gap-0"):
                ui.label("CONFERÊNCIA MV").classes("text-caption text-weight-bold text-primary")
                ui.label(f'Orçamento #{_text(budget.get("budget_number"))}').classes("text-h6 text-weight-bold")
                if prefill_attendance:
                    ui.label(f"Atendimento {prefill_attendance}").classes("text-body2 text-grey-7")
            ui.button(icon="close", on_click=dialog.close).props("flat round")
        ui.separator()

        with ui.column().classes("w-full p-5 gap-4"):
            if latest:
                with ui.element("div").classes("w-full bg-grey-2 rounded p-3"):
                    ui.label("Última conferência").classes("text-caption text-grey-6")
                    ui.label(OUTCOME_OPTIONS.get(str(latest.get("outcome")), _text(latest.get("outcome")))).classes(
                        "text-body2 text-weight-bold"
                    )
                    if latest.get("account_value") is not None:
                        ui.label(f'Valor registrado: {_money(latest.get("account_value"))}').classes("text-caption text-grey-7")

            if not can_register:
                ui.label("O registro de conferências é restrito aos gestores.").classes("text-body2 text-grey-7")
                with ui.row().classes("w-full justify-end"):
                    ui.button("Fechar", on_click=dialog.close).props("flat no-caps")
                dialog.open()
                return

            ui.label("O que foi encontrado no MV?").classes("text-subtitle1 text-weight-bold")
            outcome = ui.select(
                options=OUTCOME_OPTIONS,
                label="Resultado da conferência",
                value="PENDING",
            ).props("outlined dense").classes("w-full")

            account_value = ui.input(
                label="Valor da conta",
                placeholder="Ex.: 4989,60",
            ).props("outlined dense prefix=R$").classes("w-full")

            notes = ui.textarea(
                label="Observação",
                placeholder="Registre somente o necessário para sustentar a conferência.",
            ).props("outlined autogrow").classes("w-full")

            with ui.expansion("Identificação", icon="tag").classes("w-full border rounded-lg"):
                with ui.column().classes("w-full p-3 gap-3"):
                    attendance = ui.input(
                        label="Atendimento",
                        value=prefill_attendance,
                    ).props("outlined dense").classes("w-full")
                    notice = ui.input(
                        label="Aviso",
                        value=prefill_notice,
                    ).props("outlined dense").classes("w-full")

            saving = False

            async def save_check() -> None:
                nonlocal saving
                if saving:
                    return

                raw_amount = str(account_value.value or "").strip()
                normalized_amount = None
                if raw_amount:
                    try:
                        amount = Decimal(raw_amount.replace(".", "").replace(",", "."))
                    except InvalidOperation:
                        ui.notify("Informe um valor válido.", type="warning")
                        return
                    if not amount.is_finite() or amount < 0:
                        ui.notify("O valor deve ser válido e não negativo.", type="warning")
                        return
                    normalized_amount = str(amount)

                saving = True
                save_button.disable()
                try:
                    check_id = await run.io_bound(
                        register_particular_mv_check,
                        access=access,
                        budget_id=budget_id,
                        outcome=str(outcome.value or "PENDING"),
                        notice_number=str(notice.value or "").strip() or None,
                        attendance_number=str(attendance.value or "").strip() or None,
                        account_value=normalized_amount,
                        notes=str(notes.value or "").strip() or None,
                    )
                except Exception:
                    logger.exception("Falha ao registrar conferência MV.")
                    saving = False
                    save_button.enable()
                    ui.notify("Não foi possível registrar a conferência.", type="negative")
                    return

                ui.notify("Conferência registrada.", type="positive")
                dialog.close()
                if on_saved:
                    on_saved({
                        "check_id": check_id,
                        "outcome": str(outcome.value or "PENDING"),
                        "account_value": normalized_amount,
                        "attendance_number": str(attendance.value or "").strip() or None,
                        "notice_number": str(notice.value or "").strip() or None,
                        "notes": str(notes.value or "").strip() or None,
                    })

            with ui.row().classes("w-full items-center justify-between gap-2"):
                ui.label("Registre uma vez; o motor reutiliza esta conferência na decisão do caso.").classes(
                    "text-caption text-grey-6"
                )
                save_button = ui.button(
                    "Salvar conferência", icon="save", on_click=save_check
                ).props("unelevated no-caps")
    dialog.open()

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
    review_reason: str | None = None,
    closure_mode: str | None = None,
    on_saved: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Registro operacional da conclusão; a evidência técnica do MV permanece auditável."""
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
    normalized_reason = str(review_reason or "").strip().upper()
    normalized_closure_mode = str(closure_mode or "").strip().upper()
    inferred_closure = normalized_reason == "VALIDAR_VALOR_FINAL" and normalized_closure_mode in {"HIGHER", "LOWER"}

    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-[600px] p-0 gap-0 overflow-hidden"
    ).style("border-radius:18px; box-shadow:0 24px 80px rgba(9,38,60,.20)"):
        with ui.column().classes("w-full px-6 pt-5 pb-4 gap-2").style(
            "background:linear-gradient(120deg,#f5faff,#fff);border-bottom:1px solid #e3ebf2"
        ):
            with ui.row().classes("w-full items-start justify-between no-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("CENTRAL DE INTELIGÊNCIA  /  REGISTRO RÁPIDO").classes(
                        "text-caption text-weight-bold text-primary"
                    )
                    ui.label(f'Orçamento #{_text(budget.get("budget_number"))}').classes(
                        "text-h5 text-weight-bold"
                    ).style("color:#12374d")
                ui.button(icon="close", on_click=dialog.close).props(
                    "flat round dense color=grey-7"
                )
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                if prefill_attendance:
                    ui.badge(f"Atendimento {prefill_attendance}").props(
                        "outline color=primary"
                    )
                if prefill_notice:
                    ui.badge(f"Aviso {prefill_notice}").props("outline color=primary")

        with ui.column().classes("w-full px-6 py-5 gap-4"):
            if latest:
                with ui.row().classes("w-full items-center gap-3 px-3 py-2 rounded-lg").style(
                    "background:#f0f6fb;border:1px solid #e0ebf5"
                ):
                    ui.icon("history", size="19px").classes("text-primary")
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label("Última conferência").classes("text-caption text-grey-7")
                        ui.label(
                            OUTCOME_OPTIONS.get(
                                str(latest.get("outcome")),
                                _text(latest.get("outcome")),
                            )
                        ).classes("text-body2 text-weight-bold")
                    if latest.get("account_value") is not None:
                        ui.label(_money(latest.get("account_value"))).classes(
                            "text-body2 text-weight-bold"
                        )

            if not can_register:
                ui.label("O registro da conclusão é restrito aos gestores.").classes(
                    "text-body2 text-grey-7"
                )
                with ui.row().classes("w-full justify-end"):
                    ui.button("Fechar", on_click=dialog.close).props("flat no-caps")
                dialog.open()
                return

            ui.label("DESFECHO DA CONFERÊNCIA").classes(
                "text-caption text-weight-bold text-primary"
            )
            if inferred_closure:
                closure_label = (
                    "Fechamento a maior"
                    if normalized_closure_mode == "HIGHER"
                    else "Fechamento a menor"
                )
                with ui.row().classes("w-full items-center gap-2 px-3 py-3 rounded-lg").style(
                    "background:#edf7ff;border:1px solid #d7e9f7"
                ):
                    ui.icon("verified", size="20px").classes("text-primary")
                    ui.label(closure_label).classes("text-body1 text-weight-bold")
                outcome = None
            else:
                outcome = ui.select(
                    options=OUTCOME_OPTIONS,
                    label="Desfecho confirmado no MV",
                    value="PENDING",
                ).props("outlined dense").classes("w-full")

            account_value = ui.input(
                label="Valor final confirmado no MV" if inferred_closure else "Valor da conta (se confirmado)",
                placeholder="Ex.: 4989,60",
            ).props("outlined dense prefix=R$").classes("w-full")

            notes = ui.textarea(
                label="Observação da conferência",
                placeholder="Descreva brevemente a evidência que sustenta o registro.",
            ).props("outlined autogrow rows=2").classes("w-full")

            with ui.expansion("Conferir identificação", icon="badge").classes(
                "w-full rounded-lg"
            ).style("border:1px solid #e0e9f2"):
                with ui.row().classes("w-full p-3 gap-3 flex-wrap"):
                    attendance = ui.input(
                        label="Atendimento",
                        value=prefill_attendance,
                    ).props("outlined dense").classes("flex-1 min-w-[170px]")
                    notice = ui.input(
                        label="Aviso",
                        value=prefill_notice,
                    ).props("outlined dense").classes("flex-1 min-w-[170px]")

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

                if inferred_closure and normalized_amount is None:
                    ui.notify("Informe o valor final confirmado no MV.", type="warning")
                    return

                resolved_outcome = "REALIZED" if inferred_closure else str(outcome.value or "PENDING")

                saving = True
                save_button.disable()
                try:
                    check_id = await run.io_bound(
                        register_particular_mv_check,
                        access=access,
                        budget_id=budget_id,
                        outcome=resolved_outcome,
                        notice_number=str(notice.value or "").strip() or None,
                        attendance_number=str(attendance.value or "").strip() or None,
                        account_value=normalized_amount,
                        notes=str(notes.value or "").strip() or None,
                    )
                except Exception:
                    logger.exception("Falha ao registrar conferência MV.")
                    saving = False
                    save_button.enable()
                    ui.notify("Não foi possível registrar a conclusão.", type="negative")
                    return

                ui.notify("Conclusão registrada.", type="positive")
                dialog.close()
                if on_saved:
                    on_saved({
                        "check_id": check_id,
                        "outcome": resolved_outcome,
                        "account_value": normalized_amount,
                        "attendance_number": str(attendance.value or "").strip() or None,
                        "notice_number": str(notice.value or "").strip() or None,
                        "notes": str(notes.value or "").strip() or None,
                    })

            ui.separator().classes("mt-1")
            with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                ui.label("Registro auditável. Confirme apenas informações verificadas no MV.").classes(
                    "text-caption text-grey-7 flex-1"
                )
                save_button = ui.button(
                    "Registrar conclusão", icon="task_alt", on_click=save_check
                ).props("unelevated no-caps color=primary").classes("px-5")
    dialog.open()

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

    ui.add_css("""
    .mv-outcome-cards .q-option-group {
        display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;width:100%;
    }
    .mv-outcome-cards .q-radio {
        min-height:86px;display:flex;flex-direction:column;justify-content:center;
        gap:7px;margin:0!important;padding:12px 6px;border:1px solid #dbe6ef;
        border-radius:14px;background:white;transition:all .16s ease;
        box-shadow:0 3px 12px rgba(20,54,76,.04);
    }
    .mv-outcome-cards .q-radio:has(.q-radio__inner--truthy) {
        background:#e7f4ff;border-color:#1985ca;
        box-shadow:0 0 0 2px rgba(25,133,202,.12);
    }
    .mv-outcome-cards .q-radio__label {
        font-weight:650;font-size:13px;color:#173b53;text-align:center;padding:0;
    }
    @media(max-width:600px) {
        .mv-outcome-cards .q-option-group {grid-template-columns:repeat(2,minmax(0,1fr))}
    }
    """)
    # Layout orientado à decisão: cartões selecionáveis substituem o dropdown.
    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-[720px] p-0 gap-0 overflow-hidden"
    ).style("border-radius:24px; box-shadow:0 32px 90px rgba(6,32,54,.28)"):
        with ui.column().classes("w-full px-7 pt-6 pb-5 gap-3").style(
            "background:linear-gradient(120deg,#073a60,#006eaa);color:white"
        ):
            with ui.row().classes("w-full items-start justify-between no-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("COMERCIAL PARTICULAR  /  CONCLUSÃO RÁPIDA").classes(
                        "text-caption text-weight-bold"
                    ).style("color:#b8e4ff;letter-spacing:.09em")
                    ui.label(f'Orçamento #{_text(budget.get("budget_number"))}').classes(
                        "text-h5 text-weight-bold"
                    ).style("color:white")
                    ui.label("Registre o resultado verificado no sistema MV").classes(
                        "text-body2"
                    ).style("color:#d9efff")
                ui.button(icon="close", on_click=dialog.close).props(
                    "flat round dense text-color=white"
                )
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                if prefill_attendance:
                    ui.label(f"Atendimento {prefill_attendance}").classes(
                        "px-3 py-1 rounded-full text-caption"
                    ).style("background:rgba(255,255,255,.15);color:white")
                if prefill_notice:
                    ui.label(f"Aviso {prefill_notice}").classes(
                        "px-3 py-1 rounded-full text-caption"
                    ).style("background:rgba(255,255,255,.15);color:white")

        with ui.column().classes("w-full px-7 py-6 gap-5").style("background:#f7fafc"):
            if latest:
                with ui.row().classes("w-full items-center gap-3 px-4 py-3 rounded-xl").style(
                    "background:#eaf3fa;border:1px solid #d6e6f3"
                ):
                    ui.icon("history", size="20px").style("color:#2676ad")
                    ui.label("Último registro:").classes("text-body2 text-grey-7")
                    ui.label(
                        OUTCOME_OPTIONS.get(
                            str(latest.get("outcome")),
                            _text(latest.get("outcome")),
                        )
                    ).classes("text-body2 text-weight-bold")
                    if latest.get("account_value") is not None:
                        ui.label(_money(latest.get("account_value"))).classes(
                            "text-body2 text-weight-bold ml-auto"
                        )

            if not can_register:
                ui.label("O registro da conclusão é restrito aos gestores.").classes(
                    "text-body2 text-grey-7"
                )
                with ui.row().classes("w-full justify-end"):
                    ui.button("Fechar", on_click=dialog.close).props("flat no-caps")
                dialog.open()
                return

            with ui.column().classes("w-full gap-1"):
                ui.label("Qual é a situação confirmada?").classes(
                    "text-subtitle1 text-weight-bold"
                ).style("color:#12374d")
                ui.label("Selecione o resultado identificado no MV.").classes(
                    "text-body2 text-grey-7"
                )

            if inferred_closure:
                closure_label = (
                    "Fechamento a maior"
                    if normalized_closure_mode == "HIGHER"
                    else "Fechamento a menor"
                )
                with ui.row().classes("w-full items-center gap-3 p-4 rounded-xl").style(
                    "background:#e8f4ff;border:1px solid #a9d1f1"
                ):
                    ui.icon("verified", size="24px").style("color:#006eaa")
                    ui.label(closure_label).classes("text-body1 text-weight-bold")
                outcome = None
            else:
                outcome = ui.radio(
                    options=OUTCOME_OPTIONS,
                    value="PENDING",
                ).props("inline").classes("mv-outcome-cards w-full")

            with ui.row().classes("w-full items-start gap-4 flex-wrap"):
                with ui.column().classes("flex-1 min-w-[220px] gap-1"):
                    ui.label("Valor da conta").classes(
                        "text-body2 text-weight-medium"
                    ).style("color:#173b53")
                    account_value = ui.input(
                        placeholder="Ex.: 4.989,60",
                    ).props("outlined prefix=R$ bg-color=white").classes("w-full")
                with ui.column().classes("flex-[2] min-w-[260px] gap-1"):
                    ui.label("Observação da conferência").classes(
                        "text-body2 text-weight-medium"
                    ).style("color:#173b53")
                    notes = ui.textarea(
                        placeholder="O que foi confirmado no MV?",
                    ).props("outlined rows=2 bg-color=white").classes("w-full")

            with ui.expansion("Dados de identificação", icon="badge").classes(
                "w-full rounded-xl"
            ).style("background:white;border:1px solid #dce8f2"):
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

            with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap pt-3").style(
                "border-top:1px solid #dbe6ef"
            ):
                ui.label("Registre somente informações confirmadas.").classes(
                    "text-caption text-grey-7 flex-1"
                )
                save_button = ui.button(
                    "Confirmar registro", icon="check_circle", on_click=save_check
                ).props("unelevated no-caps color=primary size=lg").classes(
                    "px-6 rounded-xl"
                )
    dialog.open()

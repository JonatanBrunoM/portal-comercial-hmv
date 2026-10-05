from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from nicegui import run, ui

from nicegui_app.services.particular_service import ParticularAccess, resolve_particular_account_review

logger = logging.getLogger(__name__)


def open_account_resolution_dialog(
    *,
    access: ParticularAccess,
    budget_id: str,
    budget_number: Any,
    on_resolved: Callable[[], None] | None = None,
) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[620px] p-0"):
        with ui.row().classes("w-full items-center justify-between px-5 py-4"):
            with ui.column().classes("gap-0"):
                ui.label("CONCLUIR VERIFICAÇÃO").classes("text-caption text-weight-bold text-primary")
                ui.label(f"Orçamento #{budget_number}").classes("text-h6 text-weight-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round")
        ui.separator()
        with ui.column().classes("w-full p-5 gap-3"):
            ui.label(
                "Registre somente o que foi confirmado. A conclusão ficará preservada para auditoria."
            ).classes("text-body2 text-grey-7")

            status = ui.select(
                {
                    "CLOSED": "Conta fechada",
                    "REOPENED": "Conta reaberta",
                    "SPECIAL_OUTCOME": "Outro desfecho confirmado",
                    "INCONCLUSIVE": "Permanece inconclusivo",
                },
                label="Conclusão",
            ).props("outlined dense").classes("w-full")

            closure = ui.select(
                {
                    "ACCORDING_TO_BUDGET": "Conforme orçamento",
                    "HIGHER": "Fechada a maior",
                    "LOWER": "Fechada a menor",
                    "WITH_ADJUSTMENT": "Fechada com ajuste",
                    "OTHER": "Outro modo de fechamento",
                },
                label="Como foi fechada",
            ).props("outlined dense").classes("w-full")

            final_value = ui.input(
                label="Valor final confirmado", placeholder="Ex.: 4989,60"
            ).props("outlined dense").classes("w-full")

            notes = ui.textarea(
                label="Observação da verificação",
                placeholder="Descreva objetivamente o que foi confirmado.",
            ).props("outlined autogrow").classes("w-full")

            def sync_fields() -> None:
                closed = status.value == "CLOSED"
                closure.set_visibility(closed)
                final_value.set_visibility(closed and closure.value in {"HIGHER", "LOWER"})

            status.on("update:model-value", lambda _: sync_fields())
            closure.on("update:model-value", lambda _: sync_fields())
            sync_fields()

            saving = False

            async def save() -> None:
                nonlocal saving
                if saving:
                    return
                selected_status = str(status.value or "").strip()
                selected_mode = str(closure.value or "").strip() or None
                raw_value = str(final_value.value or "").strip()
                observation = str(notes.value or "").strip()

                if not selected_status:
                    ui.notify("Selecione a conclusão.", type="warning")
                    return
                if selected_status == "CLOSED" and not selected_mode:
                    ui.notify("Informe como a conta foi fechada.", type="warning")
                    return
                if selected_mode in {"HIGHER", "LOWER"} and not raw_value:
                    ui.notify("Informe o valor final confirmado.", type="warning")
                    return
                normalized_value = None
                if raw_value:
                    try:
                        amount = Decimal(raw_value.replace(".", "").replace(",", "."))
                    except InvalidOperation:
                        ui.notify("Informe um valor final válido.", type="warning")
                        return
                    if not amount.is_finite() or amount < 0:
                        ui.notify("O valor final deve ser válido e não negativo.", type="warning")
                        return
                    normalized_value = str(amount)
                if not observation:
                    ui.notify("A observação da verificação é obrigatória.", type="warning")
                    return

                saving = True
                save_button.disable()
                try:
                    await run.io_bound(
                        resolve_particular_account_review,
                        access=access,
                        budget_id=budget_id,
                        account_status=selected_status,
                        closure_mode=selected_mode if selected_status == "CLOSED" else None,
                        confirmed_final_value=normalized_value if selected_status == "CLOSED" else None,
                        resolution_notes=observation,
                    )
                except Exception:
                    logger.exception("Falha ao concluir revisão de conta.")
                    saving = False
                    save_button.enable()
                    ui.notify("Não foi possível concluir a revisão.", type="negative")
                    return

                ui.notify("Revisão concluída e registrada.", type="positive")
                dialog.close()
                if on_resolved:
                    on_resolved()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
                save_button = ui.button("Concluir revisão", icon="task_alt", on_click=save).props("unelevated no-caps")
    dialog.open()

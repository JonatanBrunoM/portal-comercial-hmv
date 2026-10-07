from __future__ import annotations

import logging
from typing import Any, Callable

from nicegui import run, ui

from nicegui_app.services.particular_service import (
    ParticularAccess,
    conclude_particular_investigation_relation,
)

logger = logging.getLogger(__name__)


def open_particular_investigation_dialog(
    *,
    access: ParticularAccess,
    budget_id: str,
    budget_number: Any,
    candidates: list[dict[str, Any]],
    on_resolved: Callable[[], None] | None = None,
) -> None:
    related_options: dict[str, str] = {}
    for candidate in candidates:
        related = candidate.get("related_budget") or {}
        related_id = str(related.get("budget_id") or "").strip()
        related_number = str(related.get("budget_number") or "").strip()
        if related_id and related_number:
            related_options[related_id] = f"Orçamento #{related_number}"

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[650px] p-0"):
        with ui.row().classes("w-full items-center justify-between px-5 py-4"):
            with ui.column().classes("gap-0"):
                ui.label("CONCLUIR INVESTIGAÇÃO").classes(
                    "text-caption text-weight-bold text-primary"
                )
                ui.label(f"Orçamento #{budget_number}").classes("text-h6 text-weight-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round")
        ui.separator()

        with ui.column().classes("w-full p-5 gap-3"):
            ui.label(
                "Registre a relação que foi confirmada durante a investigação. "
                "Os indícios encontrados pelo motor permanecem preservados como evidência."
            ).classes("text-body2 text-grey-7")

            if not related_options:
                ui.label(
                    "Nenhum dos indícios possui um orçamento relacionado disponível para conclusão."
                ).classes("text-body2 text-negative")
                with ui.row().classes("w-full justify-end"):
                    ui.button("Fechar", on_click=dialog.close).props("flat no-caps")
                dialog.open()
                return

            related_budget = ui.select(
                related_options,
                label="Orçamento relacionado",
            ).props("outlined dense").classes("w-full")

            if len(related_options) == 1:
                related_budget.value = next(iter(related_options))

            outcome = ui.select(
                {
                    "REBUDGET": "Orçamento substituído / reorçado",
                    "DISTINCT": "Sem relação com o orçamento investigado",
                },
                label="Conclusão",
            ).props("outlined dense").classes("w-full")

            ui.label("O que mudou?").classes("text-body2 text-weight-bold mt-1")
            ui.label(
                "Marque todas as alterações confirmadas entre o orçamento original e o relacionado."
            ).classes("text-caption text-grey-7")

            procedure_changed = ui.checkbox("Procedimento")
            doctor_changed = ui.checkbox("Médico")
            value_changed = ui.checkbox("Valor")
            date_changed = ui.checkbox("Data")

            notes = ui.textarea(
                label="Justificativa da investigação",
                placeholder=(
                    "Ex.: orçamento substituído após alteração do procedimento; "
                    "a grade passou a referenciar o novo orçamento."
                ),
            ).props("outlined autogrow").classes("w-full")

            def sync_fields() -> None:
                is_rebudget = outcome.value == "REBUDGET"
                for field in (
                    procedure_changed,
                    doctor_changed,
                    value_changed,
                    date_changed,
                ):
                    field.set_visibility(is_rebudget)

            outcome.on("update:model-value", lambda _: sync_fields())
            sync_fields()

            saving = False

            async def save() -> None:
                nonlocal saving
                if saving:
                    return

                related_id = str(related_budget.value or "").strip()
                decision = str(outcome.value or "").strip().upper()
                reason = str(notes.value or "").strip()

                if not related_id:
                    ui.notify("Selecione o orçamento relacionado.", type="warning")
                    return
                if decision not in {"REBUDGET", "DISTINCT"}:
                    ui.notify("Selecione a conclusão da investigação.", type="warning")
                    return
                if not reason:
                    ui.notify("A justificativa da investigação é obrigatória.", type="warning")
                    return

                dimensions: list[str] = []
                if decision == "REBUDGET":
                    if procedure_changed.value:
                        dimensions.append("PROCEDURE")
                    if doctor_changed.value:
                        dimensions.append("DOCTOR")
                    if value_changed.value:
                        dimensions.append("VALUE")
                    if date_changed.value:
                        dimensions.append("DATE")
                    if not dimensions:
                        ui.notify(
                            "Marque pelo menos uma alteração confirmada no reorçamento.",
                            type="warning",
                        )
                        return

                saving = True
                save_button.disable()
                try:
                    await run.io_bound(
                        conclude_particular_investigation_relation,
                        access=access,
                        budget_id=budget_id,
                        related_budget_id=related_id,
                        decision=decision,
                        review_reason=reason,
                        change_dimensions=dimensions,
                    )
                except Exception:
                    logger.exception("Falha ao concluir investigação operacional.")
                    saving = False
                    save_button.enable()
                    ui.notify("Não foi possível concluir a investigação.", type="negative")
                    return

                ui.notify("Investigação concluída e relação registrada.", type="positive")
                dialog.close()
                if on_resolved:
                    on_resolved()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=dialog.close).props("flat no-caps")
                save_button = ui.button(
                    "Concluir investigação",
                    icon="task_alt",
                    on_click=save,
                ).props("unelevated no-caps")

    dialog.open()


from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import ui

from nicegui_app.services.particular_service import (
    get_particular_mv_check_context,
    register_particular_mv_check,
)


OUTCOME_OPTIONS = {
    "PENDING": "Pendente",
    "REALIZED": "Realizado",
    "NOT_PERFORMED": "Não realizado",
    "CANCELLED": "Cancelado",
}


def _text(value: Any) -> str:
    if value is None:
        return "—"
    return str(value).strip() or "—"


def _money(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _text(value)

    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {formatted}"


def open_particular_mv_dialog(
    *,
    access: Any,
    budget_id: str,
) -> None:
    """Abre a conferência manual do MV para um orçamento específico."""

    try:
        context = get_particular_mv_check_context(
            access=access,
            budget_id=budget_id,
        )
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Falha ao carregar a conferência no MV"
        )

        ui.notify(
            "Não foi possível carregar os dados da conferência no MV. "
            "Consulte o terminal do Portal.",
            type="negative",
        )
        return

    budget = context["budget"]
    latest_check = context.get("latest_mv_check")
    can_register = (
        access.can_write
        and str(access.module_role).upper() == "MANAGER"
    )

    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-[900px] p-0"
    ):
        with ui.row().classes(
            "w-full items-center justify-between gap-4 p-5"
        ):
            with ui.column().classes("gap-1"):
                ui.label("CONFERÊNCIA NO MV").classes(
                    "text-caption text-weight-bold"
                )
                ui.label(
                    f'Orçamento nº {_text(budget.get("budget_number"))}'
                ).classes("text-h5 text-weight-bold")

            ui.button(
                icon="close",
                on_click=dialog.close,
            ).props("flat round")

        ui.separator()

        with ui.column().classes("w-full p-5 gap-4"):
            ui.label("Informações do orçamento").classes(
                "text-subtitle1 text-weight-bold"
            )

            with ui.grid(columns=2).classes("w-full gap-4"):
                for label, value in (
                    ("Data do orçamento", budget.get("budget_date")),
                    ("Médico", budget.get("doctor_name")),
                    ("Origem", budget.get("origin")),
                    ("Modalidade", budget.get("modality")),
                    ("Local", budget.get("location_hint")),
                    ("Situação", budget.get("state")),
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(label).classes("text-caption")
                        ui.label(_text(value)).classes(
                            "text-body2 text-weight-medium"
                        )

            ui.separator()

            ui.label("Última conferência registrada").classes(
                "text-subtitle1 text-weight-bold"
            )

            if latest_check:
                outcome_label = OUTCOME_OPTIONS.get(
                    latest_check.get("outcome"),
                    _text(latest_check.get("outcome")),
                )

                ui.label(
                    f"Resultado: {outcome_label}"
                ).classes("text-body1 text-weight-medium")

                ui.label(
                    f'Data: {_text(latest_check.get("checked_at"))}'
                ).classes("text-body2")

                ui.label(
                    f'Aviso: {_text(latest_check.get("notice_number"))}'
                ).classes("text-body2")

                ui.label(
                    "Atendimento: "
                    f'{_text(latest_check.get("attendance_number"))}'
                ).classes("text-body2")

                ui.label(
                    "Valor da conta: "
                    f'{_money(latest_check.get("account_value"))}'
                ).classes("text-body2")

                ui.label(
                    "Observações: "
                    f'{_text(latest_check.get("notes"))}'
                ).classes("text-body2")
            else:
                ui.label(
                    "Nenhuma conferência registrada para este orçamento."
                ).classes("text-body2")

            if can_register:
                ui.separator()

                ui.label("Registrar nova conferência").classes(
                    "text-subtitle1 text-weight-bold"
                )

                outcome = ui.select(
                    options=OUTCOME_OPTIONS,
                    label="Resultado da conferência",
                    value="PENDING",
                ).classes("w-full")

                notice_number = ui.input(
                    label="Número do aviso (opcional)",
                ).classes("w-full")

                attendance_number = ui.input(
                    label="Número do atendimento (opcional)",
                ).classes("w-full")

                account_value = ui.input(
                    label="Valor da conta em R$ (opcional)",
                    placeholder="Ex.: 1250,50",
                ).classes("w-full")

                notes = ui.textarea(
                    label="Observações da conferência",
                ).classes("w-full")

                # Impede envios repetidos enquanto o registro está em andamento.
                saving = False

                async def save_check() -> None:
                    nonlocal saving

                    if saving:
                        return

                    saving = True
                    save_button.disable()

                    raw_amount = str(account_value.value or "").strip()
                    normalized_amount = None

                    if raw_amount:
                        try:
                            normalized_amount = Decimal(
                                raw_amount.replace(".", "").replace(",", ".")
                            )
                        except InvalidOperation:
                            saving = False
                            save_button.enable()

                            ui.notify(
                                "Informe um valor de conta válido.",
                                type="warning",
                            )
                            return

                        if (
                            not normalized_amount.is_finite()
                            or normalized_amount < 0
                        ):
                            saving = False
                            save_button.enable()

                            ui.notify(
                                "O valor da conta deve ser um número válido "
                                "e não negativo.",
                                type="warning",
                            )
                            return

                        normalized_amount = str(normalized_amount)

                    try:
                        register_particular_mv_check(
                            access=access,
                            budget_id=budget_id,
                            outcome=outcome.value,
                            notice_number=notice_number.value,
                            attendance_number=attendance_number.value,
                            account_value=normalized_amount,
                            notes=notes.value,
                        )
                    except Exception:
                        saving = False
                        save_button.enable()

                        ui.notify(
                            "Não foi possível registrar a conferência no MV.",
                            type="negative",
                        )
                        return

                    ui.notify(
                        "Conferência registrada com sucesso.",
                        type="positive",
                    )
                    dialog.close()

                with ui.row().classes(
                    "w-full justify-end gap-3"
                ):
                    ui.button(
                        "Cancelar",
                        on_click=dialog.close,
                    ).props("flat no-caps")

                    save_button = ui.button(
                        "Registrar conferência",
                        icon="save",
                        on_click=save_check,
                    ).props("unelevated no-caps")
            else:
                ui.label(
                    "Seu perfil possui acesso de consulta. "
                    "O registro de conferências é restrito aos gestores."
                ).classes("text-caption")

    dialog.open()
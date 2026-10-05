from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_mv_dialog import open_particular_mv_dialog
from nicegui_app.components.particular_sheet_budget_dialog import open_particular_sheet_budget_dialog
from nicegui_app.services.particular_service import ParticularAccess
from nicegui_app.services.particular_work_queue import get_particular_case_dossier

logger = logging.getLogger(__name__)

_REASON = {
    "VALIDAR_VALOR_FINAL": "Confirmar o valor final da conta antes de concluir.",
    "COMPOSICAO_DIVERGENTE": "A composição registrada exige conferência humana.",
    "DEVOLUCAO_OU_ESTORNO": "Há evidência de devolução ou estorno.",
    "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": "Há ajuste registrado sem fechamento conclusivo.",
    "DESFECHO_FINANCEIRO_PENDENTE": "O desfecho financeiro ainda não está comprovado.",
    "MULTIPLOS_EVENTOS_MESMA_DATA": "Há múltiplos eventos na mesma data e não existe horário real para ordenar.",
    "SEQUENCIA_TEMPORAL_AMBIGUA": "Fechamento e reabertura aparecem na mesma data; o motor não presume a ordem.",
    "ORCAMENTO_VALOR_APROXIMADO": "O fechamento referencia orçamento de valor aproximado.",
}


def _text(value: Any) -> str:
    return "—" if value is None or str(value).strip() == "" else str(value).strip()


def _date(value: Any) -> str:
    if not value:
        return "—"
    raw = str(value)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        try:
            return date.fromisoformat(raw[:10]).strftime("%d/%m/%Y")
        except ValueError:
            return raw


def _money(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    amount = Decimal(str(value))
    return "R$ " + f"{amount:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _metric(label: str, value: str, caption: str = "") -> None:
    with ui.card().classes("flex-1 min-w-[180px] p-3 gap-0 shadow-none border"):
        ui.label(label).classes("text-caption text-grey-7")
        ui.label(value).classes("text-subtitle1 text-weight-bold")
        if caption:
            ui.label(caption).classes("text-caption text-grey-6")


def _timeline_item(icon: str, title: str, when: str, body: str, badge: str | None = None) -> None:
    with ui.row().classes("w-full gap-3 items-start no-wrap"):
        with ui.element("div").classes("rounded-full bg-blue-50 p-2 shrink-0"):
            ui.icon(icon, size="20px").classes("text-primary")
        with ui.column().classes("gap-1 flex-1 min-w-0 pb-3"):
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                ui.label(title).classes("text-body2 text-weight-bold")
                if badge:
                    ui.badge(badge).props("outline").classes("text-primary")
                ui.space()
                ui.label(when).classes("text-caption text-grey-6")
            ui.label(body).classes("text-sm text-grey-8 whitespace-pre-wrap break-words")


def open_particular_case_dossier(*, access: ParticularAccess, budget_id: str) -> None:
    if not access.can_read:
        ui.notify("Você não possui acesso ao dossiê.", type="warning")
        return

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[1180px] p-0"):
        header = ui.column().classes("w-full p-5 gap-1")
        ui.separator()
        body = ui.column().classes("w-full p-5 gap-4").style("max-height: 76vh; overflow-y: auto")
    dialog.open()

    async def load() -> None:
        with header:
            ui.label("Carregando dossiê inteligente...").classes("text-body2 text-grey-7")
        try:
            data = await run.io_bound(get_particular_case_dossier, budget_id=budget_id)
        except Exception:
            logger.exception("Falha ao carregar dossiê do Particular.")
            header.clear()
            with header:
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Não foi possível carregar o dossiê.").classes("text-subtitle1 text-weight-bold")
                    ui.button(icon="close", on_click=dialog.close).props("flat round")
            return
        if dialog.is_deleted:
            return

        row = data["queue"]
        occurrences = data["occurrences"]
        events = data["events"]
        evolutions = data["evolutions"]
        number = str(row.get("budget_number") or "")

        header.clear()
        with header:
            with ui.row().classes("w-full items-start justify-between gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("DOSSIE INTELIGENTE").classes("text-caption text-weight-bold text-primary")
                    ui.label(f"Orçamento #{number}").classes("text-h5 text-weight-bold")
                    ui.label(
                        f'{_text(row.get("doctor_name"))} · origem {_text(row.get("portfolio_origin")).title()}'
                    ).classes("text-body2 text-grey-7")
                with ui.row().classes("gap-2"):
                    ui.button(
                        "Grades", icon="table_view",
                        on_click=lambda: open_particular_sheet_budget_dialog(
                            access=access, budget_number=number,
                        ),
                    ).props("outline dense no-caps")
                    ui.button(
                        "Conferência MV", icon="fact_check",
                        on_click=lambda: open_particular_mv_dialog(
                            access=access, budget_id=budget_id,
                        ),
                    ).props("outline dense no-caps")
                    ui.button(icon="close", on_click=dialog.close).props("flat round")

        body.clear()
        with body:
            reason_code = str(row.get("account_review_reason") or row.get("work_reason") or "")
            reason = _REASON.get(reason_code, reason_code.replace("_", " ").title())
            with ui.card().classes("w-full p-4 bg-blue-50 shadow-none"):
                with ui.row().classes("w-full items-start gap-3 no-wrap"):
                    ui.icon("psychology", size="28px").classes("text-primary")
                    with ui.column().classes("gap-1"):
                        ui.label("Leitura do motor").classes("text-subtitle2 text-weight-bold")
                        ui.label(reason or "Acompanhar as evidências disponíveis.").classes("text-body2")
                        ui.label(
                            "A interpretação organiza as evidências; quando há ambiguidade, a decisão permanece humana."
                        ).classes("text-caption text-grey-7")

            with ui.row().classes("w-full gap-3 flex-wrap"):
                _metric("Valor ORIGINAL", _money(row.get("original_value")))
                _metric("Atendimento", _text(row.get("attendance_number")))
                _metric("Última data operacional observada", _date(row.get("last_observed_operational_date")))
                _metric("Fechamento", _text(row.get("account_status")).replace("_", " ").title(),
                        _text(row.get("closure_mode")).replace("_", " ").title())

            ui.label("Jornada de evidências").classes("text-subtitle1 text-weight-bold mt-2")
            _timeline_item(
                "description", "Orçamento confeccionado", _date(row.get("budget_date")),
                f'Origem: {_text(row.get("original_requester"))} · Valor ORIGINAL: {_money(row.get("original_value"))}',
                "XML",
            )

            for occ in occurrences:
                details = [
                    f'Aviso: {_text(occ.get("notice_number"))}',
                    f'Local: {_text(occ.get("location"))}',
                ]
                if occ.get("patient_confirmation"):
                    details.append(f'Confirmação: {_text(occ.get("patient_confirmation"))}')
                if occ.get("notes_original"):
                    details.append(f'Obs.: {_text(occ.get("notes_original"))}')
                _timeline_item(
                    "event", "Evidência operacional na grade", _date(occ.get("procedure_date")),
                    " · ".join(details), "GRADE",
                )

            for evo in evolutions:
                description = _text(evo.get("description_raw"))
                _timeline_item(
                    "clinical_notes", "Evolução administrativa", _date(evo.get("evolution_recorded_at")),
                    description,
                    f'Atend. {_text(evo.get("attendance_number"))}',
                )

            for event in events:
                details = event.get("interpretation_details")
                if not isinstance(details, dict):
                    details = {}
                description = str(details.get("description") or "").strip()
                review = str(event.get("review_reason") or "").strip()
                body_text = _REASON.get(review, review.replace("_", " ").title()) if review else ""
                if description and description not in [str(e.get("description_raw") or "") for e in evolutions]:
                    body_text = f"{body_text}\n{description}".strip()
                _timeline_item(
                    "account_tree",
                    _text(event.get("event_type")).replace("_", " ").title(),
                    _date(event.get("event_at")),
                    body_text or "Evento interpretado a partir da evolução administrativa.",
                    "MOTOR",
                )

            if not occurrences and not evolutions and not events:
                with ui.card().classes("w-full p-4 shadow-none border"):
                    ui.label("Nenhuma evidência adicional vinculada foi encontrada.").classes("text-body2 text-grey-7")

            ui.separator()
            with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                ui.label(
                    "Grades indicam trajetória operacional; somente evidências conclusivas sustentam fechamento."
                ).classes("text-caption text-grey-7")
                ui.button("Fechar", on_click=dialog.close).props("flat no-caps")

    ui.timer(0.05, load, once=True)

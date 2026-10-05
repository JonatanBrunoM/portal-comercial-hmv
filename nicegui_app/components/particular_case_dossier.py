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

DECISIONS = {
    "VALIDAR_VALOR_FINAL": (
        "Confirmar valor final da conta",
        "A evolução indica fechamento a maior ou a menor. O motor não assume o valor final.",
        "Conferir no MV o valor efetivamente fechado e registrar a confirmação.",
    ),
    "COMPOSICAO_DIVERGENTE": (
        "Conferir composição da conta",
        "Há evidência de item, exame ou material tratado de forma diferente do orçamento.",
        "Validar no MV a composição efetivamente faturada antes de concluir.",
    ),
    "DEVOLUCAO_OU_ESTORNO": (
        "Validar ajuste financeiro",
        "A evolução registra devolução ou estorno associado ao caso.",
        "Confirmar no MV o desfecho financeiro após o ajuste.",
    ),
    "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": (
        "Confirmar desfecho da conta",
        "Existe ajuste administrativo registrado, mas não há evidência conclusiva de fechamento posterior.",
        "Consultar o MV e confirmar a situação atual da conta.",
    ),
    "DESFECHO_FINANCEIRO_PENDENTE": (
        "Confirmar desfecho financeiro",
        "A evidência disponível ainda não comprova o fechamento da conta.",
        "Verificar no MV se houve fechamento, migração de cobrança ou outro desfecho.",
    ),
    "MULTIPLOS_EVENTOS_MESMA_DATA": (
        "Definir sequência dos eventos",
        "Existem eventos diferentes na mesma data e a fonte não possui horário real para ordená-los.",
        "Consultar o MV para identificar qual evento representa o estado atual.",
    ),
    "SEQUENCIA_TEMPORAL_AMBIGUA": (
        "Confirmar estado atual da conta",
        "Fechamento e reabertura aparecem na mesma data; o motor não presume a ordem.",
        "Consultar o MV e confirmar se a conta permanece aberta ou foi fechada novamente.",
    ),
    "ORCAMENTO_VALOR_APROXIMADO": (
        "Validar valor e fechamento",
        "O fechamento referencia orçamento de valor aproximado.",
        "Confirmar no MV o valor final antes de concluir.",
    ),
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
    with ui.column().classes("gap-0 flex-1 min-w-[170px]"):
        ui.label(label).classes("text-caption text-grey-6")
        ui.label(value).classes("text-body1 text-weight-bold")
        if caption:
            ui.label(caption).classes("text-caption text-grey-7")


def _evidence(icon: str, title: str, when: str, body: str, source: str) -> None:
    with ui.row().classes("w-full gap-3 items-start no-wrap py-2"):
        ui.icon(icon, size="20px").classes("text-primary mt-1")
        with ui.column().classes("gap-0 flex-1 min-w-0"):
            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                ui.label(title).classes("text-body2 text-weight-bold")
                ui.badge(source).props("outline").classes("text-primary")
                ui.space()
                ui.label(when).classes("text-caption text-grey-6")
            ui.label(body).classes("text-sm text-grey-8 whitespace-pre-wrap break-words")


def _decision_for(row: dict[str, Any]) -> tuple[str, str, str]:
    code = str(row.get("account_review_reason") or row.get("work_reason") or "").strip()
    if code in DECISIONS:
        return DECISIONS[code]
    group = str(row.get("work_group") or "")
    if group == "REVISAR_TRAJETORIA":
        return (
            "Revisar trajetória operacional",
            "O motor encontrou mudança ou conflito na trajetória do orçamento.",
            "Compare as evidências das grades antes de definir o desfecho.",
        )
    if group in {"GRADE_SEM_OPERACAO", "NEGATIVA_SEM_OPERACAO"}:
        return (
            "Investigar ausência de evidência",
            "A origem sugere fluxo operacional, mas nenhuma ocorrência correspondente foi encontrada.",
            "Verifique a grade e confirme se existe referência operacional ainda não identificada.",
        )
    if group == "FECHAMENTO_IDENTIFICADO":
        return (
            "Fechamento identificado",
            "A evolução administrativa fornece evidência conclusiva de fechamento.",
            "Nenhuma ação imediata é necessária; consulte as evidências se precisar auditar o caso.",
        )
    return (
        "Acompanhar caso",
        "O motor organizou as evidências disponíveis sem inferir além da fonte.",
        "Consulte a trajetória abaixo quando precisar aprofundar o caso.",
    )


def open_particular_case_dossier(*, access: ParticularAccess, budget_id: str) -> None:
    if not access.can_read:
        ui.notify("Você não possui acesso ao caso.", type="warning")
        return

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[1100px] p-0"):
        header = ui.column().classes("w-full px-6 py-5 gap-1")
        ui.separator()
        body = ui.column().classes("w-full px-6 py-5 gap-4").style("max-height: 76vh; overflow-y: auto")
    dialog.open()

    async def load() -> None:
        with header:
            ui.label("Carregando análise...").classes("text-body2 text-grey-7")
        try:
            data = await run.io_bound(get_particular_case_dossier, budget_id=budget_id)
        except Exception:
            logger.exception("Falha ao carregar dossiê do Particular.")
            header.clear()
            with header:
                ui.label("Não foi possível carregar este caso.").classes("text-subtitle1 text-weight-bold")
                ui.button(icon="close", on_click=dialog.close).props("flat round")
            return
        if dialog.is_deleted:
            return

        row = data["queue"]
        occurrences = data["occurrences"]
        events = data["events"]
        evolutions = data["evolutions"]
        number = str(row.get("budget_number") or "")
        title, why, next_action = _decision_for(row)
        needs_review = str(row.get("work_group") or "") in {"REVISAR_FECHAMENTO", "REVISAR_TRAJETORIA"}

        header.clear()
        with header:
            with ui.row().classes("w-full items-start justify-between gap-4"):
                with ui.column().classes("gap-0"):
                    ui.label("CENTRAL DE DECISAO").classes("text-caption text-weight-bold text-primary")
                    ui.label(f"Orçamento #{number}").classes("text-h5 text-weight-bold")
                    ui.label(
                        f'{_text(row.get("doctor_name"))} · origem {_text(row.get("portfolio_origin")).title()}'
                    ).classes("text-body2 text-grey-7")
                ui.button(icon="close", on_click=dialog.close).props("flat round")

        body.clear()
        with body:
            with ui.card().classes("w-full p-5 shadow-none border"):
                with ui.row().classes("w-full gap-4 items-start no-wrap"):
                    with ui.element("div").classes(
                        "rounded-full bg-red-50 p-3" if needs_review else "rounded-full bg-blue-50 p-3"
                    ):
                        ui.icon("priority_high" if needs_review else "psychology", size="27px").classes("text-primary")
                    with ui.column().classes("gap-2 flex-1"):
                        ui.label("DECISÃO NECESSÁRIA" if needs_review else "LEITURA DO MOTOR").classes(
                            "text-caption text-weight-bold text-primary"
                        )
                        ui.label(title).classes("text-h6 text-weight-bold")
                        ui.label(why).classes("text-body2 text-grey-8")
                        with ui.element("div").classes("w-full bg-grey-2 rounded p-3 mt-1"):
                            ui.label("Próxima ação").classes("text-caption text-weight-bold text-grey-7")
                            ui.label(next_action).classes("text-body2 text-weight-medium")

            with ui.card().classes("w-full p-4 shadow-none bg-grey-1"):
                with ui.row().classes("w-full gap-5 flex-wrap"):
                    _metric("Valor de referência", _money(row.get("reference_budget_value") or row.get("original_value")), "Valor ORIGINAL; não é valor final confirmado")
                    _metric("Atendimento", _text(row.get("attendance_number")))
                    _metric("Última data operacional observada", _date(row.get("last_observed_operational_date")))
                    status = _text(row.get("account_status")).replace("_", " ").title()
                    _metric("Situação da conta", status, "Interpretação atual do motor")

            with ui.row().classes("w-full gap-2 flex-wrap"):
                ui.button(
                    "Conferir no MV", icon="fact_check",
                    on_click=lambda: open_particular_mv_dialog(access=access, budget_id=budget_id),
                ).props("unelevated no-caps")
                ui.button(
                    "Consultar grades", icon="table_view",
                    on_click=lambda: open_particular_sheet_budget_dialog(access=access, budget_number=number),
                ).props("outline no-caps")

            with ui.expansion("Evidências que sustentam esta leitura", icon="fact_check").classes(
                "w-full border rounded-lg"
            ):
                with ui.column().classes("w-full p-3 gap-1"):
                    _evidence(
                        "description", "Orçamento confeccionado", _date(row.get("budget_date")),
                        f'Origem: {_text(row.get("original_requester"))} · Valor ORIGINAL: {_money(row.get("original_value"))}',
                        "XML",
                    )
                    for occ in occurrences:
                        parts = [f'Aviso: {_text(occ.get("notice_number"))}', f'Local: {_text(occ.get("location"))}']
                        if occ.get("patient_confirmation"):
                            parts.append(f'Confirmação: {_text(occ.get("patient_confirmation"))}')
                        if occ.get("notes_original"):
                            parts.append(f'Obs.: {_text(occ.get("notes_original"))}')
                        _evidence("event", "Registro operacional", _date(occ.get("procedure_date")), " · ".join(parts), "GRADE")
                    for evo in evolutions:
                        _evidence(
                            "clinical_notes", "Evolução administrativa", _date(evo.get("evolution_recorded_at")),
                            _text(evo.get("description_raw")), f'ATEND. {_text(evo.get("attendance_number"))}',
                        )
                    for event in events:
                        review = str(event.get("review_reason") or "").strip()
                        explanation = DECISIONS.get(review, ("", "", ""))[1] if review else ""
                        _evidence(
                            "account_tree", _text(event.get("event_type")).replace("_", " ").title(),
                            _date(event.get("event_at")),
                            explanation or "Evento interpretado pelo motor a partir da evolução administrativa.",
                            "MOTOR",
                        )

            with ui.expansion("Dados técnicos do caso", icon="tune").classes("w-full border rounded-lg"):
                with ui.row().classes("w-full p-4 gap-6 flex-wrap"):
                    _metric("Grupo do motor", _text(row.get("work_group")).replace("_", " ").title())
                    _metric("Modo de fechamento", _text(row.get("closure_mode")).replace("_", " ").title())
                    _metric("Estado operacional", _text(row.get("operational_state")).replace("_", " ").title())
                    _metric("Localização", _text(row.get("current_location")).replace("_", " ").title())

            ui.separator()
            with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                ui.label(
                    "Quando a fonte é ambígua, o motor sinaliza revisão em vez de presumir o desfecho."
                ).classes("text-caption text-grey-7")
                ui.button("Fechar", on_click=dialog.close).props("flat no-caps")

    ui.timer(0.05, load, once=True)

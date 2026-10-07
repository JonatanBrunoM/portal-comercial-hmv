from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_mv_dialog import open_particular_mv_dialog
from nicegui_app.components.particular_account_resolution_dialog import open_account_resolution_dialog
from nicegui_app.components.particular_sheet_budget_dialog import open_particular_sheet_budget_dialog
from nicegui_app.services.particular_service import ParticularAccess, resolve_particular_account_review
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


def _closure_review_context(
    events: list[dict[str, Any]],
    evolutions: list[dict[str, Any]],
) -> tuple[str | None, str | None, str | None]:
    """Retorna somente o contexto factual que explica a validação de valor."""
    relevant = [
        event for event in events
        if str(event.get("closure_mode") or "").upper() in {"HIGHER", "LOWER"}
    ]
    if not relevant:
        return None, None, None

    event = relevant[-1]
    mode = str(event.get("closure_mode") or "").upper()
    label = "Fechou a maior" if mode == "HIGHER" else "Fechou a menor"

    evidence_id = str(event.get("evidence_id") or "")
    evidence = next(
        (item for item in evolutions if str(item.get("id") or "") == evidence_id),
        None,
    )
    description = _text((evidence or {}).get("description_raw"))
    return label, None if description == "—" else description, mode


def _composition_review_context(
    events: list[dict[str, Any]],
    evolutions: list[dict[str, Any]],
) -> str | None:
    """Retorna a evidência administrativa que explica a divergência de composição."""
    relevant = [
        event for event in events
        if str(event.get("review_reason") or "").upper() == "COMPOSICAO_DIVERGENTE"
    ]
    if not relevant:
        return None
    evidence_id = str(relevant[-1].get("evidence_id") or "")
    evidence = next(
        (item for item in evolutions if str(item.get("id") or "") == evidence_id),
        None,
    )
    description = _text((evidence or {}).get("description_raw"))
    return None if description == "—" else description


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


def open_particular_case_dossier(
    *,
    access: ParticularAccess,
    budget_id: str,
    on_resolved: Any | None = None,
) -> None:
    if not access.can_read:
        ui.notify("Você não possui acesso ao caso.", type="warning")
        return

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[860px] p-0"):
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
        group = str(row.get("work_group") or "")
        needs_review = group in {"REVISAR_FECHAMENTO", "REVISAR_TRAJETORIA"}
        title = "Verificação necessária" if needs_review else title
        next_action = {
            "VALIDAR_VALOR_FINAL": "Confirmar o valor final da conta no MV.",
            "COMPOSICAO_DIVERGENTE": "Conferir a composição final da conta no MV.",
            "DEVOLUCAO_OU_ESTORNO": "Confirmar o desfecho após o ajuste financeiro.",
            "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": "Confirmar no MV a situação atual da conta.",
            "DESFECHO_FINANCEIRO_PENDENTE": "Confirmar no MV o desfecho financeiro da conta.",
            "MULTIPLOS_EVENTOS_MESMA_DATA": "Confirmar no MV qual é a situação atual da conta.",
            "SEQUENCIA_TEMPORAL_AMBIGUA": "Confirmar no MV qual é a situação atual da conta.",
            "ORCAMENTO_VALOR_APROXIMADO": "Confirmar no MV o valor final e o fechamento.",
        }.get(str(row.get("account_review_reason") or ""), next_action)

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
                with ui.row().classes("w-full gap-4 items-center no-wrap"):
                    with ui.element("div").classes("rounded-full bg-red-50 p-3" if needs_review else "rounded-full bg-blue-50 p-3"):
                        ui.icon("priority_high" if needs_review else "check_circle", size="28px").classes("text-primary")
                    with ui.column().classes("gap-1 flex-1"):
                        ui.label(title).classes("text-h6 text-weight-bold")
                        ui.label(next_action).classes("text-body1")

            closure_label, closure_reason, closure_mode = _closure_review_context(events, evolutions)
            if str(row.get("account_review_reason") or "") == "VALIDAR_VALOR_FINAL" and closure_label:
                with ui.element("div").classes("w-full rounded-lg bg-blue-50 px-4 py-3"):
                    with ui.row().classes("w-full items-start gap-4 flex-wrap"):
                        with ui.column().classes("gap-0 min-w-[150px]"):
                            ui.label("O que foi identificado").classes("text-caption text-grey-6")
                            ui.label(closure_label).classes("text-body1 text-weight-bold")
                        if closure_reason:
                            with ui.column().classes("gap-0 flex-1 min-w-[280px]"):
                                ui.label("Motivo registrado").classes("text-caption text-grey-6")
                                ui.label(closure_reason).classes("text-body2 text-grey-9 whitespace-pre-wrap")

            composition_reason = _composition_review_context(events, evolutions)
            if str(row.get("account_review_reason") or "") == "COMPOSICAO_DIVERGENTE" and composition_reason:
                with ui.element("div").classes("w-full rounded-lg bg-blue-50 px-4 py-3"):
                    ui.label("O que foi identificado").classes("text-caption text-grey-6")
                    ui.label("Diferença na composição da conta").classes("text-body1 text-weight-bold")
                    ui.label("Motivo registrado").classes("text-caption text-grey-6 mt-2")
                    ui.label(composition_reason).classes("text-body2 text-grey-9 whitespace-pre-wrap")

            with ui.row().classes("w-full gap-6 px-1 flex-wrap"):
                with ui.column().classes("gap-0 min-w-[160px]"):
                    ui.label("Valor de referência").classes("text-caption text-grey-6")
                    ui.label(_money(row.get("reference_budget_value") or row.get("original_value"))).classes("text-subtitle1 text-weight-bold")
                with ui.column().classes("gap-0 min-w-[140px]"):
                    ui.label("Atendimento").classes("text-caption text-grey-6")
                    ui.label(_text(row.get("attendance_number"))).classes("text-subtitle1 text-weight-bold")
                with ui.column().classes("gap-0 min-w-[190px]"):
                    ui.label("Data operacional observada").classes("text-caption text-grey-6")
                    ui.label(_date(row.get("last_observed_operational_date"))).classes("text-subtitle1 text-weight-bold")

            with ui.row().classes("w-full gap-2 flex-wrap"):
                review_reason = str(row.get("account_review_reason") or "")

                def finish_case() -> None:
                    dialog.close()
                    if on_resolved:
                        on_resolved()

                async def resolve_from_mv(saved: dict[str, Any]) -> None:
                    if review_reason != "VALIDAR_VALOR_FINAL":
                        return
                    if str(saved.get("outcome") or "").upper() != "REALIZED":
                        ui.notify(
                            "Conferência registrada. O caso permanece na fila porque o MV não confirmou realização.",
                            type="warning",
                        )
                        return
                    final_value = str(saved.get("account_value") or "").strip()
                    if not final_value or closure_mode not in {"HIGHER", "LOWER"}:
                        ui.notify(
                            "Conferência registrada. Ainda falta informação para concluir o caso.",
                            type="warning",
                        )
                        return
                    try:
                        await run.io_bound(
                            resolve_particular_account_review,
                            access=access,
                            budget_id=budget_id,
                            account_status="CLOSED",
                            closure_mode=closure_mode,
                            confirmed_final_value=final_value,
                            resolution_notes=(
                                f"Valor final confirmado no MV pela conferência {saved.get('check_id')}."
                            ),
                        )
                    except Exception:
                        logger.exception("Falha ao concluir automaticamente a revisão após conferência MV.")
                        ui.notify(
                            "A conferência foi salva, mas a conclusão automática não pôde ser registrada.",
                            type="warning",
                        )
                        return
                    ui.notify("Conferência registrada e caso resolvido.", type="positive")
                    finish_case()

                def after_mv(saved: dict[str, Any]) -> None:
                    if review_reason == "VALIDAR_VALOR_FINAL":
                        ui.timer(0.05, lambda: resolve_from_mv(saved), once=True)
                        return
                    if (
                        review_reason == "COMPOSICAO_DIVERGENTE"
                        and str(saved.get("outcome") or "").upper() == "REALIZED"
                    ):
                        open_account_resolution_dialog(
                            access=access,
                            budget_id=budget_id,
                            budget_number=number,
                            review_reason=review_reason,
                            confirmed_final_value_prefill=str(saved.get("account_value") or "") or None,
                            on_resolved=finish_case,
                        )

                if needs_review and access.can_write:
                    def handle_resolution() -> None:
                        finish_case()

                    ui.button(
                        "Registrar conclusão", icon="task_alt",
                        on_click=lambda: open_particular_mv_dialog(
                            access=access,
                            budget_id=budget_id,
                            attendance_number=str(row.get("attendance_number") or "") or None,
                            notice_number=str(row.get("notice_number") or "") or None,
                            on_saved=after_mv,
                        ),
                    ).props("unelevated no-caps")
                ui.button(
                    "Consultar grades", icon="table_view",
                    on_click=lambda: open_particular_sheet_budget_dialog(access=access, budget_number=number),
                ).props("outline no-caps")

            ui.label(
                "O histórico detalhado e as evidências técnicas ficarão disponíveis na área de auditoria."
            ).classes("text-caption text-grey-6")

            ui.separator()
            with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                ui.label(
                    "Quando a fonte é ambígua, o motor sinaliza revisão em vez de presumir o desfecho."
                ).classes("text-caption text-grey-7")
                ui.button("Fechar", on_click=dialog.close).props("flat no-caps")

    ui.timer(0.05, load, once=True)

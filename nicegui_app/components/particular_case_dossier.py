from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_mv_dialog import open_particular_mv_dialog
from nicegui_app.components.particular_account_resolution_dialog import open_account_resolution_dialog
from nicegui_app.components.particular_investigation_dialog import open_particular_investigation_dialog
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
    if group == "INVESTIGACAO_CONCLUIDA":
        return (
            "Investigação concluída",
            "O desfecho da investigação foi registrado e retirado da fila de pendências.",
            "A conclusão e as evidências permanecem disponíveis para consulta e auditoria.",
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

    with ui.dialog().props("maximized=false") as dialog, ui.card().classes("w-full max-w-[1040px] p-0 rounded-2xl shadow-2xl").style("overflow:hidden; border:1px solid #e2eaf2"):
        header = ui.column().classes("w-full px-7 py-5 gap-1").style("background:linear-gradient(110deg,#f1f7fc 0%,#fff 75%)")
        ui.separator()
        body = ui.column().classes("w-full px-7 py-5 gap-4").style("max-height: 73vh; overflow-y:auto; background:#f7f9fc")
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
        investigation_candidates = data.get("investigation_candidates") or []
        original_values = data.get("original_values") or []
        original = original_values[0] if original_values else {}
        mv_notices = data.get("mv_notices") or []
        mv_accounts = data.get("mv_accounts") or []

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
                    ui.label("CENTRAL DE INTELIGÊNCIA  /  ANÁLISE COMPLETA").classes("text-caption text-weight-bold text-primary tracking-wide")
                    ui.label(f"Orçamento #{number}").classes("text-h5 text-weight-bold").style("color:#153449; letter-spacing:-.4px")
                    ui.label(
                        f'{_text(row.get("doctor_name"))} · origem {_text(row.get("portfolio_origin")).title()}'
                    ).classes("text-body2 text-grey-7")
                ui.button(icon="close", on_click=dialog.close).props("flat round")

        body.clear()
        with body:
            with ui.card().classes("w-full p-5 shadow-none rounded-xl").style("border:1px solid #cfe0f0; border-left:4px solid #4f94cc; background:#fff"):
                with ui.row().classes("w-full gap-4 items-center no-wrap"):
                    with ui.element("div").classes("rounded-full bg-red-50 p-3" if needs_review else "rounded-full bg-blue-50 p-3"):
                        ui.icon("priority_high" if needs_review else "check_circle", size="28px").classes("text-primary")
                    with ui.column().classes("gap-1 flex-1"):
                        ui.label(title).classes("text-h6 text-weight-bold")
                        ui.label(next_action).classes("text-body1")

            # Roteiro orientativo e específico da pendência, sem criar decisão.
            review_reason = str(
                row.get("account_review_reason") or row.get("work_reason") or ""
            ).strip()
            verification_steps = {
                "VALIDAR_VALOR_FINAL": (
                    "Verifique no MV o valor efetivamente fechado.",
                    "Confirme o valor final somente com evidência conclusiva.",
                ),
                "COMPOSICAO_DIVERGENTE": (
                    "Confira os itens, materiais ou exames divergentes.",
                    "Registre a conclusão da composição com base no MV.",
                ),
                "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": (
                    "Identifique o ajuste e os eventos posteriores.",
                    "Confirme se a conta foi fechada, reaberta ou permanece pendente.",
                ),
                "DEVOLUCAO_OU_ESTORNO": (
                    "Confira o registro de devolução ou estorno.",
                    "Valide o estado atual da conta após o ajuste.",
                ),
                "MULTIPLOS_EVENTOS_MESMA_DATA": (
                    "Confira os eventos e sua sequência real no MV.",
                    "Identifique o último estado comprovado antes de concluir.",
                ),
                "SEQUENCIA_TEMPORAL_AMBIGUA": (
                    "Confira fechamento e reabertura na mesma data.",
                    "Confirme a situação atual sem presumir a ordem dos eventos.",
                ),
                "DESFECHO_FINANCEIRO_PENDENTE": (
                    "Verifique se existe encerramento ou outro desfecho no MV.",
                    "Registre somente o resultado sustentado pelas evidências.",
                ),
            }
            steps = verification_steps.get(review_reason)
            if not steps and group in {"GRADE_SEM_OPERACAO", "NEGATIVA_SEM_OPERACAO"}:
                steps = (
                    "Confira a grade e os possíveis vínculos com outros orçamentos.",
                    "Confirme a relação antes de registrar a investigação.",
                )
            if not steps and group == "REVISAR_TRAJETORIA":
                steps = (
                    "Confira os avisos e as mudanças de data ou local.",
                    "Valide o desfecho operacional antes de concluir.",
                )
            if steps:
                with ui.card().classes("w-full p-4 shadow-none rounded-xl").style("border:1px solid #e2eaf2; background:#fff"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("route", size="20px").classes("text-primary")
                        ui.label("Roteiro de conferência").classes(
                            "text-subtitle1 text-weight-bold"
                        )
                    for index, step in enumerate(steps, start=1):
                        with ui.row().classes("w-full items-start gap-2 no-wrap"):
                            ui.badge(str(index), color="primary")
                            ui.label(step).classes("text-body2")
                    ui.label(
                        "Orientação de apoio. A decisão continua sendo registrada "
                        "pelas ações existentes neste dossiê."
                    ).classes("text-caption text-grey-7")

            # Resumo baseado apenas nas evidências efetivamente retornadas pelo dossiê.
            # A ausência de registros nesta consulta não comprova ausência na origem.
            with ui.card().classes("w-full p-4 shadow-none rounded-xl").style("border:1px solid #e2eaf2; background:#fff"):
                ui.label("Fontes identificadas").classes("text-subtitle1 text-weight-bold")
                ui.label(
                    "Registros vinculados a este orçamento nas fontes consultadas."
                ).classes("text-caption text-grey-7")
                with ui.row().classes("w-full gap-5 flex-wrap mt-2"):
                    _metric("Ocorrências operacionais", str(len(occurrences)), "Grade vinculada ao caso")
                    _metric("Eventos financeiros", str(len(events)), "Eventos retornados na análise")
                    _metric("Evoluções administrativas", str(len(evolutions)), "Registros associados ao caso")
                    _metric("Indícios para investigação", str(len(investigation_candidates)), "Possíveis relações, não confirmadas")
                with ui.row().classes("w-full gap-2 flex-wrap mt-2"):
                    ui.badge("Orçamento de referência: " + _money(
                        row.get("reference_budget_value") or row.get("original_value")
                    )).props("outline")
                    if row.get("account_status"):
                        ui.badge(
                            "Estado da conta: " + _text(row.get("account_status"))
                        ).props("outline")
                ui.label(
                    "A situação financeira não confirma, por si só, o desfecho operacional."
                ).classes("text-caption text-grey-7")

            with ui.expansion(
                "Explorar evidências · XML, grade e MV",
                icon="fact_check",
            ).classes("w-full rounded-xl").style("background:#fff; border:1px solid #e2eaf2"):
                ui.label(
                    "Confronto das fontes vinculadas ao orçamento. Os valores da "
                    "importação não são comprovantes de pagamento nem valores finais confirmados."
                ).classes("text-caption text-grey-7")
                with ui.row().classes("w-full gap-5 flex-wrap"):
                    _metric(
                        "Original vigente (importação)",
                        _money(original.get("total_value")),
                        "Espelho estruturado do XML, não o arquivo bruto",
                    )
                    _metric(
                        "Contas MV vinculadas",
                        str(len(mv_accounts)),
                        "Vínculo por aviso da grade",
                    )
                if original:
                    ui.label(
                        "Procedimento: " + _money(original.get("procedure_value"))
                        + " · Materiais: " + _money(original.get("material_value"))
                    ).classes("text-body2")
                if mv_accounts:
                    ui.label("Registros de contas MV encontrados").classes(
                        "text-body2 text-weight-bold mt-2"
                    )
                    for account in mv_accounts[:15]:
                        notices = sorted({
                            str(item.get("notice_number"))
                            for item in mv_notices
                            if str(item.get("account_record_id")) == str(account.get("id"))
                        })
                        with ui.card().classes("w-full p-3 shadow-none border rounded-lg"):
                            ui.label(
                                "Aviso(s): " + (", ".join(notices) or "não informado")
                                + " · Atendimento: "
                                + str(account.get("attendance_number") or "não informado")
                            ).classes("text-body2 text-weight-bold")
                            ui.label(
                                "Conta: " + str(account.get("account_number") or "não informada")
                                + " · Valor registrado: " + _money(account.get("account_total"))
                                + " · Situação no registro: "
                                + (
                                    "Fechada" if account.get("is_closed") is True
                                    else "Aberta" if account.get("is_closed") is False
                                    else "Não informada"
                                )
                            ).classes("text-body2")
                else:
                    ui.label(
                        "Nenhuma conta MV vinculada pelos avisos consultados. "
                        "Isso não significa que não exista conta no MV."
                    ).classes("text-caption text-grey-7")
                with ui.expansion(
                    f"Grade operacional · {len(occurrences)} registro(s)", icon="event_note"
                ):
                    for item in occurrences[:20]:
                        ui.label(
                            "Aviso " + str(item.get("notice_number") or "não informado")
                            + " · " + _date(item.get("procedure_date"))
                            + " · " + str(item.get("location") or "local não informado")
                        ).classes("text-body2")
                        if item.get("notes_original"):
                            ui.label(
                                "Observação: " + str(item.get("notes_original"))
                            ).classes("text-caption text-grey-7")
                with ui.expansion(
                    f"Eventos financeiros · {len(events)} registro(s)", icon="receipt_long"
                ):
                    for item in events[:20]:
                        ui.label(
                            str(item.get("event_type") or "Evento").replace("_", " ").title()
                            + " · " + _date(item.get("event_at"))
                            + " · " + str(item.get("closure_mode") or "sem modalidade")
                        ).classes("text-body2")
                        if item.get("interpretation_details"):
                            details = item.get("interpretation_details")
                            if isinstance(details, dict):
                                details = details.get("description") or details.get("reason") or ""
                            if details:
                                ui.label(str(details)).classes("text-caption text-grey-7")
                with ui.expansion(
                    f"Evoluções administrativas · {len(evolutions)} registro(s)",
                    icon="history",
                ):
                    for item in evolutions[:20]:
                        ui.label(
                            _date(item.get("evolution_recorded_at"))
                            + " · " + str(item.get("evolution_type") or "Evolução")
                        ).classes("text-body2 text-weight-bold")
                        if item.get("description_raw"):
                            ui.label(str(item.get("description_raw"))).classes(
                                "text-body2 whitespace-pre-wrap"
                            )
                ui.label(
                    "As fontes exibidas são os registros retornados pela consulta. "
                    "Ausência de registro não comprova ausência na origem."
                ).classes("text-caption text-grey-7")

            closure_label, closure_reason, closure_mode = _closure_review_context(events, evolutions)
            raw_review_reason = str(row.get("account_review_reason") or "")
            ambiguity_with_explicit_closure = (
                raw_review_reason in {"MULTIPLOS_EVENTOS_MESMA_DATA", "SEQUENCIA_TEMPORAL_AMBIGUA"}
                and closure_mode in {"HIGHER", "LOWER"}
            )
            effective_review_reason = (
                "VALIDAR_VALOR_FINAL" if ambiguity_with_explicit_closure else raw_review_reason
            )

            if effective_review_reason == "VALIDAR_VALOR_FINAL" and closure_label:
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

            ambiguous_reasons = {"MULTIPLOS_EVENTOS_MESMA_DATA", "SEQUENCIA_TEMPORAL_AMBIGUA"}
            if raw_review_reason in ambiguous_reasons:
                event_evidence_ids = {
                    str(event.get("evidence_id") or "")
                    for event in events
                    if event.get("evidence_id")
                }
                related_evolutions = [
                    item for item in evolutions
                    if str(item.get("id") or "") in event_evidence_ids
                ]
                if not related_evolutions:
                    related_evolutions = evolutions

                with ui.element("div").classes("w-full rounded-lg bg-blue-50 px-4 py-3"):
                    ui.label("Eventos que precisam ser comparados").classes(
                        "text-caption text-grey-6"
                    )
                    ui.label(
                        "O sistema encontrou eventos cuja ordem não pode ser definida com segurança pela fonte."
                    ).classes("text-body2 text-grey-8 mb-2")
                    for item in related_evolutions:
                        with ui.element("div").classes(
                            "w-full bg-white rounded border px-3 py-2 mb-2"
                        ):
                            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                                ui.label(
                                    _date(item.get("evolution_recorded_at"))
                                ).classes("text-caption text-weight-bold text-primary")
                                evolution_type = _text(item.get("evolution_type"))
                                if evolution_type != "—":
                                    ui.badge(evolution_type).props("outline")
                                user_name = _text(item.get("user_name"))
                                if user_name != "—":
                                    ui.label(user_name).classes("text-caption text-grey-6")
                            ui.label(
                                _text(item.get("description_raw"))
                            ).classes("text-body2 text-grey-9 whitespace-pre-wrap")

            if group == "INVESTIGACAO_CONCLUIDA":
                outcome_labels = {
                    "REBUDGET": "Orçamento substituído / reorçado",
                    "DISTINCT": "Sem relação com o indício",
                    "CANCELLED": "Cancelamento confirmado",
                    "OTHER": "Outro desfecho",
                }
                dimension_labels = {
                    "PROCEDURE": "Procedimento",
                    "DOCTOR": "Médico",
                    "VALUE": "Valor",
                    "DATE": "Data",
                }
                outcome = str(row.get("investigation_outcome") or "").upper()
                related_number = _text(row.get("investigation_related_budget_number"))
                dimensions = row.get("investigation_change_dimensions") or []
                with ui.element("div").classes("w-full rounded-lg bg-green-50 px-4 py-3"):
                    ui.label("Investigação concluída").classes(
                        "text-caption text-weight-bold text-positive"
                    )
                    ui.label(outcome_labels.get(outcome, outcome or "Conclusão registrada")).classes(
                        "text-body1 text-weight-bold"
                    )
                    if related_number != "—":
                        ui.label(f"Orçamento relacionado: #{related_number}").classes(
                            "text-body2 text-grey-8"
                        )
                    if dimensions:
                        changed = ", ".join(
                            dimension_labels.get(str(item).upper(), str(item))
                            for item in dimensions
                        )
                        ui.label(f"Alterações confirmadas: {changed}").classes(
                            "text-body2 text-grey-8"
                        )
                    notes = _text(row.get("investigation_resolution_notes"))
                    if notes != "—":
                        ui.label("Justificativa").classes("text-caption text-grey-6 mt-2")
                        ui.label(notes).classes("text-body2 text-grey-9 whitespace-pre-wrap")
                    resolved_at = row.get("investigation_resolved_at")
                    if resolved_at:
                        ui.label(f"Concluída em {_date(resolved_at)}").classes(
                            "text-caption text-grey-6 mt-2"
                        )

            if investigation_candidates:
                with ui.element("div").classes("w-full rounded-lg bg-amber-50 px-4 py-3"):
                    ui.label("Indícios encontrados nas grades").classes(
                        "text-caption text-weight-bold text-orange-9"
                    )
                    ui.label(
                        "O orçamento não possui vínculo operacional direto, mas o mesmo paciente foi localizado em outras ocorrências. "
                        "Os registros abaixo são pistas para investigação e não representam vínculo automático."
                    ).classes("text-body2 text-grey-8 mb-3")

                    for candidate in investigation_candidates:
                        related = candidate.get("related_budget") or {}
                        related_number = _text(related.get("budget_number"))
                        with ui.element("div").classes("w-full bg-white rounded border px-3 py-3 mb-2"):
                            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                                ui.label(_text(candidate.get("patient_name"))).classes(
                                    "text-body2 text-weight-bold"
                                )
                                if related_number != "—":
                                    ui.badge(f"Orçamento #{related_number}").classes("bg-primary")
                                ui.space()
                                ui.label(_date(candidate.get("procedure_date"))).classes(
                                    "text-caption text-grey-6"
                                )
                            with ui.row().classes("w-full gap-5 mt-2 flex-wrap"):
                                _metric("Médico na grade", _text(candidate.get("doctor_name")))
                                _metric("Atendimento / aviso", _text(
                                    candidate.get("notice_number") or related.get("attendance_number")
                                ))
                                _metric("Valor operacional", _money(candidate.get("operational_value")))
                            if related:
                                with ui.row().classes("w-full gap-5 mt-2 flex-wrap"):
                                    _metric("Médico do orçamento relacionado", _text(related.get("doctor_name")))
                                    _metric("Valor do orçamento relacionado", _money(related.get("original_value")))
                                    _metric("Data do orçamento relacionado", _date(related.get("budget_date")))
                            differential = _text(candidate.get("differential"))
                            notes = _text(candidate.get("notes_original"))
                            if differential != "—":
                                ui.label(f"Diferencial: {differential}").classes("text-caption text-grey-8 mt-2")
                            if notes != "—":
                                ui.label(notes).classes("text-caption text-grey-7 whitespace-pre-wrap")

            with ui.row().classes("w-full gap-6 px-4 py-3 flex-wrap rounded-xl").style("background:#eaf2f9; border:1px solid #dce8f3"):
                with ui.column().classes("gap-0 min-w-[160px]"):
                    ui.label("Valor de referência").classes("text-caption text-grey-6")
                    ui.label(_money(row.get("reference_budget_value") or row.get("original_value"))).classes("text-subtitle1 text-weight-bold")
                with ui.column().classes("gap-0 min-w-[140px]"):
                    ui.label("Atendimento").classes("text-caption text-grey-6")
                    ui.label(_text(row.get("attendance_number"))).classes("text-subtitle1 text-weight-bold")
                with ui.column().classes("gap-0 min-w-[190px]"):
                    ui.label("Data operacional observada").classes("text-caption text-grey-6")
                    ui.label(_date(row.get("last_observed_operational_date"))).classes("text-subtitle1 text-weight-bold")

            with ui.row().classes("w-full gap-2 flex-wrap items-center px-4 py-3 rounded-xl").style("background:#fff; border:1px solid #dce8f3"):
                review_reason = effective_review_reason

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

                if (
                    group in {"GRADE_SEM_OPERACAO", "NEGATIVA_SEM_OPERACAO"}
                    and investigation_candidates
                    and access.can_write
                ):
                    ui.button(
                        "Concluir investigação",
                        icon="task_alt",
                        on_click=lambda: open_particular_investigation_dialog(
                            access=access,
                            budget_id=budget_id,
                            budget_number=number,
                            candidates=investigation_candidates,
                            on_resolved=finish_case,
                        ),
                    ).props("unelevated no-caps")

                if needs_review and access.can_write:
                    def handle_resolution() -> None:
                        finish_case()

                    def open_conclusion() -> None:
                        # Se a própria evolução já comprova o fechamento e a pendência é
                        # somente de composição, não perguntamos novamente se houve realização.
                        # Vamos direto ao desfecho da composição, preservando a evidência original.
                        if review_reason == "COMPOSICAO_DIVERGENTE" and composition_reason:
                            open_account_resolution_dialog(
                                access=access,
                                budget_id=budget_id,
                                budget_number=number,
                                review_reason=review_reason,
                                confirmed_final_value_prefill=(
                                    str(row.get("mv_account_value") or "") or None
                                ),
                                on_resolved=finish_case,
                            )
                            return

                        open_particular_mv_dialog(
                            access=access,
                            budget_id=budget_id,
                            attendance_number=str(row.get("attendance_number") or "") or None,
                            notice_number=str(row.get("notice_number") or "") or None,
                            review_reason=review_reason or None,
                            closure_mode=closure_mode,
                            on_saved=after_mv,
                        )

                    ui.button(
                        "Registrar conclusão", icon="task_alt",
                        on_click=open_conclusion,
                    ).props("unelevated no-caps")

            ui.label(
                "As decisões registradas preservam o histórico e as evidências vinculadas."
            ).classes("text-caption text-grey-6")

            ui.separator()
            with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                ui.label(
                    "Quando a fonte é ambígua, o motor sinaliza revisão em vez de presumir o desfecho."
                ).classes("text-caption text-grey-7")
                ui.button("Fechar", on_click=dialog.close).props("flat no-caps")

    ui.timer(0.05, load, once=True)

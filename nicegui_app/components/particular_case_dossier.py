from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_mv_dialog import open_particular_mv_dialog
from nicegui_app.components.particular_account_resolution_dialog import open_account_resolution_dialog
from nicegui_app.components.particular_investigation_dialog import open_particular_investigation_dialog
from nicegui_app.services.particular_service import ParticularAccess, resolve_particular_account_review, register_particular_mv_check
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



# Rótulos de interface: nunca alteram os códigos persistidos no banco.
TECHNICAL_LABELS = {
    "ACCOUNT_ADJUSTED": "Ajuste registrado na conta",
    "ACCOUNT_CLOSED": "Conta fechada",
    "ACCOUNT_REOPENED": "Conta reaberta",
    "ACCOUNT_OPENED": "Conta aberta",
    "ACCOUNT_CREATED": "Conta criada",
    "ACCOUNT_CANCELLED": "Conta cancelada",
    "ACCOUNT_CANCELED": "Conta cancelada",
    "SPECIAL_OUTCOME": "Situação financeira especial",
    "REVIEW_REQUIRED": "Necessita de revisão",
    "AUTO_RESOLVED": "Análise automática concluída",
    "MANUALLY_RESOLVED": "Análise concluída manualmente",
    "ACCORDING_TO_BUDGET": "Conforme orçamento",
    "HIGHER": "Fechamento a maior",
    "LOWER": "Fechamento a menor",
    "WITH_ADJUSTMENT": "Fechamento com ajuste",
    "PENDING": "Pendente",
    "REALIZED": "Realizado",
    "NOT_PERFORMED": "Não realizado",
    "CANCELLED": "Cancelado",
    "CONFIRMED": "Confirmado",
    "CORRECTED": "Corrigido",
    "DISMISSED": "Descartado após análise",
    "NOT_ENOUGH_INFORMATION": "Informações insuficientes",
    "MULTIPLE_NOTICE": "Múltiplos avisos",
    "POSSIBLE_CANCELLATION": "Possível cancelamento",
    "POSSIBLE_TRANSFER": "Possível transferência",
    "SOURCE_CONFLICT": "Conflito entre fontes",
    "VALUE_DIVERGENCE": "Divergência de valor",
    "ORIGIN_DIVERGENCE": "Divergência de origem",
    "STATE_DIVERGENCE": "Divergência de situação",
    "CLOSED": "Conta fechada",
    "OPEN": "Em aberto",
    "INCONCLUSIVE": "Situação inconclusiva",
    "OTHER": "Outro desfecho",
    "NONE": "Sem alteração",
    "NO_CHANGE": "Sem alteração",
    "STABLE": "Sem mudança identificada",
    "REOPENED": "Reaberta",
    "ACCOUNT_REOPENED": "Conta reaberta",
    "ACCOUNT_REOPENING": "Reabertura de conta",
    "ACCOUNT_ADJUSTMENT": "Ajuste na conta",
    "ACCOUNT_REVERSED": "Estorno na conta",
    "ACCOUNT_REFUNDED": "Devolução financeira",
    "TRANSFER_INTENT": "Intenção de transferência",
    "TRANSFER_EXPLICIT": "Transferência registrada",
    "CANCEL_INTENT": "Intenção de cancelamento",
    "CANCEL_EXPLICIT": "Cancelamento registrado",
    "MULTIPLE_LOCATION": "Múltiplos locais registrados",
    "UNMATCHED_OPERATION": "Operação sem orçamento identificado",
    "DUPLICATE_BUDGET": "Possível orçamento duplicado",
    "UNKNOWN_MODALITY": "Modalidade não identificada",
    "MANUAL_REVIEW": "Revisão manual",
    "REVISAR_FECHAMENTO": "Revisar fechamento",
    "REVISAR_TRAJETORIA": "Revisar trajetória",
    "GRADE_SEM_OPERACAO": "Grade sem operação vinculada",
    "NEGATIVA_SEM_OPERACAO": "Negativa sem operação vinculada",
    "OPERACAO_COMPETENCIA": "Operação na competência",
    "OPERACAO_FUTURA": "Operação futura",
    "FECHAMENTO_IDENTIFICADO": "Fechamento identificado",
    "CONSULTORIO_SEM_OPERACAO": "Consultório sem operação vinculada",
    "COTACAO": "Cotação",
    "TRANSCRICAO": "Transcrição",
    "ANULADO_CONFIRMADO": "Anulação confirmada",
    "INVESTIGACAO_CONCLUIDA": "Investigação concluída",
    "GRADE": "Grade",
    "NEGATIVA": "Negativa",
    "XML": "Orçamento original (XML)",
    "GOOGLE_SHEETS": "Planilha operacional",
    "INDICATOR_SHEET": "Planilha de indicadores",
    "MV": "Sistema MV",
    "SYSTEM": "Motor de análise",
    "MANUAL": "Registro manual",
    "REVIEW": "Em revisão",
    "REVIEWED": "Revisado",
    "OPEN_REVIEW": "Revisão em aberto",
    "IN_REVIEW": "Em análise",
    "RESOLVED": "Resolvido",
    "DISMISSED": "Descartado após análise",
    "VALIDAR_VALOR_FINAL": "Confirmar valor final",
    "COMPOSICAO_DIVERGENTE": "Divergência na composição da conta",
    "DEVOLUCAO_OU_ESTORNO": "Devolução ou estorno",
    "CONTA_REABERTA": "Conta reaberta",
    "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": "Ajuste sem fechamento confirmado",
    "DESFECHO_FINANCEIRO_PENDENTE": "Desfecho financeiro pendente",
    "EVOLUCAO_INCONCLUSIVA": "Evolução inconclusiva",
    "MULTIPLOS_EVENTOS_MESMA_DATA": "Eventos diferentes na mesma data",
    "SEQUENCIA_TEMPORAL_AMBIGUA": "Sequência de eventos indefinida",
    "ORCAMENTO_VALOR_APROXIMADO": "Orçamento com valor aproximado",
    "ORIGEM_GRADE_SEM_EVIDENCIA_OPERACIONAL": "Grade sem evidência operacional",
    "ORIGEM_NEGATIVA_SEM_EVIDENCIA_OPERACIONAL": "Negativa sem evidência operacional",
    "INVESTIGACAO_CONCLUIDA_REORCAMENTO": "Reorçamento confirmado",
    "INVESTIGACAO_CONCLUIDA_SEM_RELACAO": "Sem relação com o orçamento",
    "INVESTIGACAO_CONCLUIDA_CANCELAMENTO": "Cancelamento confirmado na investigação",
    "INVESTIGACAO_CONCLUIDA_OUTRO": "Outro desfecho de investigação",
    "REBUDGET": "Reorçamento",
    "DISTINCT": "Orçamentos distintos",
    "CONFIRMED_DUPLICATE": "Duplicidade confirmada",
    "PENDING_REVIEW": "Aguardando revisão",
}

def _technical_label(value: Any) -> str:
    """Traduz códigos conhecidos e humaniza códigos novos sem expor identificadores crus."""
    raw = _text(value)
    if raw == "—":
        return raw
    code = raw.upper().strip()
    if code in TECHNICAL_LABELS:
        return TECHNICAL_LABELS[code]
    if "_" in code and all(part.isalnum() for part in code.split("_")):
        return code.replace("_", " ").capitalize()
    return raw


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

    ui.add_css("""
    .mv-outcome-cards.q-option-group {
        display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;width:100%;
    }
    .mv-outcome-cards .q-radio {
        min-width:0;min-height:78px;display:flex;flex-direction:column;
        align-items:center;justify-content:center;gap:5px;margin:0!important;
        padding:10px 5px;border:1px solid #dbe6ef;border-radius:13px;background:#fff;
        box-shadow:0 3px 12px rgba(20,54,76,.04);
    }
    .mv-outcome-cards .q-radio:has(.q-radio__inner--truthy) {
        background:#e7f4ff;border-color:#1985ca;
        box-shadow:0 0 0 2px rgba(25,133,202,.12);
    }
    .mv-outcome-cards .q-radio__label {
        font-weight:650;font-size:13px;color:#173b53;text-align:center;padding:0;
    }
    .mv-fields-grid .q-field--outlined .q-field__control {min-height:56px;}
    .mv-fields-grid .q-textarea textarea {min-height:24px!important;resize:vertical;}
    @media(max-width:600px) {
        .mv-outcome-cards.q-option-group {grid-template-columns:repeat(2,minmax(0,1fr))}
        .mv-fields-grid {grid-template-columns:1fr!important}
    }
    """)
    with ui.dialog().props("maximized=false") as dialog, ui.card().classes("w-[min(1080px,96vw)] max-w-none p-0 rounded-2xl shadow-2xl").style("overflow:hidden; border:1px solid #e2eaf2; display:flex; flex-direction:column; height:min(800px,92vh)"):
        header = ui.column().classes("w-full px-6 py-2 gap-0 shrink-0").style("background:linear-gradient(110deg,#f1f7fc 0%,#fff 75%); border-bottom:1px solid #e2eaf2")
        body = ui.column().classes("w-full px-6 py-3 gap-2").style("flex:1 1 0; min-height:0; overflow-y:auto; background:#f7f9fc; overscroll-behavior:contain")
        footer = ui.column().classes("w-full px-6 py-2 gap-1 shrink-0").style("background:#f7fafc; border-top:1px solid #dce8f3; box-shadow:0 -5px 18px rgba(20,52,73,.07); max-height:48vh; overflow-y:auto")
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
            with ui.card().classes("w-full p-4 shadow-none rounded-xl").style("border:1px solid #cfe0f0; border-left:4px solid #4f94cc; background:#fff"):
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
            # Síntese direta das três fontes, sem dropdowns ou histórico bruto.
            # Cada leitura é factual: registros associados não comprovam pagamento.
            def source_card(icon: str, label: str, headline: str, detail: str) -> None:
                with ui.card().classes("flex-1 min-w-[205px] p-4 gap-2 shadow-none rounded-xl").style(
                    "background:#fff; border:1px solid #dce8f3"
                ):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon(icon, size="19px").classes("text-primary")
                        ui.label(label).classes("text-caption text-weight-bold text-primary")
                    ui.label(headline).classes("text-body1 text-weight-bold").style("color:#16384d")
                    ui.label(detail).classes("text-body2 text-grey-7")

            latest_evolution = evolutions[-1] if evolutions else {}
            evolution_description = str(latest_evolution.get("description_raw") or "").strip()
            evolution_headline = (
                f"{len(evolutions)} evolução(ões) vinculada(s)"
                if evolutions else "Sem evolução vinculada"
            )
            evolution_detail = (
                evolution_description[:190] + ("…" if len(evolution_description) > 190 else "")
                if evolution_description else
                ("Há registro(s), mas sem descrição disponível." if evolutions
                 else "Não foram localizados registros nesta consulta.")
            )
            latest_occurrence = occurrences[-1] if occurrences else {}
            grade_headline = (
                f"{len(occurrences)} ocorrência(s) localizada(s)"
                if occurrences else "Sem ocorrência vinculada"
            )
            grade_detail = (
                "Aviso " + _text(latest_occurrence.get("notice_number"))
                + " · " + _date(latest_occurrence.get("procedure_date"))
                + (" · " + str(latest_occurrence.get("notes_original"))[:110]
                   if latest_occurrence.get("notes_original") else "")
                if occurrences else "Nenhum registro de grade associado nesta consulta."
            )
            latest_event = events[-1] if events else {}
            account_headline = (
                f"{len(events)} evento(s) · {len(mv_accounts)} conta(s) MV"
            )
            account_detail = (
                "Último evento: " + _technical_label(latest_event.get("event_type"))
                + " · " + _date(latest_event.get("event_at"))
                if events else
                ("Conta(s) MV vinculada(s), sem evento financeiro associado nesta consulta."
                 if mv_accounts else "Sem evento ou conta vinculada nesta consulta.")
            )
            with ui.row().classes("w-full gap-3 items-stretch flex-wrap"):
                source_card("history", "EVOLUÇÕES", evolution_headline, evolution_detail)
                source_card("event_note", "GRADE", grade_headline, grade_detail)
                source_card("receipt_long", "CONTAS / MV", account_headline, account_detail)

            if steps:
                ui.label("Próxima conferência: " + steps[0]).classes(
                    "text-body2 text-grey-8 px-1"
                )
            ui.label(
                "Resumo dos registros vinculados. A ausência de vínculo não comprova "
                "ausência na origem; eventos financeiros não confirmam pagamento."
            ).classes("text-caption text-grey-6 px-1")

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
                    ui.label(outcome_labels.get(outcome, _technical_label(outcome) if outcome else "Conclusão registrada")).classes(
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

        footer.clear()
        with footer:
            with ui.column().classes("w-full gap-3"):
                with ui.row().classes("w-full items-center gap-5 flex-wrap px-2 py-2 rounded-xl").style("background:#edf5fb;border:1px solid #d8e8f3"):
                    with ui.column().classes("gap-0"):
                        ui.label("REFERÊNCIA").classes("text-caption text-grey-6")
                        ui.label(_money(row.get("reference_budget_value") or row.get("original_value"))).classes("text-body2 text-weight-bold")
                    with ui.column().classes("gap-0"):
                        ui.label("ATENDIMENTO").classes("text-caption text-grey-6")
                        ui.label(_text(row.get("attendance_number"))).classes("text-body2 text-weight-bold")
                    with ui.column().classes("gap-0"):
                        ui.label("DATA OBSERVADA").classes("text-caption text-grey-6")
                        ui.label(_date(row.get("last_observed_operational_date"))).classes("text-body2 text-weight-bold")
                with ui.column().classes("w-full gap-2"):
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

                        # Registro integrado ao dossiê: sem abrir um segundo modal.
                        # A composição com desfecho comprovado mantém sua decisão específica.
                        composition_direct = review_reason == "COMPOSICAO_DIVERGENTE" and bool(composition_reason)
                        if composition_direct:
                            ui.button(
                                "Concluir composição", icon="task_alt",
                                on_click=lambda: open_account_resolution_dialog(
                                    access=access,
                                    budget_id=budget_id,
                                    budget_number=number,
                                    review_reason=review_reason,
                                    confirmed_final_value_prefill=str(row.get("mv_account_value") or "") or None,
                                    on_resolved=finish_case,
                                ),
                            ).props("unelevated no-caps color=primary")
                        else:
                            inferred_closure = review_reason == "VALIDAR_VALOR_FINAL" and closure_mode in {"HIGHER", "LOWER"}
                            with ui.column().classes("w-full gap-3 p-4 rounded-2xl").style("background:#fff;border:1px solid #dce8f2"):
                                ui.label("REGISTRAR CONCLUSÃO NO MV").classes("text-caption text-weight-bold text-primary")
                                if inferred_closure:
                                    with ui.row().classes("w-full items-center gap-3 p-3 rounded-xl").style(
                                        "background:#e8f4ff;border:1px solid #a9d1f1"
                                    ):
                                        ui.icon("verified", size="22px").classes("text-primary")
                                        ui.label(
                                            "Fechamento a maior" if closure_mode == "HIGHER"
                                            else "Fechamento a menor"
                                        ).classes("text-body1 text-weight-bold")
                                    outcome_input = None
                                else:
                                    ui.label("Situação confirmada no MV").classes(
                                        "text-body2 text-weight-medium"
                                    ).style("color:#173b53")
                                    outcome_input = ui.radio(
                                        {"PENDING": "Pendente", "REALIZED": "Realizado",
                                         "NOT_PERFORMED": "Não realizado", "CANCELLED": "Cancelado"},
                                        value="PENDING",
                                    ).classes("mv-outcome-cards w-full")
                                with ui.grid(columns=2).classes("w-full gap-4 mv-fields-grid"):
                                    with ui.column().classes("w-full min-w-0 gap-1"):
                                        ui.label("Valor confirmado").classes(
                                            "text-body2 text-weight-medium"
                                        ).style("color:#173b53")
                                        amount_input = ui.input(
                                            placeholder="Ex.: 4.989,60"
                                        ).props("outlined prefix=R$ bg-color=white").classes("w-full")
                                    with ui.column().classes("w-full min-w-0 gap-1"):
                                        ui.label("Observação da conferência").classes(
                                            "text-body2 text-weight-medium"
                                        ).style("color:#173b53")
                                        note_input = ui.textarea(
                                            placeholder="Qual evidência sustenta a decisão?"
                                        ).props("outlined rows=1 bg-color=white").classes("w-full")
                                saving = False

                                async def save_inline() -> None:
                                    nonlocal saving
                                    if saving:
                                        return
                                    raw_amount = str(amount_input.value or "").strip()
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
                                    resolved_outcome = "REALIZED" if inferred_closure else str(outcome_input.value or "PENDING")
                                    saving = True
                                    save_button.disable()
                                    try:
                                        check_id = await run.io_bound(
                                            register_particular_mv_check,
                                            access=access, budget_id=budget_id,
                                            outcome=resolved_outcome,
                                            notice_number=str(row.get("notice_number") or "").strip() or None,
                                            attendance_number=str(row.get("attendance_number") or "").strip() or None,
                                            account_value=normalized_amount,
                                            notes=str(note_input.value or "").strip() or None,
                                        )
                                    except Exception:
                                        logger.exception("Falha ao registrar conclusão integrada.")
                                        saving = False
                                        save_button.enable()
                                        ui.notify("Não foi possível registrar a conclusão.", type="negative")
                                        return
                                    ui.notify("Conferência registrada.", type="positive")
                                    after_mv({
                                        "check_id": check_id, "outcome": resolved_outcome,
                                        "account_value": normalized_amount,
                                        "notes": str(note_input.value or "").strip() or None,
                                    })
                                    if not inferred_closure and review_reason != "COMPOSICAO_DIVERGENTE":
                                        finish_case()

                                save_button = ui.button(
                                    "Registrar conclusão", icon="task_alt", on_click=save_inline
                                ).props("unelevated no-caps color=primary size=lg").classes("self-end px-5 rounded-xl")

            ui.label(
                    "A conclusão exige validação das evidências; dados não confirmados "
                    "permanecem sinalizados para revisão."
            ).classes("text-caption text-grey-7 px-1")

    ui.timer(0.05, load, once=True)

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_case_dossier import open_particular_case_dossier
from nicegui_app.services.particular_service import ParticularAccess
from nicegui_app.services.particular_work_queue import (
    get_particular_case_dossier,
    list_particular_work_queue,
)

logger = logging.getLogger(__name__)

GROUPS = {
    "REVISAR_FECHAMENTO": ("Fechamento", "error", "payments"),
    "REVISAR_TRAJETORIA": ("Trajetória", "warning", "timeline"),
    "GRADE_SEM_OPERACAO": ("Sem evidência", "warning", "manage_search"),
    "NEGATIVA_SEM_OPERACAO": ("Sem evidência", "warning", "manage_search"),
    "OPERACAO_COMPETENCIA": ("Em acompanhamento", "primary", "event_available"),
    "OPERACAO_FUTURA": ("Operação futura", "info", "event_upcoming"),
    "FECHAMENTO_IDENTIFICADO": ("Fechamento identificado", "positive", "verified"),
    "CONSULTORIO_SEM_OPERACAO": ("Consultório", "grey", "business_center"),
    "COTACAO": ("Cotação", "grey", "request_quote"),
    "TRANSCRICAO": ("Transcrição", "grey", "description"),
    "ANULADO_CONFIRMADO": ("Anulado", "grey", "block"),
    "INVESTIGACAO_CONCLUIDA": ("Investigação concluída", "positive", "task_alt"),
}
REVIEW_GROUPS = {"REVISAR_FECHAMENTO", "REVISAR_TRAJETORIA"}
INVESTIGATE_GROUPS = {"GRADE_SEM_OPERACAO", "NEGATIVA_SEM_OPERACAO"}
FOLLOW_GROUPS = {"OPERACAO_COMPETENCIA", "OPERACAO_FUTURA"}
ARCHIVE_GROUPS = {
    "FECHAMENTO_IDENTIFICADO", "CONSULTORIO_SEM_OPERACAO",
    "COTACAO", "TRANSCRICAO", "ANULADO_CONFIRMADO", "INVESTIGACAO_CONCLUIDA",
}


def _money(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    amount = Decimal(str(value))
    return "R$ " + f"{amount:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _date(value: Any) -> str:
    if not value:
        return "—"
    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        try:
            return date.fromisoformat(raw[:10]).strftime("%d/%m/%Y")
        except ValueError:
            return raw


def _count(rows: list[dict[str, Any]], groups: set[str]) -> int:
    return sum(str(r.get("work_group") or "") in groups for r in rows)


def _sum(rows: list[dict[str, Any]], groups: set[str]) -> Decimal:
    return sum(
        (Decimal(str(r.get("original_value") or 0)) for r in rows
         if str(r.get("work_group") or "") in groups),
        Decimal("0"),
    )


def _action(row: dict[str, Any]) -> tuple[str, str]:
    code = str(row.get("account_review_reason") or row.get("work_reason") or "").strip()
    actions = {
        "VALIDAR_VALOR_FINAL": ("Confirmar valor final", "A evolução indica fechamento a maior ou a menor."),
        "COMPOSICAO_DIVERGENTE": ("Conferir composição da conta", "Há item, exame ou material que exige validação."),
        "DEVOLUCAO_OU_ESTORNO": ("Validar ajuste financeiro", "Há devolução ou estorno associado ao fechamento."),
        "CONTA_REABERTA": ("Confirmar situação atual", "Há evidência de reabertura da conta."),
        "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": ("Confirmar desfecho da conta", "Existe ajuste, mas não há fechamento conclusivo."),
        "DESFECHO_FINANCEIRO_PENDENTE": ("Confirmar desfecho financeiro", "A evidência disponível ainda não comprova o fechamento."),
        "EVOLUCAO_INCONCLUSIVA": ("Revisar evolução administrativa", "A evolução não permite concluir o desfecho."),
        "MULTIPLOS_EVENTOS_MESMA_DATA": ("Definir sequência dos eventos", "Há eventos na mesma data sem horário real para ordenação."),
        "SEQUENCIA_TEMPORAL_AMBIGUA": ("Confirmar estado atual da conta", "Fechamento e reabertura aparecem na mesma data."),
        "ORCAMENTO_VALOR_APROXIMADO": ("Validar valor e fechamento", "O fechamento referencia orçamento de valor aproximado."),
        "ORIGEM_GRADE_SEM_EVIDENCIA_OPERACIONAL": ("Investigar ausência na grade", "Origem Grade sem ocorrência operacional encontrada."),
        "ORIGEM_NEGATIVA_SEM_EVIDENCIA_OPERACIONAL": ("Investigar ausência de evidência", "Origem Negativa sem ocorrência operacional encontrada."),
        "INVESTIGACAO_CONCLUIDA_REORCAMENTO": ("Investigação concluída", f'Orçamento relacionado: #{row.get("investigation_related_budget_number") or "—"} · Reorçamento confirmado.'),
        "INVESTIGACAO_CONCLUIDA_SEM_RELACAO": ("Investigação concluída", "O indício foi analisado e não possui relação com o orçamento."),
        "INVESTIGACAO_CONCLUIDA_CANCELAMENTO": ("Investigação concluída", "Cancelamento confirmado durante a investigação."),
        "INVESTIGACAO_CONCLUIDA_OUTRO": ("Investigação concluída", "Desfecho operacional registrado durante a investigação."),
    }
    if code in actions:
        return actions[code]
    group = str(row.get("work_group") or "")
    if group == "REVISAR_TRAJETORIA":
        return ("Revisar trajetória operacional", "Há mudança ou conflito que exige validação.")
    if group == "FECHAMENTO_IDENTIFICADO":
        return ("Nenhuma ação imediata", "Fechamento identificado pela evolução administrativa.")
    if group == "OPERACAO_FUTURA":
        return ("Monitorar", f'Operação observada para {_date(row.get("last_observed_operational_date"))}.')
    if group == "OPERACAO_COMPETENCIA":
        return ("Acompanhar evolução", "Há operação identificada na competência.")
    return ("Consultar caso", code.replace("_", " ").title() if code else "Consulte as evidências disponíveis.")


def render_particular_work_queue(*, access: ParticularAccess, competence: str | None = None, render_duplicates: Any | None = None, duplicates_count: int = 0) -> None:
    if not access.can_read:
        ui.label("Você não possui acesso à carteira operacional.")
        return

    state = {"scope": "ACTION", "search": "", "group": "TODOS", "origin": "TODOS"}
    all_rows: list[dict[str, Any]] = []
    state["selected_budget_id"] = None

    with ui.column().classes("w-full gap-3 intel-queue"):
        with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            ui.label("PAINEL OPERACIONAL").classes(
                "text-caption text-weight-bold text-grey-7"
            ).style("letter-spacing: .08em")
            ui.badge("Motor operacional V2").props("outline").classes("text-primary")

        summary = ui.row().classes("w-full gap-3 flex-wrap")
        scope_row = ui.row().classes("intel-tabs w-full gap-2 flex-wrap")

        filters_card = ui.card().classes("intel-filters w-full p-3 shadow-none border rounded-lg")
        with filters_card:
            with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                search = ui.input(
                    "Buscar", placeholder="Orçamento, médico ou atendimento"
                ).props("outlined dense clearable").classes("min-w-[300px] flex-1")
                group_select = ui.select(
                    {"TODOS": "Todas"}, value="TODOS", label="Motivo"
                ).props("outlined dense").classes("min-w-[210px]")
                origin_select = ui.select(
                    {"TODOS": "Todas"}, value="TODOS", label="Origem"
                ).props("outlined dense").classes("min-w-[180px]")

        result_label = ui.label("").classes("text-sm text-grey-7")
        with ui.row().classes("intel-split w-full items-start gap-4 no-wrap"):
            results = ui.column().classes("intel-list gap-2")
            detail_panel = ui.column().classes("intel-detail gap-3")

    def visible_rows() -> list[dict[str, Any]]:
        scope = state["scope"]
        allowed = (
            REVIEW_GROUPS if scope == "ACTION"
            else INVESTIGATE_GROUPS if scope == "INVESTIGATE"
            else FOLLOW_GROUPS if scope == "FOLLOW"
            else ARCHIVE_GROUPS if scope == "ARCHIVE"
            else set(GROUPS)
        )
        rows = [r for r in all_rows if str(r.get("work_group") or "") in allowed]
        if state["group"] != "TODOS":
            rows = [r for r in rows if r.get("work_group") == state["group"]]
        if state["origin"] != "TODOS":
            rows = [r for r in rows if r.get("portfolio_origin") == state["origin"]]
        term = state["search"].casefold().strip()
        if term:
            rows = [r for r in rows if term in " ".join([
                str(r.get("budget_number") or ""), str(r.get("doctor_name") or ""),
                str(r.get("attendance_number") or ""), str(r.get("original_requester") or ""),
            ]).casefold()]
        return rows

    def set_scope(scope: str) -> None:
        state["scope"] = scope
        state["group"] = "TODOS"
        group_select.value = "TODOS"
        filters_card.set_visibility(scope != "DUPLICATES")
        summary.set_visibility(scope != "DUPLICATES")
        detail_panel.set_visibility(scope != "DUPLICATES")
        render_scopes()
        render_rows()

    def render_summary() -> None:
        summary.clear()
        cards = [
            ("priority_high", "Aguardando decisão", REVIEW_GROUPS, "DECIDIR"),
            ("manage_search", "Investigar origem", INVESTIGATE_GROUPS, "INVESTIGAR"),
            ("event", "Em acompanhamento", FOLLOW_GROUPS, "ACOMPANHAR"),
        ]
        with summary:
            for icon, title, groups, kicker in cards:
                with ui.card().classes("intel-summary flex-1 min-w-[220px] gap-1"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(kicker).classes("text-caption text-weight-bold text-primary")
                        ui.icon(icon, size="20px").classes("text-primary")
                    with ui.row().classes("items-center gap-3"):
                        ui.label(str(_count(all_rows, groups))).classes("text-h5 text-weight-bold")
                        ui.label(title).classes("text-body2 text-weight-medium")
                    ui.label(_money(_sum(all_rows, groups)) + " em valores de referência").classes(
                        "text-caption text-grey-7"
                    )

    def render_scopes() -> None:
        scope_row.clear()
        options = [
            ("ACTION", "Decidir", _count(all_rows, REVIEW_GROUPS)),
            ("INVESTIGATE", "Investigar", _count(all_rows, INVESTIGATE_GROUPS)),
            ("FOLLOW", "Acompanhar", _count(all_rows, FOLLOW_GROUPS)),
            *([("DUPLICATES", "Duplicidades", duplicates_count)] if render_duplicates else []),
            ("ARCHIVE", "Outras situações", _count(all_rows, ARCHIVE_GROUPS)),
            ("ALL", "Todos", len(all_rows)),
        ]
        with scope_row:
            for key, label, count in options:
                props = "unelevated no-caps" if state["scope"] == key else "outline no-caps"
                ui.button(
                    f"{label}  {count}", on_click=lambda _=None, key=key: set_scope(key)
                ).props(props)

    def render_rows() -> None:
        rows = visible_rows()
        results.clear()
        if state["scope"] == "DUPLICATES" and render_duplicates:
            result_label.set_text(f"{duplicates_count} relação(ões) entre orçamentos.")
            with results:
                render_duplicates()
            return
        result_label.set_text(f"{len(rows)} caso(s) nesta fila.")
        selected_ids = {str(r.get("budget_id") or "") for r in rows}
        if state["selected_budget_id"] not in selected_ids:
            state["selected_budget_id"] = str(rows[0].get("budget_id") or "") if rows else None
        render_detail()
        with results:
            if not rows:
                with ui.card().classes("w-full p-6"):
                    ui.label("Nenhum caso nesta fila.").classes("text-subtitle1 text-weight-bold")
                    ui.label("Ajuste os filtros ou escolha outra leitura.").classes("text-body2 text-grey-7")
                return

            for row in rows:
                group = str(row.get("work_group") or "")
                label, color, icon = GROUPS.get(group, (group, "grey", "info"))
                action, explanation = _action(row)
                selected = str(row.get("budget_id") or "") == state["selected_budget_id"]
                with ui.card().classes(
                    "intel-case w-full p-0 overflow-hidden" + (" intel-case-selected" if selected else "")
                ):
                    with ui.row().classes("w-full items-stretch no-wrap"):
                        with ui.element("div").classes(
                            "w-[5px] bg-red-5" if group in REVIEW_GROUPS
                            else "w-[5px] bg-orange-5" if group in INVESTIGATE_GROUPS
                            else "w-[5px] bg-blue-5"
                        ):
                            pass
                        with ui.row().classes("flex-1 items-center gap-4 px-4 py-3 flex-wrap"):
                            with ui.column().classes("gap-0 min-w-[90px]"):
                                ui.label(f'#{row.get("budget_number")}').classes("text-subtitle1 text-weight-bold")
                                ui.label(_date(row.get("budget_date"))).classes("text-caption text-grey-7")
                                ui.label(str(row.get("portfolio_origin") or "—").replace("_", " ").title()).classes("text-caption text-grey-6")

                            with ui.column().classes("gap-1 flex-1 min-w-[190px]"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon(icon, size="19px").classes("text-primary")
                                    ui.label(action).classes("text-body1 text-weight-bold")
                                    ui.badge(label, color=color).props("outline")
                                ui.label(explanation).classes("text-body2 text-grey-7")
                                doctor = str(row.get("doctor_name") or "").strip()
                                if doctor:
                                    ui.label(doctor).classes("text-caption text-grey-6")

                            with ui.column().classes("gap-0 min-w-[110px]"):
                                ui.label("Referência").classes("text-caption text-grey-6")
                                ui.label(_money(row.get("original_value"))).classes("text-body2 text-weight-bold")

                            with ui.column().classes("gap-0 min-w-[125px]"):
                                attendance = row.get("attendance_number")
                                ui.label(f"Atend. {attendance}" if attendance else "Sem atendimento vinculado").classes("text-body2")
                                last_date = row.get("last_observed_operational_date")
                                ui.label(
                                    _date(last_date) if last_date else "Data não identificada"
                                ).classes("text-caption text-grey-7")

                            budget_id = str(row.get("budget_id") or "")
                            ui.button(
                                "Analisar" if group in REVIEW_GROUPS else "Visualizar",
                                icon="arrow_forward",
                                on_click=lambda _=None, bid=budget_id: select_case(bid),
                            ).props("unelevated no-caps")

    def select_case(budget_id: str) -> None:
        state["selected_budget_id"] = budget_id
        render_rows()

    async def load_evidence(budget_id: str, container: Any) -> None:
        """Consulta factual sob demanda, sem classificar ou alterar dados."""
        if container.is_deleted:
            return
        container.clear()
        with container:
            ui.spinner(size="sm").classes("text-primary")
            ui.label("Consultando fontes vinculadas...").classes("text-caption text-grey-7")
        try:
            dossier = await run.io_bound(get_particular_case_dossier, budget_id=budget_id)
        except Exception:
            logger.exception("Falha ao consultar evidências do orçamento %s", budget_id)
            if not container.is_deleted:
                container.clear()
                with container:
                    ui.label("Não foi possível consultar as fontes. Tente novamente.").classes(
                        "text-body2 text-negative"
                    )
            return
        if container.is_deleted or state["selected_budget_id"] != budget_id:
            return
        occurrences = dossier.get("occurrences") or []
        events = dossier.get("events") or []
        evolutions = dossier.get("evolutions") or []
        candidates = dossier.get("investigation_candidates") or []
        original_values = dossier.get("original_values") or []
        mv_notices = dossier.get("mv_notices") or []
        mv_accounts = dossier.get("mv_accounts") or []
        original = original_values[0] if original_values else {}
        linked_mv_ids = {str(item.get("id")) for item in mv_accounts}
        matched_notices = sorted({
            str(item.get("notice_number"))
            for item in mv_notices
            if str(item.get("account_record_id")) in linked_mv_ids
        })
        original_total = original.get("total_value")
        mv_totals = [
            item.get("account_total") for item in mv_accounts
            if item.get("account_total") is not None
        ]
        container.clear()
        event_labels = {
            "ACCOUNT_ADJUSTED": "Ajuste registrado na conta",
            "ACCOUNT_CLOSED": "Fechamento de conta identificado",
            "ACCOUNT_REOPENED": "Reabertura de conta identificada",
            "ACCOUNT_OPENED": "Abertura de conta identificada",
        }
        closure_labels = {
            "ACCORDING_TO_BUDGET": "Conforme orçamento",
            "HIGHER": "Valor maior que o orçamento",
            "LOWER": "Valor menor que o orçamento",
            "WITH_ADJUSTMENT": "Com ajuste",
            "OTHER": "Outra modalidade",
        }
        case_row = dossier.get("queue") or {}
        account_state = str(case_row.get("account_status") or "").upper()
        event_types = {str(item.get("event_type") or "").upper() for item in events}
        intent_notes = [
            str(item.get("notes_original") or "").strip()
            for item in occurrences
            if str(item.get("notes_original") or "").strip()
        ]
        review_flags = [
            item for item in events if item.get("requires_review") is True
        ]
        findings: list[tuple[str, str, str]] = []
        if account_state == "CLOSED":
            findings.append((
                "Estado financeiro registrado",
                "A visão consolidada da conta indica CLOSED. Isso não comprova pagamento "
                "nem resolve automaticamente a situação operacional.",
                "info",
            ))
        elif account_state:
            findings.append((
                "Estado financeiro disponível",
                f"Situação informada pelo motor: {account_state}. "
                "Consulte o dossiê antes de registrar um desfecho.",
                "info",
            ))
        if "ACCOUNT_ADJUSTED" in event_types:
            findings.append((
                "Ajuste financeiro identificado",
                "Há registro de ajuste na conta. Um ajuste isolado não comprova "
                "fechamento, pagamento ou valor final confirmado.",
                "warning",
            ))
        if "ACCOUNT_CLOSED" in event_types:
            findings.append((
                "Evento de fechamento identificado",
                "Existe evento interpretado como fechamento. Confira sua data, "
                "modalidade e eventuais eventos posteriores.",
                "info",
            ))
        if review_flags:
            findings.append((
                "Validação humana indicada",
                f"{len(review_flags)} evento(s) financeiro(s) sinalizado(s) "
                "para revisão pela fonte de interpretação.",
                "warning",
            ))
        if len({str(item.get("notice_number")) for item in occurrences if item.get("notice_number")}) > 1:
            findings.append((
                "Mais de um aviso operacional",
                "Foram identificados números de aviso distintos neste orçamento. "
                "A relação entre eles precisa ser conferida.",
                "warning",
            ))
        if intent_notes:
            findings.append((
                "Observações operacionais disponíveis",
                "Há anotações da grade. Expressões de intenção, como 'vai cancelar' "
                "ou 'vai transferir', não confirmam que o evento ocorreu.",
                "info",
            ))
        if candidates:
            findings.append((
                "Possíveis relações para investigação",
                "Há ocorrências candidatas a vínculo; nenhuma relação é "
                "confirmada somente por esta busca.",
                "warning",
            ))
        if mv_accounts:
            findings.append((
                "Correspondência de aviso com conta MV",
                f"{len(mv_accounts)} registro(s) de conta MV associado(s) a "
                f"{len(matched_notices)} aviso(s) da grade. Confira o atendimento "
                "e o histórico antes de interpretar o desfecho.",
                "info",
            ))
        elif occurrences:
            findings.append((
                "Sem correspondência MV nesta consulta",
                "Nenhuma conta MV foi vinculada aos avisos consultados. "
                "Isso não comprova ausência de conta ou de atendimento.",
                "info",
            ))
        if not findings:
            findings.append((
                "Sem conclusão adicional nesta consulta",
                "Os registros retornados não sustentam uma conclusão automática. "
                "Confira o histórico e as fontes antes de decidir.",
                "info",
            ))
        follow_ups: list[str] = []
        if "ACCOUNT_ADJUSTED" in event_types or review_flags:
            follow_ups.append("Verificar no MV a sequência de eventos e o desfecho da conta.")
        if len({str(item.get("notice_number")) for item in occurrences if item.get("notice_number")}) > 1:
            follow_ups.append("Conferir se os avisos representam o mesmo atendimento.")
        if intent_notes:
            follow_ups.append("Confirmar se as intenções registradas na grade se concretizaram.")
        if candidates:
            follow_ups.append("Validar os vínculos sugeridos antes de relacionar orçamentos.")
        if mv_accounts:
            follow_ups.append(
                "Conferir atendimento, datas e valores das contas MV vinculadas."
            )
        elif occurrences:
            follow_ups.append(
                "Pesquisar no MV os avisos sem correspondência nesta consulta."
            )
        if not follow_ups:
            follow_ups.append("Conferir o dossiê completo antes de registrar a decisão.")
        container.clear()
        with container:
            with ui.column().classes("w-full gap-2 p-3").style(
                "background:#f4f8fc;border:1px solid #dce9f3;border-radius:12px"
            ):
                ui.label("ANÁLISE DO MOTOR").classes(
                    "text-caption text-weight-bold text-primary"
                )
                priority_findings = sorted(
                    findings, key=lambda item: item[2] != "warning"
                )
                for heading, detail, level in priority_findings[:3]:
                    with ui.row().classes("w-full items-start gap-2 no-wrap"):
                        ui.icon(
                            "error_outline" if level == "warning" else "info_outline",
                            size="18px",
                        ).classes("text-amber-8" if level == "warning" else "text-blue-7")
                        with ui.column().classes("gap-0 flex-1"):
                            ui.label(heading).classes("text-body2 text-weight-bold")
                            ui.label(detail).classes("text-caption text-grey-8")
                ui.separator()
                ui.label("Próxima ação sugerida").classes(
                    "text-body2 text-weight-bold"
                )
                ui.label(follow_ups[0]).classes("text-body2")
                ui.label(
                    "Leitura de apoio, não é uma decisão automática."
                ).classes("text-caption text-grey-7")

            with ui.expansion(
                "Conferir fontes e histórico", icon="fact_check"
            ).classes("w-full"):
                with ui.column().classes("w-full gap-3"):
                    with ui.row().classes("w-full gap-2 flex-wrap"):
                        for name, count in (
                            ("Grade", len(occurrences)),
                            ("Eventos", len(events)),
                            ("Evoluções", len(evolutions)),
                            ("Relações", len(candidates)),
                        ):
                            with ui.column().classes("intel-evidence-count flex-1 gap-0 p-2"):
                                ui.label(str(count)).classes("text-subtitle1 text-weight-bold")
                                ui.label(name).classes("text-caption text-grey-7")
                    with ui.row().classes("w-full gap-3 flex-wrap"):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label("Original vigente").classes("text-caption text-grey-7")
                            ui.label(_money(original_total)).classes("text-body2 text-weight-bold")
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label("Contas MV vinculadas").classes("text-caption text-grey-7")
                            ui.label(str(len(mv_accounts))).classes("text-body2 text-weight-bold")
                    if original:
                        ui.label(
                            "Procedimento: " + _money(original.get("procedure_value"))
                            + " · Materiais: " + _money(original.get("material_value"))
                        ).classes("text-caption text-grey-7")
                    if mv_accounts:
                        with ui.expansion(
                            "Registros MV vinculados", icon="receipt_long"
                        ).classes("w-full"):
                            for account in mv_accounts[:10]:
                                record_id = str(account.get("id"))
                                notices = sorted({
                                    str(item.get("notice_number"))
                                    for item in mv_notices
                                    if str(item.get("account_record_id")) == record_id
                                })
                                ui.label(
                                    "Aviso(s): " + (", ".join(notices) or "não informado")
                                    + " · Atendimento: "
                                    + str(account.get("attendance_number") or "não informado")
                                    + " · Conta: " + str(account.get("account_number") or "não informada")
                                ).classes("text-body2 text-weight-medium")
                                ui.label(
                                    "Valor registrado: " + _money(account.get("account_total"))
                                    + " · " + (
                                        "Fechada" if account.get("is_closed") is True
                                        else "Aberta" if account.get("is_closed") is False
                                        else "Estado não informado"
                                    )
                                ).classes("text-caption text-grey-7")
                    if len(priority_findings) > 3 or len(follow_ups) > 1:
                        with ui.expansion(
                            "Outros achados e verificações", icon="list_alt"
                        ).classes("w-full"):
                            for heading, detail, _ in priority_findings[3:]:
                                ui.label(heading).classes("text-body2 text-weight-bold")
                                ui.label(detail).classes("text-caption text-grey-7")
                            for task in follow_ups[1:]:
                                ui.label("• " + task).classes("text-caption text-grey-7")
                    ui.label(
                        "Dados da importação e fontes consultadas. Sem vínculo não significa "
                        "ausência de conta. Valor MV não confirma pagamento nem valor final."
                    ).classes("text-caption text-grey-7")
                if occurrences:
                    with ui.expansion(
                        f"Grade operacional · {len(occurrences)} registro(s)",
                        icon="event_note",
                    ).classes("w-full"):
                        for item in occurrences[:10]:
                            with ui.column().classes("w-full gap-1 py-2"):
                                ui.label(
                                    "Aviso " + str(item.get("notice_number") or "não informado")
                                ).classes("text-body2 text-weight-bold")
                                ui.label(
                                    "Procedimento: " + _date(item.get("procedure_date"))
                                    + " · Local: " + str(item.get("location") or "não informado")
                                ).classes("text-body2")
                                if item.get("notes_original"):
                                    ui.label(
                                        "Observação da origem: " + str(item["notes_original"])
                                    ).classes("text-caption text-grey-7")
                if events:
                    with ui.expansion(
                        f"Histórico financeiro · {len(events)} evento(s)",
                        icon="account_balance_wallet",
                        value=True,
                    ).classes("w-full"):
                        for item in events[:10]:
                            code = str(item.get("event_type") or "")
                            with ui.column().classes("w-full gap-1 py-2"):
                                ui.label(
                                    event_labels.get(code, code.replace("_", " ").title() or "Evento")
                                ).classes("text-body2 text-weight-bold")
                                ui.label(
                                    "Data: " + _date(item.get("event_at"))
                                    + " · Modalidade: "
                                    + closure_labels.get(
                                        str(item.get("closure_mode") or ""),
                                        str(item.get("closure_mode") or "não informada"),
                                    )
                                ).classes("text-body2")
                                if item.get("interpretation_details"):
                                    ui.label(
                                        str(item["interpretation_details"])
                                    ).classes("text-caption text-grey-7")
                                if item.get("requires_review"):
                                    ui.badge("Requer validação humana", color="warning")
                if evolutions:
                    with ui.expansion(
                        f"Evoluções administrativas · {len(evolutions)} registro(s)",
                        icon="history",
                    ).classes("w-full"):
                        for item in evolutions[:10]:
                            with ui.column().classes("w-full gap-1 py-2"):
                                ui.label(
                                    str(item.get("evolution_type") or "Evolução administrativa")
                                ).classes("text-body2 text-weight-bold")
                                ui.label(
                                    "Registrada em " + _date(item.get("evolution_recorded_at"))
                                ).classes("text-caption text-grey-7")
                                if item.get("description_raw"):
                                    ui.label(
                                        str(item["description_raw"])
                                    ).classes("text-body2 whitespace-pre-wrap break-words")
                if candidates:
                    with ui.expansion(
                        f"Possíveis relações · {len(candidates)} indício(s)",
                        icon="manage_search",
                    ).classes("w-full"):
                        for item in candidates[:10]:
                            ui.label(
                                "Aviso " + str(item.get("notice_number") or "não informado")
                                + " · " + _date(item.get("procedure_date"))
                            ).classes("text-body2")
                        ui.label(
                            "Indícios de associação, ainda não confirmados."
                        ).classes("text-caption text-grey-7")
                ui.label(
                    "Exibidos até 10 registros por categoria. Ausência nesta consulta "
                    "não comprova ausência na origem. XML e contas MV não são consultados "
                    "diretamente neste resumo."
                ).classes("text-caption text-grey-7")

    def render_detail() -> None:
        detail_panel.clear()
        if state["scope"] == "DUPLICATES":
            return
        selected = next(
            (r for r in all_rows if str(r.get("budget_id") or "") == state["selected_budget_id"]),
            None,
        )
        with detail_panel:
            if not selected:
                with ui.card().classes("intel-detail-card w-full p-5"):
                    ui.icon("fact_check", size="36px").classes("text-blue-4")
                    ui.label("Selecione um orçamento").classes("text-subtitle1 text-weight-bold")
                    ui.label("Escolha um caso para visualizar seu resumo.").classes("text-body2 text-grey-7")
                return
            group = str(selected.get("work_group") or "")
            label, color, icon = GROUPS.get(group, (group, "grey", "info"))
            action, explanation = _action(selected)
            with ui.card().classes("intel-detail-card w-full p-5 gap-4"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    ui.label("RESUMO DO CASO").classes("text-caption text-weight-bold text-primary")
                    ui.badge(label, color=color).props("outline")
                ui.label(f'Orçamento #{selected.get("budget_number")}').classes("text-h5 text-weight-bold")
                ui.label(str(selected.get("doctor_name") or "Médico não informado")).classes("text-body2 text-grey-7")
                ui.separator()
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label("Data do orçamento").classes("text-caption text-grey-7")
                        ui.label(_date(selected.get("budget_date"))).classes("text-body2 text-weight-medium")
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label("Origem").classes("text-caption text-grey-7")
                        ui.label(str(selected.get("portfolio_origin") or "—").replace("_", " ").title()).classes("text-body2 text-weight-medium")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label("Valor de referência").classes("text-caption text-grey-7")
                        ui.label(_money(selected.get("original_value"))).classes("text-subtitle1 text-weight-bold")
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label("Atendimento").classes("text-caption text-grey-7")
                        ui.label(str(selected.get("attendance_number") or "Não vinculado")).classes("text-body2 text-weight-medium")
                ui.separator()
                ui.label("LEITURA DO MOTOR").classes("text-caption text-weight-bold text-primary")
                with ui.column().classes("intel-insight w-full gap-2 p-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon(icon).classes("text-primary")
                        ui.label(action).classes("text-body1 text-weight-bold")
                    ui.label(explanation).classes("text-body2 text-grey-7")
                    ui.label("Classificação atual da fila, não uma conclusão definitiva.").classes("text-caption text-grey-7")
                with ui.expansion("Dados para conferência", icon="fact_check").classes(
                    "intel-evidence w-full"
                ):
                    ui.label(
                        "Última data operacional observada: " + _date(
                            selected.get("last_observed_operational_date")
                        )
                    ).classes("text-body2")
                    ui.label(
                        "Os dados acima são um resumo da fila. Consulte o dossiê "
                        "para verificar fontes, eventos e evoluções."
                    ).classes("text-body2 text-grey-7")
                evidence_panel = ui.column().classes("w-full gap-2")
                ui.button(
                    "Consultar evidências vinculadas",
                    icon="fact_check",
                    on_click=lambda bid=str(selected.get("budget_id") or ""), panel=evidence_panel:
                        load_evidence(bid, panel),
                ).props("outline no-caps").classes("w-full")
                ui.button(
                    "Abrir análise completa", icon="open_in_new",
                    on_click=lambda bid=str(selected.get("budget_id") or ""): open_case(bid),
                ).props("unelevated no-caps").classes("w-full")
                ui.label("As evidências detalhadas e decisões permanecem no dossiê completo.").classes("text-caption text-grey-7")

    def refresh() -> None:
        state["search"] = str(search.value or "").strip()
        state["group"] = str(group_select.value or "TODOS")
        state["origin"] = str(origin_select.value or "TODOS")
        render_rows()

    async def reload_after_resolution() -> None:
        """Recarrega a fotografia da fila depois de uma decisão humana."""
        result_label.set_text("Atualizando prioridades...")
        try:
            rows = await run.io_bound(list_particular_work_queue, competence=competence)
        except Exception:
            logger.exception("Falha ao atualizar particular_work_queue_v1")
            ui.notify(
                "A decisão foi registrada, mas não foi possível atualizar a fila automaticamente.",
                type="warning",
            )
            return

        all_rows.clear()
        all_rows.extend(rows)
        group_select.options = {
            "TODOS": "Todas",
            **{
                key: value[0]
                for key, value in GROUPS.items()
                if any(r.get("work_group") == key for r in all_rows)
            },
        }
        origins = sorted({
            str(r.get("portfolio_origin") or "")
            for r in all_rows
            if r.get("portfolio_origin")
        })
        origin_select.options = {
            "TODOS": "Todas",
            **{x: x.replace("_", " ").title() for x in origins},
        }
        render_summary()
        render_scopes()
        render_rows()

    def open_case(budget_id: str) -> None:
        open_particular_case_dossier(
            access=access,
            budget_id=budget_id,
            on_resolved=lambda: ui.timer(0.05, reload_after_resolution, once=True),
        )

    async def load() -> None:
        result_label.set_text("Carregando prioridades...")
        try:
            rows = await run.io_bound(list_particular_work_queue, competence=competence)
        except Exception:
            logger.exception("Falha ao carregar particular_work_queue_v1")
            result_label.set_text("Não foi possível carregar a Central de Trabalho.")
            ui.notify("Não foi possível carregar a fila inteligente.", type="negative")
            return
        all_rows.clear()
        all_rows.extend(rows)
        group_select.options = {
            "TODOS": "Todas",
            **{key: value[0] for key, value in GROUPS.items() if any(r.get("work_group") == key for r in all_rows)},
        }
        origins = sorted({str(r.get("portfolio_origin") or "") for r in all_rows if r.get("portfolio_origin")})
        origin_select.options = {"TODOS": "Todas", **{x: x.replace("_", " ").title() for x in origins}}
        render_summary()
        render_scopes()
        render_rows()

    search.on("update:model-value", lambda _: refresh())
    group_select.on("update:model-value", lambda _: refresh())
    origin_select.on("update:model-value", lambda _: refresh())
    ui.timer(0.05, load, once=True)

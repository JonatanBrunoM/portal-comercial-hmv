from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_case_dossier import open_particular_case_dossier
from nicegui_app.services.particular_service import ParticularAccess
from nicegui_app.services.particular_work_queue import list_particular_work_queue

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
}
REVIEW_GROUPS = {"REVISAR_FECHAMENTO", "REVISAR_TRAJETORIA"}
INVESTIGATE_GROUPS = {"GRADE_SEM_OPERACAO", "NEGATIVA_SEM_OPERACAO"}
FOLLOW_GROUPS = {"OPERACAO_COMPETENCIA", "OPERACAO_FUTURA"}
ARCHIVE_GROUPS = {
    "FECHAMENTO_IDENTIFICADO", "CONSULTORIO_SEM_OPERACAO",
    "COTACAO", "TRANSCRICAO", "ANULADO_CONFIRMADO",
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


def render_particular_work_queue(*, access: ParticularAccess) -> None:
    if not access.can_read:
        ui.label("Você não possui acesso à carteira operacional.")
        return

    state = {"scope": "ACTION", "search": "", "group": "TODOS", "origin": "TODOS"}
    all_rows: list[dict[str, Any]] = []

    with ui.column().classes("w-full gap-4"):
        with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
            with ui.column().classes("gap-0"):
                ui.label("CENTRAL DE TRABALHO").classes("text-caption text-weight-bold text-primary")
                ui.label("Prioridades do Particular").classes("text-h4 text-weight-bold")
                ui.label(
                    "A fila mostra primeiro o que exige decisão. Evidências e carteira completa continuam disponíveis sem poluir o trabalho diário."
                ).classes("text-body2 text-grey-7")
            ui.badge("Motor operacional V1").props("outline").classes("text-primary")

        summary = ui.row().classes("w-full gap-3 flex-wrap")
        scope_row = ui.row().classes("w-full gap-2 flex-wrap")

        with ui.card().classes("w-full p-3 shadow-sm"):
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
        results = ui.column().classes("w-full gap-2")

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
        render_scopes()
        render_rows()

    def render_summary() -> None:
        summary.clear()
        cards = [
            ("priority_high", "Decisão necessária", REVIEW_GROUPS, "AÇÃO", "Casos que dependem de validação humana"),
            ("manage_search", "Investigar", INVESTIGATE_GROUPS, "INVESTIGAR", "Origem operacional sem evidência correspondente"),
            ("event", "Monitorar", FOLLOW_GROUPS, "ACOMPANHAR", "Operações identificadas que ainda estão em trajetória"),
        ]
        with summary:
            for icon, title, groups, kicker, subtitle in cards:
                with ui.card().classes("flex-1 min-w-[260px] p-4 gap-1 shadow-sm"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(kicker).classes("text-caption text-weight-bold text-primary")
                        ui.icon(icon, size="23px").classes("text-primary")
                    ui.label(str(_count(all_rows, groups))).classes("text-h4 text-weight-bold")
                    ui.label(title).classes("text-subtitle1 text-weight-bold")
                    ui.label(_money(_sum(all_rows, groups))).classes("text-body2 text-weight-medium")
                    ui.label(subtitle).classes("text-caption text-grey-7")

    def render_scopes() -> None:
        scope_row.clear()
        options = [
            ("ACTION", "Decisão necessária", _count(all_rows, REVIEW_GROUPS)),
            ("INVESTIGATE", "Investigar", _count(all_rows, INVESTIGATE_GROUPS)),
            ("FOLLOW", "Monitorar", _count(all_rows, FOLLOW_GROUPS)),
            ("ARCHIVE", "Carteira completa / resolvidos", _count(all_rows, ARCHIVE_GROUPS)),
            ("ALL", "Todos", len(all_rows)),
        ]
        with scope_row:
            for key, label, count in options:
                props = "unelevated no-caps" if state["scope"] == key else "outline no-caps"
                ui.button(
                    f"{label} · {count}", on_click=lambda _=None, key=key: set_scope(key)
                ).props(props)

    def render_rows() -> None:
        rows = visible_rows()
        results.clear()
        result_label.set_text(f"{len(rows)} caso(s) nesta fila.")
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
                with ui.card().classes("w-full p-0 shadow-sm overflow-hidden"):
                    with ui.row().classes("w-full items-stretch no-wrap"):
                        with ui.element("div").classes(
                            "w-[5px] bg-red-5" if group in REVIEW_GROUPS
                            else "w-[5px] bg-orange-5" if group in INVESTIGATE_GROUPS
                            else "w-[5px] bg-blue-5"
                        ):
                            pass
                        with ui.row().classes("flex-1 items-center gap-4 p-4 flex-wrap"):
                            with ui.column().classes("gap-0 min-w-[135px]"):
                                ui.label(f'#{row.get("budget_number")}').classes("text-subtitle1 text-weight-bold")
                                ui.label(_date(row.get("budget_date"))).classes("text-caption text-grey-7")
                                ui.label(str(row.get("portfolio_origin") or "—").replace("_", " ").title()).classes("text-caption text-grey-6")

                            with ui.column().classes("gap-1 flex-1 min-w-[330px]"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon(icon, size="19px").classes("text-primary")
                                    ui.label(action).classes("text-body1 text-weight-bold")
                                    ui.badge(label, color=color).props("outline")
                                ui.label(explanation).classes("text-body2 text-grey-7")
                                doctor = str(row.get("doctor_name") or "").strip()
                                if doctor:
                                    ui.label(doctor).classes("text-caption text-grey-6")

                            with ui.column().classes("gap-0 min-w-[145px]"):
                                ui.label("Valor de referência").classes("text-caption text-grey-6")
                                ui.label(_money(row.get("original_value"))).classes("text-body2 text-weight-bold")

                            with ui.column().classes("gap-0 min-w-[180px]"):
                                attendance = row.get("attendance_number")
                                ui.label(f"Atend. {attendance}" if attendance else "Sem atendimento vinculado").classes("text-body2")
                                last_date = row.get("last_observed_operational_date")
                                ui.label(
                                    f"Última data observada: {_date(last_date)}" if last_date
                                    else "Sem data operacional identificada"
                                ).classes("text-caption text-grey-7")

                            budget_id = str(row.get("budget_id") or "")
                            ui.button(
                                "Abrir decisão" if group in REVIEW_GROUPS else "Abrir caso",
                                icon="arrow_forward",
                                on_click=lambda _=None, bid=budget_id: open_case(bid),
                            ).props("unelevated no-caps")

    def refresh() -> None:
        state["search"] = str(search.value or "").strip()
        state["group"] = str(group_select.value or "TODOS")
        state["origin"] = str(origin_select.value or "TODOS")
        render_rows()

    async def reload_after_resolution() -> None:
        """Recarrega a fotografia da fila depois de uma decisão humana."""
        result_label.set_text("Atualizando prioridades...")
        try:
            rows = await run.io_bound(list_particular_work_queue)
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
            rows = await run.io_bound(list_particular_work_queue)
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

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import ui, run

from nicegui_app.components.particular_mv_dialog import open_particular_mv_dialog
from nicegui_app.components.particular_sheet_budget_dialog import open_particular_sheet_budget_dialog
from nicegui_app.services.particular_service import ParticularAccess
from nicegui_app.services.particular_work_queue import list_particular_work_queue

logger = logging.getLogger(__name__)

GROUPS = {
    "REVISAR_FECHAMENTO": ("Revisar fechamento", "error", "rule"),
    "REVISAR_TRAJETORIA": ("Revisar trajetória", "warning", "timeline"),
    "GRADE_SEM_OPERACAO": ("Grade sem evidência", "warning", "search"),
    "NEGATIVA_SEM_OPERACAO": ("Negativa sem evidência", "warning", "search"),
    "OPERACAO_COMPETENCIA": ("Operação na competência", "primary", "event_available"),
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
RESOLVED_GROUPS = {
    "FECHAMENTO_IDENTIFICADO", "CONSULTORIO_SEM_OPERACAO",
    "COTACAO", "TRANSCRICAO", "ANULADO_CONFIRMADO",
}


def _money(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    amount = Decimal(str(value))
    text = f"{amount:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {text}"


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
    return sum(str(row.get("work_group") or "") in groups for row in rows)


def _sum(rows: list[dict[str, Any]], groups: set[str]) -> Decimal:
    return sum(
        (Decimal(str(row.get("original_value") or 0)) for row in rows
         if str(row.get("work_group") or "") in groups),
        Decimal("0"),
    )


def _reason(row: dict[str, Any]) -> str:
    reason = str(row.get("account_review_reason") or row.get("work_reason") or "").strip()
    labels = {
        "VALIDAR_VALOR_FINAL": "Confirmar o valor final da conta",
        "COMPOSICAO_DIVERGENTE": "Composição da conta exige conferência",
        "COBRANCA_EXTERNA_OU_TERCEIRO": "Há cobrança externa ou por terceiro",
        "ORCAMENTO_VALOR_APROXIMADO": "Orçamento possui valor aproximado",
        "DEVOLUCAO_OU_ESTORNO": "Há devolução ou estorno",
        "CONTA_REABERTA": "Conta reaberta",
        "AJUSTE_SEM_FECHAMENTO_CONCLUSIVO": "Ajuste sem fechamento conclusivo",
        "DESFECHO_FINANCEIRO_PENDENTE": "Desfecho financeiro pendente",
        "EVOLUCAO_INCONCLUSIVA": "Evolução administrativa inconclusiva",
        "MULTIPLOS_EVENTOS_MESMA_DATA": "Múltiplos eventos na mesma data",
        "SEQUENCIA_TEMPORAL_AMBIGUA": "Sequência temporal ambígua",
        "ORIGEM_GRADE_SEM_EVIDENCIA_OPERACIONAL": "Origem Grade sem evidência operacional encontrada",
        "ORIGEM_NEGATIVA_SEM_EVIDENCIA_OPERACIONAL": "Origem Negativa sem evidência operacional encontrada",
        "FECHAMENTO_ADMINISTRATIVO_IDENTIFICADO": "Fechamento administrativo identificado pelo motor",
        "OPERACAO_NA_COMPETENCIA": "Operação identificada na competência",
        "OPERACAO_EM_COMPETENCIA_POSTERIOR": "Operação identificada em competência posterior",
    }
    return labels.get(reason, reason.replace("_", " ").title() if reason else "Acompanhar evidências")


def render_particular_work_queue(*, access: ParticularAccess) -> None:
    """Central diária orientada por exceção sobre particular_work_queue_v1."""
    if not access.can_read:
        ui.label("Você não possui acesso à carteira operacional.")
        return

    state = {"scope": "ACTION", "search": "", "group": "TODOS", "origin": "TODOS"}
    all_rows: list[dict[str, Any]] = []

    with ui.column().classes("w-full gap-5"):
        with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
            with ui.column().classes("gap-1"):
                ui.label("CENTRAL DE ACOMPANHAMENTO").classes("text-caption text-weight-bold text-primary")
                ui.label("O que precisa da sua atenção").classes("text-h4 text-weight-bold")
                ui.label(
                    "O motor cruza carteira, grades e evolução administrativa para separar ação, investigação e acompanhamento."
                ).classes("text-body2 text-grey-7")
            ui.badge("Motor operacional V1").props("outline").classes("text-primary")

        summary = ui.row().classes("w-full gap-3 flex-wrap")
        scope_row = ui.row().classes("w-full gap-2 flex-wrap")
        with ui.card().classes("w-full p-4 shadow-sm"):
            with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                search = ui.input(
                    "Buscar",
                    placeholder="Orçamento, médico ou atendimento",
                ).props("outlined dense clearable").classes("min-w-[280px] flex-1")
                group_select = ui.select(
                    {"TODOS": "Todas as situações"}, value="TODOS", label="Situação"
                ).props("outlined dense").classes("min-w-[220px]")
                origin_select = ui.select(
                    {"TODOS": "Todas as origens"}, value="TODOS", label="Origem"
                ).props("outlined dense").classes("min-w-[190px]")
        result_label = ui.label("").classes("text-sm text-grey-7")
        results = ui.column().classes("w-full gap-2")

    def visible_rows() -> list[dict[str, Any]]:
        rows = all_rows
        scope = state["scope"]
        if scope == "ACTION":
            allowed = REVIEW_GROUPS
        elif scope == "INVESTIGATE":
            allowed = INVESTIGATE_GROUPS
        elif scope == "FOLLOW":
            allowed = FOLLOW_GROUPS
        elif scope == "RESOLVED":
            allowed = RESOLVED_GROUPS
        else:
            allowed = set(GROUPS)
        rows = [r for r in rows if str(r.get("work_group") or "") in allowed]
        if state["group"] != "TODOS":
            rows = [r for r in rows if r.get("work_group") == state["group"]]
        if state["origin"] != "TODOS":
            rows = [r for r in rows if r.get("portfolio_origin") == state["origin"]]
        term = state["search"].casefold().strip()
        if term:
            rows = [
                r for r in rows
                if term in " ".join([
                    str(r.get("budget_number") or ""),
                    str(r.get("doctor_name") or ""),
                    str(r.get("attendance_number") or ""),
                    str(r.get("original_requester") or ""),
                ]).casefold()
            ]
        return rows

    def render_summary() -> None:
        summary.clear()
        cards = [
            ("error_outline", "Precisa de análise", REVIEW_GROUPS, "Casos com decisão humana necessária"),
            ("manage_search", "Investigar", INVESTIGATE_GROUPS, "Origem operacional sem evidência encontrada"),
            ("verified", "Fechamento identificado", {"FECHAMENTO_IDENTIFICADO"}, "Identificado pela evolução administrativa"),
            ("event", "Acompanhamento", FOLLOW_GROUPS, "Operação identificada nas grades"),
        ]
        with summary:
            for icon, title, groups, subtitle in cards:
                with ui.card().classes("flex-1 min-w-[220px] p-4 gap-1 shadow-sm"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.icon(icon, size="24px").classes("text-primary")
                        ui.label(str(_count(all_rows, groups))).classes("text-h5 text-weight-bold")
                    ui.label(title).classes("text-subtitle2 text-weight-bold")
                    ui.label(_money(_sum(all_rows, groups))).classes("text-body2 text-weight-medium")
                    ui.label(subtitle).classes("text-caption text-grey-7")

    def render_scopes() -> None:
        scope_row.clear()
        options = [
            ("ACTION", "Precisa de ação", _count(all_rows, REVIEW_GROUPS)),
            ("INVESTIGATE", "Investigar", _count(all_rows, INVESTIGATE_GROUPS)),
            ("FOLLOW", "Acompanhamento", _count(all_rows, FOLLOW_GROUPS)),
            ("RESOLVED", "Fora da fila principal", _count(all_rows, RESOLVED_GROUPS)),
            ("ALL", "Todos", len(all_rows)),
        ]
        with scope_row:
            for key, label, count in options:
                props = "unelevated no-caps" if state["scope"] == key else "outline no-caps"
                ui.button(
                    f"{label} · {count}",
                    on_click=lambda _=None, key=key: set_scope(key),
                ).props(props)

    def render_rows() -> None:
        rows = visible_rows()
        results.clear()
        result_label.set_text(f"{len(rows)} orçamento(s) nesta leitura.")
        with results:
            if not rows:
                with ui.card().classes("w-full p-6"):
                    ui.label("Nenhum orçamento encontrado.").classes("text-subtitle1 text-weight-bold")
                    ui.label("Ajuste os filtros ou escolha outra leitura.").classes("text-body2 text-grey-7")
                return
            for row in rows:
                group = str(row.get("work_group") or "")
                label, color, icon = GROUPS.get(group, (group, "grey", "info"))
                with ui.card().classes("w-full p-4 shadow-sm"):
                    with ui.row().classes("w-full items-center gap-4 flex-wrap"):
                        with ui.row().classes("items-center gap-3 min-w-[235px]"):
                            ui.icon(icon, size="25px").classes("text-primary")
                            with ui.column().classes("gap-0"):
                                ui.label(f'#{row.get("budget_number")}').classes("text-subtitle1 text-weight-bold")
                                ui.label(_date(row.get("budget_date"))).classes("text-caption text-grey-7")
                        with ui.column().classes("gap-0 flex-1 min-w-[260px]"):
                            ui.label(label).classes("text-body2 text-weight-bold")
                            ui.label(_reason(row)).classes("text-caption text-grey-7")
                            doctor = str(row.get("doctor_name") or "").strip()
                            if doctor:
                                ui.label(doctor).classes("text-caption text-grey-6")
                        with ui.column().classes("gap-0 min-w-[150px]"):
                            ui.label(_money(row.get("original_value"))).classes("text-body2 text-weight-bold")
                            ui.label(str(row.get("portfolio_origin") or "—").replace("_", " ").title()).classes("text-caption text-grey-7")
                        with ui.column().classes("gap-0 min-w-[150px]"):
                            attendance = row.get("attendance_number")
                            ui.label(f"Atend. {attendance}" if attendance else "Sem atendimento vinculado").classes("text-body2")
                            last_date = row.get("last_observed_operational_date")
                            ui.label(
                                f"Última data observada: {_date(last_date)}" if last_date else "Sem data operacional identificada"
                            ).classes("text-caption text-grey-7")
                        ui.badge(label, color=color).props("outline")
                        with ui.row().classes("gap-2"):
                            budget_id = str(row.get("budget_id") or "")
                            number = str(row.get("budget_number") or "")
                            ui.button(
                                "Detalhes", icon="open_in_new",
                                on_click=lambda _=None, bid=budget_id: open_particular_mv_dialog(
                                    access=access, budget_id=bid,
                                ),
                            ).props("outline dense no-caps")
                            ui.button(
                                icon="table_view",
                                on_click=lambda _=None, number=number: open_particular_sheet_budget_dialog(
                                    access=access, budget_number=number,
                                ),
                            ).props("flat round dense").tooltip("Consultar evidências nas grades")

    def refresh() -> None:
        state["search"] = str(search.value or "").strip()
        state["group"] = str(group_select.value or "TODOS")
        state["origin"] = str(origin_select.value or "TODOS")
        render_rows()

    def set_scope(scope: str) -> None:
        state["scope"] = scope
        state["group"] = "TODOS"
        group_select.value = "TODOS"
        render_scopes()
        render_rows()

    async def load() -> None:
        result_label.set_text("Carregando inteligência operacional...")
        try:
            rows = await run.io_bound(list_particular_work_queue)
        except Exception:
            logger.exception("Falha ao carregar particular_work_queue_v1")
            result_label.set_text("Não foi possível carregar a Central de Acompanhamento.")
            ui.notify("Não foi possível carregar a fila inteligente.", type="negative")
            return
        all_rows.clear()
        all_rows.extend(rows)
        group_select.options = {
            "TODOS": "Todas as situações",
            **{key: value[0] for key, value in GROUPS.items() if any(r.get("work_group") == key for r in all_rows)},
        }
        origin_values = sorted({str(r.get("portfolio_origin") or "") for r in all_rows if r.get("portfolio_origin")})
        origin_select.options = {"TODOS": "Todas as origens", **{x: x.replace("_", " ").title() for x in origin_values}}
        render_summary()
        render_scopes()
        render_rows()

    search.on("update:model-value", lambda _: refresh())
    group_select.on("update:model-value", lambda _: refresh())
    origin_select.on("update:model-value", lambda _: refresh())
    ui.timer(0.05, load, once=True)

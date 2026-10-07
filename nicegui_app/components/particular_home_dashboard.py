from __future__ import annotations

from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_monthly_dashboard import render_particular_monthly_dashboard
from nicegui_app.services.particular_monthly_dashboard import (
    format_brl,
    list_home_management,
    list_home_operational_competence,
    month_label,
)
from nicegui_app.services.particular_service import ParticularAccess


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _pct(value: Any) -> str:
    try:
        return f"{Decimal(str(value or 0)):.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def _compact_brl(value: Any) -> str:
    amount = Decimal(str(value or 0))
    absolute = abs(amount)
    if absolute >= Decimal("1000000"):
        return f"R$ {(amount / Decimal('1000000')):.2f} mi".replace(".", ",")
    if absolute >= Decimal("1000"):
        return f"R$ {(amount / Decimal('1000')):.1f} mil".replace(".", ",")
    return format_brl(amount)


def _metric_card(
    title: str,
    value: str,
    subtitle: str,
    icon: str,
    *,
    emphasis: bool = False,
) -> None:
    classes = (
        "flex-1 min-w-[190px] p-4 gap-1 border-0 border-r border-grey-3 shadow-none"
        if emphasis
        else "flex-1 min-w-[190px] p-4 gap-1 border-0 border-r border-grey-3 shadow-none"
    )
    with ui.card().classes(classes):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(title).classes("text-caption text-grey-7 text-weight-medium")
            ui.icon(icon, size="21px").classes("text-primary")
        ui.label(value).classes("text-h5 text-weight-bold")
        ui.label(subtitle).classes("text-caption text-grey-7")


def render_particular_home_dashboard(access: ParticularAccess, competence: str | None = None) -> None:
    """Home executiva do Particular; análises legadas permanecem disponíveis abaixo."""
    management_by_month: dict[str, dict[str, Any]] = {}
    competence_cache: dict[str, list[dict[str, Any]]] = {}

    with ui.row().classes("w-full items-end justify-between gap-3 flex-wrap"):
        with ui.column().classes("gap-0"):
            ui.label("CARTEIRA PARTICULAR").classes("text-caption text-weight-bold text-primary")
            ui.label(
                "Da criação do orçamento à primeira evidência operacional identificada."
            ).classes("text-body2 text-grey-7")
        month_select = ui.select(options={}, label="Competência de criação").props("dense outlined").classes("w-[210px]")
    # A competência agora é controlada pelo contexto global do módulo Particular.
    month_select.set_visibility(False)

    executive = ui.column().classes("w-full gap-4")

    def render_month(month: str, competence_rows: list[dict[str, Any]]) -> None:
        executive.clear()
        row = management_by_month.get(month)
        if not row:
            return

        with executive:
            with ui.card().classes("w-full p-0 gap-0 overflow-hidden shadow-sm"):
                with ui.row().classes("w-full gap-0 flex-wrap"):
                    _metric_card(
                        "Orçamentos",
                        f'{_int(row.get("budgets_total")):,}'.replace(",", "."),
                        f"Carteira criada em {month_label(month)}",
                        "receipt_long",
                    )
                    _metric_card(
                        "Valor ORIGINAL",
                        _compact_brl(row.get("original_value_total")),
                        (
                            f'Procedimentos {_compact_brl(row.get("procedure_value_total"))} · '
                            f'Materiais {_compact_brl(row.get("material_value_total"))}'
                        ),
                        "payments",
                        emphasis=True,
                    )
                    _metric_card(
                        "Com data operacional",
                        f'{_int(row.get("budgets_with_operational_date"))} · '
                        f'{_pct(row.get("pct_budgets_with_operational_date"))}',
                        f'{_compact_brl(row.get("value_with_operational_date"))} do valor ORIGINAL',
                        "event_available",
                    )
                    _metric_card(
                        "Sem data operacional",
                        f'{_int(row.get("budgets_without_operational_date"))} · '
                        f'{_pct(row.get("pct_budgets_without_operational_date"))}',
                        f'{_compact_brl(row.get("value_without_operational_date"))} do valor ORIGINAL',
                        "event_busy",
                    )

            with ui.row().classes("w-full gap-4 items-start flex-wrap"):
                with ui.card().classes("flex-[2] min-w-[520px] p-5 gap-3 shadow-sm"):
                    with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap"):
                        with ui.column().classes("gap-1"):
                            ui.label("Carteira → operação").classes("text-h6 text-weight-bold")
                            ui.label(
                                "Primeira competência operacional observada para a carteira criada no período."
                            ).classes("text-body2 text-grey-7")
                        with ui.column().classes("items-end gap-0"):
                            ui.label(
                                f'{_int(row.get("budgets_with_operational_date"))} com data identificada'
                            ).classes("text-subtitle2 text-weight-bold text-primary")
                            ui.label(
                                f'{_pct(row.get("pct_budgets_with_operational_date"))} da carteira'
                            ).classes("text-caption text-grey-7")

                    if competence_rows:
                        chart_rows = [
                            item for item in competence_rows
                            if item.get("first_operational_competence")
                        ]
                        if chart_rows:
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "grid": {"left": 45, "right": 20, "bottom": 40, "top": 20},
                                "xAxis": {
                                    "type": "category",
                                    "data": [
                                        month_label(str(item["first_operational_competence"]))[:3]
                                        for item in chart_rows
                                    ],
                                },
                                "yAxis": {"type": "value", "name": "Orçamentos"},
                                "series": [{
                                    "type": "bar",
                                    "data": [_int(item.get("budgets")) for item in chart_rows],
                                    "itemStyle": {"color": "#005691", "borderRadius": [5, 5, 0, 0]},
                                }],
                            }).classes("w-full h-56")

                        with ui.row().classes("w-full gap-2 flex-wrap"):
                            for item in competence_rows:
                                competence = item.get("first_operational_competence")
                                label = (
                                    month_label(str(competence))
                                    if competence
                                    else "Sem data"
                                )
                                with ui.card().classes("w-[145px] min-w-[145px] p-3 gap-0 bg-grey-1"):
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(
                                        f'{_int(item.get("budgets"))} · {_pct(item.get("pct_budgets"))}'
                                    ).classes("text-subtitle1 text-weight-bold")
                                    ui.label(
                                        _compact_brl(item.get("original_value"))
                                    ).classes("text-caption")
                    else:
                        ui.label("Não há distribuição operacional para esta competência.").classes(
                            "text-body2 text-grey-7"
                        )

                with ui.card().classes("flex-1 min-w-[300px] p-5 gap-3 shadow-sm"):
                    ui.label("Atenção operacional").classes("text-h6 text-weight-bold")
                    ui.label(
                        "Sinais que merecem acompanhamento sem presumir cancelamento, transferência ou realização."
                    ).classes("text-body2 text-grey-7")

                    attention = (
                        ("Revisão humana", row.get("budgets_review"), "fact_check"),
                        ("Mudança de data identificada", row.get("budgets_date_change"), "event_repeat"),
                        ("Sinal de cancelamento", row.get("budgets_cancellation_signal"), "warning_amber"),
                        ("Múltiplos avisos", row.get("budgets_multiple_notice"), "content_copy"),
                        ("Sinal de transferência", row.get("budgets_transfer_signal"), "swap_horiz"),
                    )
                    for label, value, icon in attention:
                        with ui.row().classes("w-full items-center justify-between gap-3 py-1"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon(icon, size="20px").classes("text-primary")
                                ui.label(label).classes("text-body2")
                            ui.label(str(_int(value))).classes("text-subtitle1 text-weight-bold")

                    ui.separator()
                    ui.label(
                        f'Revisões abertas representam {_compact_brl(row.get("value_review"))} '
                        "da carteira ORIGINAL."
                    ).classes("text-caption text-grey-7")

            with ui.card().classes("w-full p-5 gap-3 shadow-sm"):
                with ui.column().classes("gap-0"):
                    ui.label("Leitura operacional da carteira").classes("text-h6 text-weight-bold")
                    ui.label(
                        "Onde a primeira evidência operacional foi observada e como ela se relaciona com a competência de criação."
                    ).classes("text-body2 text-grey-7")

                with ui.row().classes("w-full gap-5 items-center flex-wrap"):
                    ui.echart({
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                        "legend": {"orient": "vertical", "right": 10, "top": "center"},
                        "series": [{
                            "type": "pie",
                            "radius": ["48%", "72%"],
                            "center": ["35%", "50%"],
                            "avoidLabelOverlap": True,
                            "label": {"show": False},
                            "data": [
                                {"value": _int(row.get("budgets_sede")), "name": "SEDE"},
                                {"value": _int(row.get("budgets_pontal")), "name": "Pontal"},
                                {"value": _int(row.get("budgets_location_unidentified")), "name": "Unidade não identificada"},
                            ],
                        }],
                    }).classes("flex-[2] min-w-[420px] h-52")

                    with ui.column().classes("flex-1 min-w-[280px] gap-2"):
                        for label, value, detail, icon in (
                            ("Mesma competência", row.get("budgets_same_competence"), _compact_brl(row.get("value_same_competence")), "calendar_month"),
                            ("Competência futura", row.get("budgets_future_competence"), _compact_brl(row.get("value_future_competence")), "event_upcoming"),
                        ):
                            with ui.row().classes("w-full items-center justify-between gap-3 p-3 border border-grey-3 rounded-lg"):
                                with ui.row().classes("items-center gap-3"):
                                    ui.icon(icon, size="22px").classes("text-primary")
                                    with ui.column().classes("gap-0"):
                                        ui.label(label).classes("text-body2 text-weight-medium")
                                        ui.label(str(detail)).classes("text-caption text-grey-7")
                                ui.label(str(_int(value))).classes("text-h6 text-weight-bold")

                with ui.row().classes("w-full items-start gap-2"):
                    ui.icon("info", size="16px").classes("text-grey-6 mt-0.5")
                    ui.label(
                        "Evidência operacional indica presença nas fontes persistidas. "
                        "Não equivale, por si só, a realização, faturamento, cancelamento ou conversão."
                    ).classes("text-caption text-grey-7")

    async def load_competence(month: str) -> None:
        executive.clear()
        with executive:
            ui.label("Carregando inteligência operacional...").classes("text-body2 text-grey-7")
        try:
            rows = competence_cache.get(month)
            if rows is None:
                rows = await run.io_bound(list_home_operational_competence, access, month)
                competence_cache[month] = rows
            if month_select.value == month:
                render_month(month, rows)
        except Exception:
            executive.clear()
            with executive:
                ui.label(
                    "Não foi possível carregar a distribuição operacional desta competência."
                ).classes("text-negative")

    async def change_month(value: str | None) -> None:
        if value and value in management_by_month:
            await load_competence(value)

    month_select.on_value_change(lambda event: change_month(event.value))

    async def refresh() -> None:
        refresh_button.disable()
        executive.clear()
        with executive:
            ui.label("Carregando visão gerencial...").classes("text-body2 text-grey-7")
        try:
            rows = await run.io_bound(list_home_management, access)
            management_by_month.clear()
            management_by_month.update({
                str(row["budget_competence"])[:10]: row
                for row in rows
                if row.get("budget_competence")
            })
            competence_cache.clear()
            month_select.options = {
                key: month_label(key)
                for key in management_by_month
            }
            month_select.set_visibility(bool(management_by_month))
            month_select.update()

            if not management_by_month:
                executive.clear()
                with executive:
                    ui.label("Nenhuma competência disponível na base gerencial.")
                return

            current = (
                competence
                if competence in management_by_month
                else month_select.value
                if month_select.value in management_by_month
                else next(iter(management_by_month))
            )
            month_select.value = current
            await load_competence(current)
        except Exception:
            executive.clear()
            with executive:
                ui.label(
                    "Não foi possível carregar a visão gerencial. "
                    "Confira as views e as permissões no Supabase."
                ).classes("text-negative")
        finally:
            refresh_button.enable()

    with ui.row().classes("w-full justify-end"):
        refresh_button = ui.button(
            "Atualizar visão",
            icon="refresh",
            on_click=refresh,
        ).props("flat no-caps")

    with ui.element("section").classes("w-full pt-3"):
        with ui.row().classes("w-full items-end justify-between gap-3 flex-wrap mb-3"):
            with ui.column().classes("gap-0"):
                ui.label("EXPLORAR").classes("text-caption text-weight-bold text-primary")
                ui.label("Análises da carteira").classes("text-h5 text-weight-bold")
                ui.label(
                    "Aprofunde a leitura financeira, médica, por itens e evolução."
                ).classes("text-body2 text-grey-7")
        render_particular_monthly_dashboard(access)

    ui.timer(0.1, refresh, once=True)

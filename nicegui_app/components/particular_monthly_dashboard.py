"""Painel mensal e evolução semanal de validação dos orçamentos do Particular."""
from __future__ import annotations

from decimal import Decimal

from nicegui import ui, run

from nicegui_app.services.particular_monthly_dashboard import (
    list_monthly_validation, list_weekly_validation, format_brl, month_label,
)
from nicegui_app.services.particular_service import ParticularAccess


_WEEK_LABELS = ("1–7", "8–14", "15–21", "22–28", "29–fim")
_WEEK_FIELDS = (
    ("Liberado", "valor_liberado_duplicidade", "#176b50"),
    ("Retido", "valor_aguardando_analise", "#d69e27"),
    ("Excluído", "valor_excluido_duplicidade", "#b44444"),
)


def render_particular_monthly_dashboard(access: ParticularAccess) -> None:
    ui.label("Análise gerencial · Orçamentos").classes("text-h5 text-weight-bold")
    ui.label(
        "Valores de orçamentos importados, classificados pelas decisões de duplicidade. "
        "Não representam faturamento realizado nem comprovam cobertura completa do mês."
    ).classes("text-body2 text-grey-7")

    with ui.row().classes("w-full items-end justify-between gap-3 flex-wrap"):
        months = ui.select(options={}, label="Mês de referência").classes("min-w-[220px]")
    months.set_visibility(False)
    content = ui.column().classes("w-full gap-4")
    rows_by_month: dict[str, dict] = {}
    weekly_cache: dict[str, list[dict]] = {}
    weekly_content = ui.column().classes("w-full gap-3")
    selection_version = 0

    def render_month(value: str | None) -> None:
        content.clear()
        row = rows_by_month.get(value or "")
        if not row:
            return
        with content:
            with ui.row().classes("w-full gap-3 flex-wrap"):
                for label, field, count in (
                    ("Bruto importado", "valor_bruto_importado", "orcamentos_importados"),
                    ("Liberado por duplicidade", "valor_liberado_duplicidade", "orcamentos_liberados"),
                    ("Retido para análise", "valor_aguardando_analise", "orcamentos_aguardando_analise"),
                    ("Excluído por duplicidade", "valor_excluido_duplicidade", "orcamentos_excluidos"),
                ):
                    with ui.card().classes("flex-1 min-w-[210px] p-4 gap-1"):
                        ui.label(label).classes("text-caption text-grey-7")
                        ui.label(format_brl(row.get(field))).classes("text-h5 text-weight-bold")
                        ui.label(f'{int(row.get(count) or 0)} orçamentos').classes("text-caption")
            pending = int(row.get("orcamentos_aguardando_analise") or 0)
            incomplete = int(row.get("orcamentos_decisao_incompleta") or 0)
            if pending or incomplete:
                with ui.card().classes("w-full p-4 gap-2"):
                    ui.label("Atenção: fechamento ainda possui pendências").classes("text-subtitle1 text-weight-bold text-warning")
                    ui.label(
                        f"{pending} orçamento(s) retido(s) em análises pendentes; "
                        f"{incomplete} com decisão de duplicidade incompleta. "
                        "Esses valores não integram o total liberado. "
                        "Consulte a aba Duplicidades para concluir as revisões."
                    )
            if int(row.get("orcamentos_transcricao") or 0):
                ui.label("Transcrições são apresentadas separadamente e não integram o total liberado.").classes("text-body2 text-grey-7")
            if int(row.get("orcamentos_valor_nao_validado") or 0):
                ui.label("Há orçamentos com valores financeiros não validados.").classes("text-warning")
            ui.label(
                "A classificação Particular/Pontal/Negativas e a cobertura da importação ainda "
                "dependem de validação. A data do orçamento não é a data de realização."
            ).classes("text-caption text-grey-7")

    def render_weekly(month: str, rows: list[dict]) -> None:
        weekly_content.clear()
        with weekly_content:
            ui.label("Evolução por faixa de dias do mês").classes("text-h6 text-weight-bold")
            ui.label(
                "Distribuição pela data do orçamento (dias 1–7, 8–14, 15–21, 22–28 e 29–fim). "
                "Não é data de agendamento, realização ou faturamento."
            ).classes("text-body2 text-grey-7")
            if not rows:
                ui.label("Não há dados semanais para este mês.").classes("text-body2 text-grey-7")
                return
            by_week = {int(row["semana_mes"]): row for row in rows}
            monthly = rows_by_month.get(month) or {}
            comparable = (
                ("orcamentos_importados", "orcamentos_importados"),
                ("valor_bruto_importado", "valor_bruto_importado"),
                ("orcamentos_liberados", "orcamentos_liberados"),
                ("valor_liberado_duplicidade", "valor_liberado_duplicidade"),
                ("orcamentos_aguardando_analise", "orcamentos_aguardando_analise"),
                ("valor_aguardando_analise", "valor_aguardando_analise"),
                ("orcamentos_excluidos", "orcamentos_excluidos"),
                ("valor_excluido_duplicidade", "valor_excluido_duplicidade"),
                ("orcamentos_decisao_incompleta", "orcamentos_decisao_incompleta"),
                ("valor_decisao_incompleta", "valor_decisao_incompleta"),
                ("orcamentos_transcricao", "orcamentos_transcricao"),
                ("valor_transcricao", "valor_transcricao"),
                ("orcamentos_valor_nao_validado", "orcamentos_valor_nao_validado"),
            )
            if any(
                sum(Decimal(str(row.get(weekly_field) or 0)) for row in rows)
                != Decimal(str(monthly.get(monthly_field) or 0))
                for weekly_field, monthly_field in comparable
            ):
                ui.label(
                    "Os dados semanais não estão conciliados com o resumo mensal. "
                    "Atualize os indicadores antes de utilizar esta análise."
                ).classes("text-negative text-weight-bold")
                return
            ui.echart({
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 0},
                "grid": {"left": 95, "right": 25, "bottom": 45, "top": 55},
                "xAxis": {"type": "category", "name": "Dias do mês", "data": list(_WEEK_LABELS)},
                "yAxis": {"type": "value", "name": "Valor (R$ milhões)", "axisLabel": {"formatter": "{value}"}},
                "series": [
                    {"name": label, "type": "bar", "itemStyle": {"color": color},
                     "data": [float(Decimal(str(by_week.get(week, {}).get(field) or 0)) / Decimal("1000000")) for week in range(1, 6)]}
                    for label, field, color in _WEEK_FIELDS
                ],
            }).classes("w-full h-80")
            ui.label("Eixo vertical em milhões de reais; valores exatos nos cartões abaixo.").classes("text-caption text-grey-7")
            with ui.row().classes("w-full gap-3 flex-wrap"):
                for week in range(1, 6):
                    record = by_week.get(week)
                    if not record:
                        continue
                    with ui.card().classes("flex-1 min-w-[170px] p-3 gap-1"):
                        ui.label(f"Dias {_WEEK_LABELS[week - 1]}").classes("text-subtitle2 text-weight-bold")
                        ui.label(f'{int(record.get("orcamentos_importados") or 0)} orçamentos').classes("text-caption")
                        for label, field, _ in _WEEK_FIELDS:
                            ui.label(f'{label}: {format_brl(record.get(field))}').classes("text-body2")
            ui.label(
                "O gráfico compara valores de orçamentos importados. Valores de outras classificações "
                "(como transcrições e decisões incompletas) não estão nas três séries exibidas."
            ).classes("text-caption text-grey-7")

    async def load_weekly(month: str) -> None:
        nonlocal selection_version
        selection_version += 1
        request_version = selection_version
        weekly_content.clear()
        with weekly_content:
            ui.label("Carregando evolução semanal...").classes("text-body2 text-grey-7")
        try:
            rows = weekly_cache.get(month)
            if rows is None:
                rows = await run.io_bound(list_weekly_validation, access, month)
                weekly_cache[month] = rows
            if request_version == selection_version and months.value == month:
                render_weekly(month, rows)
        except Exception:
            if request_version == selection_version and months.value == month:
                weekly_content.clear()
                with weekly_content:
                    ui.label("Não foi possível consultar a evolução semanal. Confira a view e as permissões no Supabase.").classes("text-negative")

    async def change_month(value: str | None) -> None:
        render_month(value)
        if value in rows_by_month:
            await load_weekly(value)

    months.on_value_change(lambda event: change_month(event.value))

    async def refresh() -> None:
        nonlocal selection_version
        button.disable()
        selection_version += 1
        content.clear()
        weekly_content.clear()
        with content:
            ui.label("Carregando indicadores mensais...").classes("text-body2 text-grey-7")
        try:
            rows = await run.io_bound(list_monthly_validation, access)
            rows_by_month.clear()
            rows_by_month.update({str(row["mes_referencia"])[:10]: row for row in rows if row.get("mes_referencia")})
            weekly_cache.clear()
            months.options = {key: month_label(key) for key in rows_by_month}
            months.set_visibility(bool(rows_by_month))
            months.update()
            if rows_by_month:
                current = months.value if months.value in rows_by_month else next(iter(rows_by_month))
                months.value = current
                render_month(current)
                await load_weekly(current)
            else:
                content.clear()
                with content:
                    ui.label("Nenhum mês disponível na base importada.")
        except Exception:
            content.clear()
            weekly_content.clear()
            with content:
                ui.label("Não foi possível carregar os indicadores. Verifique a view e as permissões do Supabase.").classes("text-negative")
        finally:
            button.enable()

    button = ui.button("Atualizar indicadores", icon="refresh", on_click=refresh).props("outline no-caps")
    ui.timer(0.1, refresh, once=True)

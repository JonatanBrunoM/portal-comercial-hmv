"""Composição mensal dos itens dos orçamentos liberados."""
from __future__ import annotations

from decimal import Decimal

from nicegui import run, ui

from nicegui_app.services.particular_item_dashboard import list_item_monthly
from nicegui_app.services.particular_monthly_dashboard import format_brl
from nicegui_app.services.particular_service import ParticularAccess


def _decimal(value: object) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def render_item_dashboard(access: ParticularAccess, month_select: ui.select, monthly_rows: dict) -> None:
    """Renderiza composição por código ligada ao seletor mensal principal."""
    with ui.expansion("Composição por itens dos orçamentos", icon="inventory_2").classes("w-full border rounded-lg"):
        ui.label(
            "Detalhamento dos itens dos orçamentos liberados. Os valores representam somente "
            "os itens disponíveis na base e não o valor integral dos orçamentos."
        ).classes("text-body2 text-grey-7")
        status = ui.column().classes("w-full gap-2")
        area = ui.column().classes("w-full gap-3")
        cache: dict[str, list[dict]] = {}
        version = 0

        async def load(month: str | None, force: bool = False) -> None:
            nonlocal version
            version += 1
            request = version
            status.clear()
            area.clear()
            if not month or month not in monthly_rows:
                return
            with status:
                ui.label("Carregando composição por itens...").classes("text-caption text-grey-7")
            try:
                if force or month not in cache:
                    cache[month] = await run.io_bound(list_item_monthly, access, month)
                rows = cache[month]
                if request != version or month_select.value != month:
                    return
                status.clear()
                monthly = monthly_rows[month]
                released = _decimal(monthly.get("valor_liberado_duplicidade"))
                item_value = sum((_decimal(row.get("valor_itens")) for row in rows), Decimal(0))
                item_records = sum(int(row.get("registros_item") or 0) for row in rows)
                coverage = item_value / released * Decimal("100") if released else Decimal(0)
                top_value_rows = rows[:10]
                top_value = sum((_decimal(row.get("valor_itens")) for row in top_value_rows), Decimal(0))
                top_concentration = top_value / item_value * Decimal("100") if item_value else Decimal(0)
                recurring_rows = sorted(rows, key=lambda row: (int(row.get("orcamentos") or 0), _decimal(row.get("valor_itens"))), reverse=True)[:10]

                with area:
                    if not rows:
                        ui.label("Não há itens detalhados para os orçamentos liberados deste mês.").classes("text-body2 text-grey-7")
                        return

                    with ui.row().classes("w-full gap-3 flex-wrap"):
                        for label, value, note in (
                            ("Valor dos itens detalhados", format_brl(item_value), "Não equivale ao total dos orçamentos"),
                            ("Cobertura financeira dos itens", f"{coverage:.2f}%".replace(".", ","), f"Sobre {format_brl(released)} liberados"),
                            ("Registros de itens", f"{item_records:,}".replace(",", "."), "Itens ativos agregados"),
                            ("Concentração Top 10", f"{top_concentration:.2f}%".replace(".", ","), f"{format_brl(top_value)} dos itens detalhados"),
                        ):
                            with ui.card().classes("flex-1 min-w-[210px] p-4 gap-1"):
                                ui.label(label).classes("text-caption text-grey-7")
                                ui.label(value).classes("text-h5 text-weight-bold")
                                ui.label(note).classes("text-caption text-grey-7")

                    top = top_value_rows
                    ui.label("Itens com maior valor acumulado").classes("text-h6 text-weight-bold")
                    ui.echart({
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                        "grid": {"left": 155, "right": 35, "bottom": 30, "top": 20},
                        "xAxis": {"type": "value", "name": "R$ mil", "axisLabel": {"formatter": "{value}"}},
                        "yAxis": {
                            "type": "category",
                            "inverse": True,
                            "data": [str(row.get("codigo") or "SEM_CODIGO") for row in top],
                        },
                        "series": [{
                            "name": "Valor dos itens",
                            "type": "bar",
                            "data": [float(_decimal(row.get("valor_itens")) / Decimal("1000")) for row in top],
                        }],
                    }).classes("w-full h-96")
                    ui.label(
                        "Ranking calculado somente sobre os itens detalhados dos orçamentos liberados; "
                        "o eixo horizontal está em milhares de reais."
                    ).classes("text-caption text-grey-7")

                    ui.label("Itens presentes em mais orçamentos").classes("text-h6 text-weight-bold")
                    ui.echart({
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                        "grid": {"left": 155, "right": 35, "bottom": 30, "top": 20},
                        "xAxis": {"type": "value", "name": "Orçamentos", "minInterval": 1},
                        "yAxis": {"type": "category", "inverse": True, "data": [str(row.get("codigo") or "SEM_CODIGO") for row in recurring_rows]},
                        "series": [{"name": "Orçamentos", "type": "bar", "data": [int(row.get("orcamentos") or 0) for row in recurring_rows]}],
                    }).classes("w-full h-96")
                    ui.label("Recorrência = quantidade de orçamentos liberados em que cada código/descrição aparece; não corresponde à quantidade física do item.").classes("text-caption text-grey-7")

                    columns = [
                        {"name": "codigo", "label": "Código", "field": "codigo", "align": "left", "sortable": True},
                        {"name": "descricao", "label": "Descrição", "field": "descricao", "align": "left", "sortable": True},
                        {"name": "orcamentos", "label": "Orçamentos", "field": "orcamentos", "sortable": True},
                        {"name": "quantidade", "label": "Quantidade", "field": "quantidade", "sortable": True},
                        {"name": "valor", "label": "Valor acumulado", "field": "valor", "sortable": True},
                        {"name": "participacao", "label": "Participação", "field": "participacao", "sortable": True},
                    ]
                    data = [
                        {
                            "row_key": str(row.get("codigo") or "SEM_CODIGO") + "::" + str(row.get("descricao") or "Descrição não informada"),
                            "codigo": str(row.get("codigo") or "SEM_CODIGO"),
                            "descricao": str(row.get("descricao") or "Descrição não informada"),
                            "orcamentos": int(row.get("orcamentos") or 0),
                            "quantidade": f'{_decimal(row.get("quantidade")):,.2f}'.replace(",", "_").replace(".", ",").replace("_", "."),
                            "valor": format_brl(row.get("valor_itens")),
                            "participacao": f'{_decimal(row.get("participacao_itens_percentual")):.2f}%'.replace(".", ","),
                        }
                        for row in rows
                    ]
                    ui.table(columns=columns, rows=data, row_key="row_key", pagination=10).classes("w-full")
                    ui.label(
                        "Cobertura financeira = soma dos itens detalhados ÷ valor dos orçamentos liberados. "
                        "Não interpretar esta composição como faturamento realizado ou receita por procedimento."
                    ).classes("text-caption text-grey-7")
            except Exception:
                if request == version:
                    status.clear()
                    area.clear()
                    with status:
                        ui.label(
                            "Não foi possível carregar a composição por itens. Confira a view e as permissões no Supabase."
                        ).classes("text-negative")

        month_select.on_value_change(lambda event: load(event.value))
        ui.button(
            "Atualizar composição por itens",
            icon="refresh",
            on_click=lambda: load(month_select.value, True),
        ).props("outline no-caps")
        ui.timer(0.3, lambda: load(month_select.value), once=True)

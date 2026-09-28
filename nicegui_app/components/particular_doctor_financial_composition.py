"""Composição financeira mensal por médico dos orçamentos liberados."""
from __future__ import annotations

from decimal import Decimal

from nicegui import run, ui

from nicegui_app.services.particular_doctor_financial_composition import list_doctor_financial_composition
from nicegui_app.services.particular_monthly_dashboard import format_brl
from nicegui_app.services.particular_service import ParticularAccess


def _decimal(value: object) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def render_doctor_financial_composition(access: ParticularAccess, month_select: ui.select, monthly_rows: dict) -> None:
    with ui.expansion("Composição financeira por médico", icon="medical_services").classes("w-full border rounded-lg"):
        ui.label(
            "Composição dos orçamentos liberados por médico, separando procedimentos e materiais. "
            "Os valores são de orçamento e não representam faturamento realizado nem honorários médicos."
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
                ui.label("Carregando composição financeira por médico...").classes("text-caption text-grey-7")
            try:
                if force or month not in cache:
                    cache[month] = await run.io_bound(list_doctor_financial_composition, access, month)
                rows = cache[month]
                if request != version or month_select.value != month:
                    return
                status.clear()
                if not rows:
                    with area:
                        ui.label("Não há composição financeira por médico disponível para este mês.").classes("text-body2 text-grey-7")
                    return

                monthly = monthly_rows[month]
                total = sum((_decimal(row.get("valor_total_liberado")) for row in rows), Decimal("0"))
                procedures = sum((_decimal(row.get("valor_procedimentos")) for row in rows), Decimal("0"))
                materials = sum((_decimal(row.get("valor_materiais")) for row in rows), Decimal("0"))
                budgets = sum(int(row.get("orcamentos_liberados") or 0) for row in rows)
                expected_total = _decimal(monthly.get("valor_liberado_duplicidade"))
                expected_budgets = int(monthly.get("orcamentos_liberados") or 0)
                reconciled = total == expected_total and procedures + materials == total and budgets == expected_budgets

                with area:
                    if not reconciled:
                        ui.label(
                            "A composição financeira por médico não está conciliada com o resumo mensal. "
                            "Atualize os dados antes de utilizar esta análise."
                        ).classes("text-negative text-weight-bold")
                        return

                    ui.label(
                        f"Conciliação: {budgets} orçamentos · {format_brl(total)} liberados · "
                        f"{format_brl(procedures)} em procedimentos · {format_brl(materials)} em materiais."
                    ).classes("text-caption text-grey-7")

                    top = rows[:10]
                    ui.label("Top 10 médicos por valor liberado").classes("text-h6 text-weight-bold")
                    ui.echart({
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                        "legend": {"top": 0},
                        "grid": {"left": 220, "right": 30, "bottom": 35, "top": 55},
                        "xAxis": {"type": "value", "name": "R$ milhões", "axisLabel": {"formatter": "{value}"}},
                        "yAxis": {
                            "type": "category",
                            "inverse": True,
                            "data": [str(row.get("medico") or "Médico não informado") for row in top],
                        },
                        "series": [
                            {
                                "name": "Procedimentos",
                                "type": "bar",
                                "stack": "total",
                                "data": [float(_decimal(row.get("valor_procedimentos")) / Decimal("1000000")) for row in top],
                            },
                            {
                                "name": "Materiais",
                                "type": "bar",
                                "stack": "total",
                                "data": [float(_decimal(row.get("valor_materiais")) / Decimal("1000000")) for row in top],
                            },
                        ],
                    }).classes("w-full h-[440px]")

                    columns = [
                        {"name": "medico", "label": "Médico", "field": "medico", "align": "left", "sortable": True},
                        {"name": "orcamentos", "label": "Orçamentos", "field": "orcamentos", "align": "right", "sortable": True},
                        {"name": "procedimentos", "label": "Procedimentos", "field": "procedimentos", "align": "right", "sortable": True},
                        {"name": "materiais", "label": "Materiais", "field": "materiais", "align": "right", "sortable": True},
                        {"name": "total", "label": "Total liberado", "field": "total", "align": "right", "sortable": True},
                        {"name": "pct_materiais", "label": "% Materiais", "field": "pct_materiais", "align": "right", "sortable": True},
                    ]
                    table_rows = [
                        {
                            "medico": str(row.get("medico") or "Médico não informado"),
                            "orcamentos": int(row.get("orcamentos_liberados") or 0),
                            "procedimentos": format_brl(row.get("valor_procedimentos")),
                            "materiais": format_brl(row.get("valor_materiais")),
                            "total": format_brl(row.get("valor_total_liberado")),
                            "pct_materiais": f'{_decimal(row.get("participacao_materiais_percentual")):.2f}%'.replace(".", ","),
                        }
                        for row in rows
                    ]
                    ui.table(columns=columns, rows=table_rows, row_key="medico", pagination=10).classes("w-full")
                    ui.label(
                        "Ranking baseado no valor dos orçamentos liberados. A composição indica como o valor orçado "
                        "está distribuído entre procedimentos e materiais; não mede produção realizada, receita faturada "
                        "ou remuneração do médico."
                    ).classes("text-caption text-grey-7")
            except Exception:
                if request == version:
                    status.clear()
                    area.clear()
                    with status:
                        ui.label(
                            "Não foi possível carregar a composição financeira por médico. "
                            "Confira a view e as permissões no Supabase."
                        ).classes("text-negative")

        month_select.on_value_change(lambda event: load(event.value))
        ui.button(
            "Atualizar composição por médico",
            icon="refresh",
            on_click=lambda: load(month_select.value, True),
        ).props("outline no-caps")
        ui.timer(0.3, lambda: load(month_select.value), once=True)

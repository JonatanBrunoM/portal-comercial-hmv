"""Composição financeira mensal dos orçamentos liberados."""
from __future__ import annotations

from decimal import Decimal

from nicegui import run, ui

from nicegui_app.services.particular_financial_composition import list_financial_composition
from nicegui_app.services.particular_monthly_dashboard import format_brl
from nicegui_app.services.particular_service import ParticularAccess


def _decimal(value: object) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def render_financial_composition(access: ParticularAccess, month_select: ui.select, monthly_rows: dict) -> None:
    with ui.expansion("Composição financeira", icon="account_balance").classes("w-full border rounded-lg"):
        ui.label(
            "Decomposição dos orçamentos liberados entre procedimentos e materiais. "
            "Os valores são de orçamento e não representam faturamento realizado."
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
                ui.label("Carregando composição financeira...").classes("text-caption text-grey-7")
            try:
                if force or month not in cache:
                    cache[month] = await run.io_bound(list_financial_composition, access, month)
                rows = cache[month]
                if request != version or month_select.value != month:
                    return
                status.clear()
                if not rows:
                    with area:
                        ui.label("Não há composição financeira disponível para este mês.").classes("text-body2 text-grey-7")
                    return

                row = rows[0]
                monthly = monthly_rows[month]
                total = _decimal(row.get("valor_total_liberado"))
                expected = _decimal(monthly.get("valor_liberado_duplicidade"))
                procedures = _decimal(row.get("valor_procedimentos"))
                materials = _decimal(row.get("valor_materiais"))
                reconciled = total == expected and procedures + materials == total

                with area:
                    if not reconciled:
                        ui.label(
                            "A composição financeira não está conciliada com o total mensal liberado. "
                            "Atualize os dados antes de utilizar esta análise."
                        ).classes("text-negative text-weight-bold")
                        return

                    with ui.row().classes("w-full gap-3 flex-wrap"):
                        for label, value, note in (
                            ("Total liberado", format_brl(total), f'{int(row.get("orcamentos_liberados") or 0)} orçamentos'),
                            ("Procedimentos", format_brl(procedures), f'{_decimal(row.get("participacao_procedimentos_percentual")):.2f}% do liberado'.replace(".", ",")),
                            ("Materiais", format_brl(materials), f'{_decimal(row.get("participacao_materiais_percentual")):.2f}% do liberado'.replace(".", ",")),
                            ("Orçamentos com itens", f'{int(row.get("orcamentos_com_itens") or 0)} de {int(row.get("orcamentos_liberados") or 0)}', f'{_decimal(row.get("cobertura_orcamentos_itens_percentual")):.2f}% de cobertura'.replace(".", ",")),
                        ):
                            with ui.card().classes("flex-1 min-w-[210px] p-4 gap-1"):
                                ui.label(label).classes("text-caption text-grey-7")
                                ui.label(value).classes("text-h5 text-weight-bold")
                                ui.label(note).classes("text-caption text-grey-7")

                    ui.label("Distribuição do valor liberado").classes("text-h6 text-weight-bold")
                    ui.echart({
                        "tooltip": {"trigger": "item", "formatter": "{b}: R$ {c} mi ({d}%)"},
                        "legend": {"bottom": 0},
                        "series": [{
                            "name": "Composição financeira",
                            "type": "pie",
                            "radius": ["45%", "72%"],
                            "center": ["50%", "45%"],
                            "label": {"formatter": "{b}\n{d}%"},
                            "data": [
                                {"name": "Procedimentos", "value": float(procedures / Decimal("1000000"))},
                                {"name": "Materiais", "value": float(materials / Decimal("1000000"))},
                            ],
                        }],
                    }).classes("w-full h-80")
                    ui.label(
                        f'Conciliação: procedimentos + materiais = {format_brl(total)}. '
                        f'Os itens detalhados somam {format_brl(row.get("valor_itens_detalhados"))} '
                        f'({_decimal(row.get("cobertura_financeira_itens_percentual")):.2f}% do valor liberado).'.replace(".", ",")
                    ).classes("text-caption text-grey-7")
            except Exception:
                if request == version:
                    status.clear()
                    area.clear()
                    with status:
                        ui.label(
                            "Não foi possível carregar a composição financeira. Confira a view e as permissões no Supabase."
                        ).classes("text-negative")

        month_select.on_value_change(lambda event: load(event.value))
        ui.button(
            "Atualizar composição financeira",
            icon="refresh",
            on_click=lambda: load(month_select.value, True),
        ).props("outline no-caps")
        ui.timer(0.25, lambda: load(month_select.value), once=True)

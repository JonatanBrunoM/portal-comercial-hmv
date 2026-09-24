"""Painel mensal de validação de duplicidades do Particular."""
from __future__ import annotations

from nicegui import ui, run

from nicegui_app.services.particular_monthly_dashboard import (
    list_monthly_validation, format_brl, month_label,
)
from nicegui_app.services.particular_service import ParticularAccess


def render_particular_monthly_dashboard(access: ParticularAccess) -> None:
    ui.label("Análise gerencial · Orçamentos").classes("text-h5 text-weight-bold")
    ui.label(
        "Valores de orçamentos importados, classificados pelas decisões de duplicidade. "
        "Não representam faturamento realizado nem comprovam cobertura completa do mês."
    ).classes("text-body2 text-grey-7")

    content = ui.column().classes("w-full gap-4")
    months = ui.select(options={}, label="Mês de referência").classes("min-w-[220px]")
    months.set_visibility(False)
    rows_by_month = {}

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

    months.on_value_change(lambda event: render_month(event.value))

    async def refresh() -> None:
        button.disable()
        content.clear()
        with content:
            loading = ui.label("Carregando indicadores mensais...").classes("text-body2 text-grey-7")
        try:
            rows = await run.io_bound(list_monthly_validation, access)
            rows_by_month.clear()
            rows_by_month.update({str(row["mes_referencia"])[:10]: row for row in rows if row.get("mes_referencia")})
            months.options = {key: month_label(key) for key in rows_by_month}
            months.set_visibility(bool(rows_by_month))
            months.update()
            if rows_by_month:
                current = months.value if months.value in rows_by_month else next(iter(rows_by_month))
                months.value = current
                render_month(current)
            else:
                content.clear()
                with content:
                    ui.label("Nenhum mês disponível na base importada.")
        except Exception:
            content.clear()
            with content:
                ui.label("Não foi possível carregar os indicadores. Verifique a view e as permissões do Supabase.").classes("text-negative")
        finally:
            button.enable()

    button = ui.button("Atualizar indicadores", icon="refresh", on_click=refresh).props("outline no-caps")
    ui.timer(0.1, refresh, once=True)

from __future__ import annotations

from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_monthly_dashboard import render_particular_monthly_dashboard
from nicegui_app.services.particular_monthly_dashboard import (
    format_brl,
    list_home_management,
    list_monthly_validation,
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
    validation_by_month: dict[str, dict[str, Any]] = {}

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
            with executive:
                with ui.card().classes("w-full p-6 rounded-xl shadow-sm gap-2"):
                    ui.icon("event_busy", size="30px").classes("text-grey-5")
                    ui.label("Ainda não há produção registrada nesta competência.").classes("text-h6")
                    ui.label("Nenhum orçamento de outro mês será exibido como se pertencesse ao período selecionado.").classes("text-body2 text-grey-7")
            return

        validation = validation_by_month.get(month, {})
        total = _int(row.get("budgets_total"))
        with executive:
            with ui.column().classes("w-full gap-1 mb-2"):
                ui.label("RESUMO EXECUTIVO").classes("text-caption text-weight-bold text-primary")
                ui.label("O que aconteceu com a carteira deste mês?").classes("text-h5 text-weight-bold")
                ui.label("Produção original, elegibilidade gerencial e rastreabilidade são leituras distintas.").classes("text-body2 text-grey-7")
            with ui.row().classes("w-full gap-3 flex-wrap"):
                for title, value, detail, icon in (
                    ("Orçamentos criados", str(total), "Total original preservado", "receipt_long"),
                    ("Valor original", _compact_brl(row.get("original_value_total")), "Procedimentos e materiais", "payments"),
                    ("Liberados gerencialmente", str(_int(validation.get("orcamentos_liberados"))) if validation else "—",
                     _compact_brl(validation.get("valor_liberado_duplicidade")) if validation else "Validação não disponível", "verified"),
                    ("Aguardando análise", str(_int(validation.get("orcamentos_aguardando_analise"))) if validation else "—",
                     "Pendências da validação financeira" if validation else "Validação não disponível", "pending_actions"),
                ):
                    with ui.card().classes("flex-1 min-w-[205px] p-5 gap-2 shadow-sm rounded-xl"):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label(title).classes("text-caption text-grey-7")
                            ui.icon(icon, size="22px").classes("text-primary")
                        ui.label(value).classes("text-h5 text-weight-bold")
                        ui.label(detail).classes("text-caption text-grey-7")

            # Painel único: classificação, rastreabilidade e ação são
            # dimensões diferentes da mesma carteira, não somáveis entre si.
            with ui.card().classes("w-full p-5 gap-4 shadow-sm rounded-xl"):
                with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
                    with ui.column().classes("gap-0"):
                        ui.label("Mapa da carteira").classes("text-h6 text-weight-bold")
                        ui.label(
                            "Classificação gerencial, rastreabilidade e alertas — três leituras independentes."
                        ).classes("text-body2 text-grey-7")
                    ui.badge(f"{total} orçamentos originais", color="primary").props("outline")

                with ui.row().classes("w-full gap-5 items-stretch flex-wrap"):
                    with ui.column().classes("flex-[2] min-w-[300px] gap-3"):
                        ui.label("01  COMPOSIÇÃO GERENCIAL").classes(
                            "text-caption text-weight-bold text-primary"
                        )
                        if validation and total:
                            categories = (
                                ("Liberados", _int(validation.get("orcamentos_liberados")), "#087C86"),
                                ("Transcrições", _int(validation.get("orcamentos_transcricao")), "#D79B36"),
                                ("Em análise", _int(validation.get("orcamentos_aguardando_analise")), "#D65D54"),
                                ("Duplicidades", _int(validation.get("orcamentos_excluidos")), "#8792A2"),
                                ("Anulados", _int(validation.get("orcamentos_anulados")), "#64748B"),
                                ("Outros", max(0, total - sum(_int(validation.get(key)) for key in (
                                    "orcamentos_liberados", "orcamentos_transcricao",
                                    "orcamentos_aguardando_analise", "orcamentos_excluidos",
                                    "orcamentos_anulados"))), "#B7C0CB"),
                            )
                            # Uma única faixa representa 100% da carteira.
                            with ui.element("div").classes(
                                "flex w-full h-[22px] overflow-hidden rounded-lg bg-slate-100"
                            ):
                                for label, count, color in categories:
                                    if count:
                                        segment = ui.element("div").style(
                                            f"width: {count / total * 100:.5f}%; background: {color};"
                                        )
                                        segment.tooltip(f"{label}: {count} ({count / total * 100:.1f}%)")
                            with ui.element("div").classes("grid grid-cols-2 gap-x-5 gap-y-2 w-full"):
                                for label, count, color in categories:
                                    if count:
                                        with ui.row().classes("items-center justify-between gap-2"):
                                            with ui.row().classes("items-center gap-2"):
                                                ui.element("span").classes(
                                                    "w-[9px] h-[9px] rounded-full"
                                                ).style(f"background: {color}")
                                                ui.label(label).classes("text-body2")
                                            ui.label(
                                                f"{count} · {count / total * 100:.1f}%".replace(".", ",")
                                            ).classes("text-body2 text-weight-medium")
                        else:
                            ui.label("Classificação indisponível.").classes("text-body2 text-grey-7")
                        ui.label(
                            "Classificação não representa realização ou faturamento."
                        ).classes("text-caption text-grey-7")

                    ui.separator().props("vertical").classes("max-sm:hidden")

                    with ui.column().classes("flex-1 min-w-[245px] gap-3"):
                        ui.label("02  RASTREABILIDADE").classes(
                            "text-caption text-weight-bold text-primary"
                        )
                        with_date = _int(row.get("budgets_with_operational_date"))
                        without_date = _int(row.get("budgets_without_operational_date"))
                        ui.label(f"{with_date} de {total}").classes("text-h5 text-weight-bold")
                        ui.label("com data operacional identificada").classes(
                            "text-body2 text-grey-7"
                        )
                        with ui.element("div").classes(
                            "flex w-full h-[22px] rounded-lg overflow-hidden bg-slate-200"
                        ):
                            if total:
                                ui.element("div").style(
                                    f"width: {with_date / total * 100:.5f}%; background: #087C86;"
                                )
                        with ui.row().classes("w-full justify-between"):
                            ui.label(f"Com data: {with_date}").classes("text-body2")
                            ui.label(f"Sem data: {without_date}").classes("text-body2")
                        ui.label(
                            "Data é evidência de rastreabilidade, não confirmação de realização."
                        ).classes("text-caption text-grey-7")

                ui.separator()
                with ui.row().classes("w-full items-center gap-4 flex-wrap"):
                    ui.label("03  EXIGEM ATENÇÃO").classes(
                        "text-caption text-weight-bold text-primary"
                    )
                    for label, key in (
                        ("Revisão operacional", "budgets_review"),
                        ("Sinais de cancelamento", "budgets_cancellation_signal"),
                        ("Sinais de transferência", "budgets_transfer_signal"),
                    ):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(label).classes("text-body2")
                            ui.badge(str(_int(row.get(key))), color="primary").props("outline")
                    ui.label("Sinais não são decisões confirmadas.").classes(
                        "text-caption text-grey-7"
                    )

            with ui.expansion("Explorar trajetória operacional e distribuição por competência", icon="timeline").classes("w-full bg-white shadow-sm"):
                ui.label("Primeira competência operacional observada para os orçamentos criados neste mês.").classes("text-body2 text-grey-7")
                if competence_rows:
                    with ui.row().classes("w-full gap-3 flex-wrap"):
                        for item in competence_rows:
                            observed = item.get("first_operational_competence")
                            label = month_label(str(observed)) if observed else "Sem data"
                            with ui.card().classes("min-w-[160px] flex-1 p-3 gap-1"):
                                ui.label(label).classes("text-caption text-grey-7")
                                ui.label(str(_int(item.get("budgets")))).classes("text-h6 text-weight-bold")
                                ui.label(_compact_brl(item.get("original_value"))).classes("text-caption")
                else:
                    ui.label("Sem distribuição operacional disponível.").classes("text-body2 text-grey-7")

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
            monthly_rows = await run.io_bound(list_monthly_validation, access)
            validation_by_month.clear()
            validation_by_month.update({str(item["mes_referencia"])[:10]: item for item in monthly_rows if item.get("mes_referencia")})
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
            month_select.set_visibility(False)
            month_select.update()

            if not management_by_month and not competence:
                executive.clear()
                with executive:
                    ui.label("Nenhuma competência disponível na base gerencial.")
                return

            current = competence or (
                month_select.value if month_select.value in management_by_month
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

    with ui.expansion("Análises detalhadas: financeiro, médicos, itens e evolução", icon="analytics", value=False).classes("w-full bg-white shadow-sm"):
        with ui.row().classes("w-full items-end justify-between gap-3 flex-wrap mb-3"):
            with ui.column().classes("gap-0"):
                ui.label("EXPLORAR").classes("text-caption text-weight-bold text-primary")
                ui.label("Análises da carteira").classes("text-h5 text-weight-bold")
                ui.label(
                    "Aprofunde a leitura financeira, médica, por itens e evolução."
                ).classes("text-body2 text-grey-7")
        render_particular_monthly_dashboard(access)

    ui.timer(0.1, refresh, once=True)

from __future__ import annotations

from decimal import Decimal
from typing import Any

from nicegui import run, ui

from nicegui_app.components.particular_monthly_dashboard import render_particular_monthly_dashboard
from nicegui_app.services.particular_doctor_dashboard import list_doctor_monthly
from nicegui_app.services.particular_item_dashboard import list_item_monthly
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
    doctor_cache: dict[str, list[dict[str, Any]]] = {}
    item_cache: dict[str, list[dict[str, Any]]] = {}

    # O seletor técnico continua disponível para sincronizar a competência
    # global, mas não cria um cabeçalho redundante na Home.
    month_select = ui.select(options={}, label="Competência de criação").props("dense outlined").classes("w-[210px]")
    # A competência agora é controlada pelo contexto global do módulo Particular.
    month_select.set_visibility(False)

    executive = ui.column().classes("w-full gap-4")
    ranking = ui.column().classes("w-full gap-3")
    ranking_basis = {"value": "gross"}

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
                    ("Valor total bruto", format_brl(row.get("original_value_total")), "Procedimentos e materiais · valor original", "payments"),
                    ("Com evidência operacional", str(_int(row.get("budgets_with_operational_date"))),
                     "Data identificada · não comprova realização", "event_available"),
                    ("Valor gerencialmente liberado", format_brl(validation.get("valor_liberado_duplicidade")) if validation else "—",
                     f"{_int(validation.get('orcamentos_liberados'))} orçamentos elegíveis" if validation else "Validação não disponível", "verified"),
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


            # Gráficos executivos derivados exclusivamente das views mensais existentes.
            # As dimensões financeira e operacional não devem ser somadas.
            with ui.row().classes("w-full gap-4 items-stretch flex-wrap"):
                with ui.card().classes("flex-1 min-w-[320px] p-5 rounded-xl shadow-sm gap-2"):
                    ui.label("Valor por situação").classes("text-h6 text-weight-bold")
                    ui.label(
                        "Valores gerenciais da carteira · não representam faturamento."
                    ).classes("text-caption text-grey-7")
                    if validation:
                        financial_series = (
                            ("Liberado", "valor_liberado_duplicidade", "#087C86"),
                            ("Em análise", "valor_aguardando_analise", "#D79B36"),
                            ("Transcrições", "valor_transcricao", "#64748B"),
                            ("Duplicidades", "valor_excluido_duplicidade", "#8792A2"),
                            ("Anulados", "valor_anulado", "#D65D54"),
                        )
                        ui.echart({
                            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                            "grid": {"left": 130, "right": 25, "top": 10, "bottom": 30},
                            "xAxis": {"type": "value", "name": "R$ milhões"},
                            "yAxis": {"type": "category", "inverse": True,
                                      "data": [name for name, _, _ in financial_series]},
                            "series": [{
                                "type": "bar",
                                "data": [
                                    {"value": float(Decimal(str(validation.get(field) or 0)) / Decimal("1000000")),
                                     "itemStyle": {"color": color}}
                                    for _, field, color in financial_series
                                ],
                                "barMaxWidth": 22,
                            }],
                        }).classes("w-full h-[290px]")
                        ui.label(
                            "Classificações exclusivas da validação; valores exibidos em milhões."
                        ).classes("text-caption text-grey-7")
                    else:
                        ui.label("Valores financeiros indisponíveis para esta competência.").classes("text-body2 text-grey-7")

                with ui.card().classes("flex-1 min-w-[320px] p-5 rounded-xl shadow-sm gap-2"):
                    ui.label("Rastreabilidade operacional").classes("text-h6 text-weight-bold")
                    ui.label(
                        "Presença de data operacional nos orçamentos originais."
                    ).classes("text-caption text-grey-7")
                    with_date = _int(row.get("budgets_with_operational_date"))
                    without_date = _int(row.get("budgets_without_operational_date"))
                    if with_date + without_date == total and total:
                        ui.echart({
                            "tooltip": {"trigger": "item"},
                            "legend": {"bottom": 0},
                            "series": [{
                                "type": "pie",
                                "radius": ["52%", "73%"],
                                "center": ["50%", "44%"],
                                "label": {"formatter": "{b}: {c}"},
                                "data": [
                                    {"name": "Com data", "value": with_date,
                                     "itemStyle": {"color": "#087C86"}},
                                    {"name": "Sem data", "value": without_date,
                                     "itemStyle": {"color": "#CBD5E1"}},
                                ],
                            }],
                        }).classes("w-full h-[290px]")
                        ui.label(
                            "Data identificada não comprova realização, faturamento ou pagamento."
                        ).classes("text-caption text-grey-7")
                    else:
                        ui.label("Contagem operacional não conciliada com a carteira.").classes("text-body2 text-grey-7")

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

    def render_doctors(month: str) -> None:
        ranking.clear()
        field = "valor_liberado_duplicidade" if ranking_basis["value"] == "released" else "valor_bruto_importado"
        rows = doctor_cache.get(month)
        with ranking:
            with ui.column().classes("w-full gap-3"):
                with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                    ui.label("DESTAQUES DA COMPETÊNCIA").classes(
                        "text-caption text-weight-bold text-primary"
                    )
                    ui.toggle(
                        {"gross": "Bruto original", "released": "Gerencialmente liberado"},
                        value=ranking_basis["value"],
                        on_change=lambda event: change_ranking_basis(event.value),
                    ).props("no-caps dense").classes("text-body2")
                with ui.element("div").classes("grid grid-cols-1 lg:grid-cols-3 gap-4 w-full"):
                    with ui.card().classes("w-full p-4 rounded-xl shadow-sm gap-3"):
                        ui.label("Top 5 médicos").classes("text-h6 text-weight-bold")
                        ui.label("Valores financeiros consolidados").classes("text-caption text-grey-7")
                        if rows is None:
                            ui.label("Ranking indisponível.").classes("text-body2 text-grey-7")
                        else:
                            valid = [
                                item for item in rows
                                if str(item.get("medico") or "").strip()
                                and "CONSULT" not in str(item.get("medico") or "").upper()
                            ]
                            valid.sort(key=lambda item: Decimal(str(item.get(field) or 0)), reverse=True)
                            top = valid[:5]
                            highest = max(
                                (Decimal(str(item.get(field) or 0)) for item in top),
                                default=Decimal(0),
                            )
                            for index, item in enumerate(top, 1):
                                value = Decimal(str(item.get(field) or 0))
                                width = float(value / highest * 100) if highest > 0 else 0
                                with ui.column().classes("w-full gap-1 py-1"):
                                    with ui.row().classes("w-full items-start gap-2 no-wrap"):
                                        ui.label(f"{index:02d}").classes(
                                            "text-primary text-weight-bold text-body2"
                                        )
                                        ui.label(str(item.get("medico"))).classes(
                                            "text-body2 text-weight-medium flex-1"
                                        ).style("overflow-wrap: anywhere;")
                                    ui.label(format_brl(value)).classes(
                                        "text-body2 text-weight-bold"
                                    )
                                    with ui.element("div").classes(
                                        "w-full h-[5px] rounded-full overflow-hidden bg-slate-100"
                                    ):
                                        ui.element("div").classes(
                                            "h-full rounded-full bg-cyan-700"
                                        ).style(f"width: {max(0, min(width, 100)):.2f}%")
                            if not top:
                                ui.label("Nenhum médico identificado.").classes("text-body2 text-grey-7")
                        ui.label("Transcrições CONSULTORIO não atribuídas a médicos.").classes(
                            "text-caption text-grey-7"
                        )
                    for title, subtitle, category in (
                        ("Top 5 procedimentos", "Pacotes cirúrgicos · valores detalhados", "procedures"),
                        ("Top 5 materiais e medicamentos", "Itens de materiais e medicamentos · valores detalhados", "supplies"),
                    ):
                        with ui.card().classes("w-full p-4 rounded-xl shadow-sm gap-3"):
                            ui.label(title).classes("text-h6 text-weight-bold")
                            ui.label(subtitle).classes("text-caption text-grey-7")
                            items = item_cache.get(month)
                            if items is None:
                                ui.label("Itens indisponíveis nesta competência.").classes("text-body2 text-grey-7")
                            else:
                                grouped: dict[str, Decimal] = {}
                                descriptions: dict[str, str] = {}
                                selected_base = (
                                    "RELEASED"
                                    if ranking_basis["value"] == "released"
                                    else "GROSS"
                                )
                                for item in items:
                                    if item.get("base_valor") != selected_base:
                                        continue
                                    code = str(item.get("codigo") or "").strip()
                                    description = str(item.get("descricao") or "").strip()
                                    normalized = description.upper()
                                    prefix = code[:2]
                                    is_complement = "COMPLEMENTO" in normalized or "ROBOTICA" in normalized
                                    is_procedure = (
                                        prefix == "91"
                                        and not is_complement
                                        and ("PCT" in normalized or "PACOTE" in normalized)
                                    )
                                    is_supply = prefix in ("07", "08", "87")
                                    if (category == "procedures" and is_procedure) or (
                                        category == "supplies" and is_supply
                                    ):
                                        grouped[code] = grouped.get(code, Decimal(0)) + Decimal(
                                            str(item.get("valor_itens") or 0)
                                        )
                                        descriptions.setdefault(code, description)
                                top_items = sorted(
                                    grouped.items(), key=lambda pair: pair[1], reverse=True
                                )[:5]
                                highest_item = top_items[0][1] if top_items else Decimal(0)
                                for index, (code, value) in enumerate(top_items, 1):
                                    width = float(value / highest_item * 100) if highest_item > 0 else 0
                                    with ui.column().classes("w-full gap-1 py-1"):
                                        with ui.row().classes("w-full items-start gap-2 no-wrap"):
                                            ui.label(f"{index:02d}").classes(
                                                "text-primary text-weight-bold text-body2"
                                            )
                                            ui.label(descriptions[code]).classes(
                                                "text-body2 text-weight-medium flex-1"
                                            ).style("overflow-wrap: anywhere;")
                                        ui.label(format_brl(value)).classes(
                                            "text-body2 text-weight-bold"
                                        )
                                        with ui.element("div").classes(
                                            "w-full h-[5px] rounded-full overflow-hidden bg-slate-100"
                                        ):
                                            ui.element("div").classes(
                                                "h-full rounded-full bg-cyan-700"
                                            ).style(f"width: {max(0, min(width, 100)):.2f}%")
                                if not top_items:
                                    ui.label("Nenhum item classificado neste grupo.").classes(
                                        "text-body2 text-grey-7"
                                    )
                                ui.label(
                                    "Classificação preliminar por código e descrição. "
                                    "Não equivale ao valor financeiro consolidado."
                                ).classes("text-caption text-grey-7")


    def change_ranking_basis(value: str) -> None:
        ranking_basis["value"] = value
        if month_select.value:
            render_doctors(month_select.value)

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
                try:
                    doctors = doctor_cache.get(month)
                    if doctors is None:
                        doctors = await run.io_bound(list_doctor_monthly, access, month)
                        doctor_cache[month] = doctors
                except Exception:
                    doctor_cache.pop(month, None)
                if month_select.value == month:
                    try:
                        items = item_cache.get(month)
                        if items is None:
                            items = await run.io_bound(list_item_monthly, access, month)
                            item_cache[month] = items
                    except Exception:
                        item_cache.pop(month, None)
                    if month_select.value == month:
                        render_doctors(month)
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
            doctor_cache.clear()
            item_cache.clear()
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

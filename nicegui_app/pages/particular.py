from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.particular_service import (
    ParticularAccessDenied,
    decide_particular_relation,
    get_particular_context,
    get_particular_relation_detail,
    resolve_particular_access,
    rectify_particular_relation,
)

from nicegui_app.components.particular_mv_dialog import (
    open_particular_mv_dialog,
)
from nicegui_app.services.particular_sheets_service import (
    get_particular_sheets_summary,
)
from nicegui_app.components.particular_operational_budgets import (
    render_particular_operational_budgets,
)
from nicegui_app.components.particular_monthly_dashboard import (
    render_particular_monthly_dashboard,
)


def _text(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    normalized = str(value).strip()
    return normalized or fallback


def _date(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    raw = str(value).strip()
    if not raw:
        return "—"
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        return raw


def _money(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    try:
        amount = Decimal(str(value))
    except Exception:
        return _text(value)
    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {formatted}"


def _signal_label(signal: Any) -> str:
    labels = {
        "VERY_HIGH_SIMILARITY": "Similaridade muito alta",
        "SAME_STRUCTURE": "Mesma estrutura",
        "REPEATED_STRUCTURE": "Estrutura repetida",
        "SAME_VALUE": "Mesmo valor",
        "OTHER": "Outros indícios",
    }
    normalized = str(signal or "").strip()
    return labels.get(normalized, normalized or "Não informado")


def _decision_label(decision: Any) -> str:
    labels = {
        "PENDING_REVIEW": "Pendente de revisão",
        "CONFIRMED_DUPLICATE": "Duplicidade confirmada",
        "REBUDGET": "Reorçamento",
        "DISTINCT": "Orçamentos distintos",
    }
    normalized = str(decision or "").strip()
    return labels.get(normalized, normalized or "Não informado")


def _render_access_denied(user: dict) -> None:
    with portal_layout(user=user, active="particular"):
        with ui.column().classes("w-full items-center justify-center py-16 gap-3"):
            ui.icon("lock", size="48px")
            ui.label("Acesso restrito").classes("text-h5 text-weight-bold")
            ui.label(
                "Seu perfil não possui autorização para acessar o módulo Particular."
            ).classes("text-body1 text-center")


def _comparison_field(label: str, value: Any) -> None:
    with ui.column().classes("gap-0"):
        ui.label(label).classes("text-caption")
        ui.label(_text(value)).classes("text-body2 text-weight-medium")


def _comparison_money_field(label: str, value: Any) -> None:
    with ui.column().classes("gap-0"):
        ui.label(label).classes("text-caption")
        ui.label(_money(value)).classes("text-body2 text-weight-medium")


def _render_budget_comparison(title: str, budget: dict[str, Any]) -> None:
    with ui.card().classes("w-full p-5"):
        ui.label(title).classes("text-caption text-weight-bold")
        ui.label(f'Orçamento {_text(budget.get("budget_number"))}').classes(
            "text-h5 text-weight-bold"
        )
        ui.separator()

        with ui.grid(columns=2).classes("w-full gap-4"):
            _comparison_field("Paciente", budget.get("patient_name"))
            _comparison_field("Médico", budget.get("doctor_name"))
            _comparison_field("Data do orçamento", _date(budget.get("budget_date")))
            _comparison_field(
                "Origem",
                budget.get("current_origin") or budget.get("original_requester"),
            )
            _comparison_field("Modalidade", budget.get("modality"))
            _comparison_field("Local", budget.get("location_hint"))

        ui.separator()

        with ui.grid(columns=3).classes("w-full gap-4"):
            _comparison_money_field("Procedimento", budget.get("procedure_value"))
            _comparison_money_field("Material", budget.get("material_value"))
            _comparison_money_field("Total", budget.get("total_value"))

        ui.separator()
        ui.label("Itens do orçamento").classes("text-subtitle1 text-weight-bold")

        items = list(budget.get("items") or [])
        if not items:
            ui.label("Nenhum item registrado.").classes("text-body2")
            return

        for index, item in enumerate(items):
            if index:
                ui.separator()
            with ui.row().classes(
                "w-full items-start justify-between gap-4 py-2 flex-wrap"
            ):
                with ui.column().classes("gap-0"):
                    ui.label(_text(item.get("description"))).classes(
                        "text-body2 text-weight-medium"
                    )
                    ui.label(f'Código: {_text(item.get("item_code"))}').classes(
                        "text-caption"
                    )
                with ui.column().classes("gap-0 items-end"):
                    ui.label(f'Quantidade: {_text(item.get("quantity"))}').classes(
                        "text-body2"
                    )
                    ui.label(_money(item.get("total_value"))).classes("text-caption")


def _open_relation_comparison(access: Any, relation_id: str) -> None:
    try:
        detail = get_particular_relation_detail(
            access=access,
            relation_id=relation_id,
        )
    except Exception:
        ui.notify(
            "Não foi possível carregar a comparação.",
            type="negative",
            position="top",
        )
        return

    relation = dict(detail.get("relation") or {})
    budget_a = dict(detail.get("budget_a") or {})
    budget_b = dict(detail.get("budget_b") or {})
    current_decision = str(relation.get("decision") or "").strip().upper()

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-[1200px] p-0"):
        with ui.row().classes("w-full items-start justify-between gap-4 p-5"):
            with ui.column().classes("gap-1"):
                ui.label("COMPARAÇÃO").classes("text-caption text-weight-bold")
                ui.label(
                    f'Orçamento {_text(budget_a.get("budget_number"))} '
                    f'× {_text(budget_b.get("budget_number"))}'
                ).classes("text-h5 text-weight-bold")
                ui.label(
                    f'{_signal_label(relation.get("detector_signal"))} · '
                    f'{_decision_label(relation.get("decision"))}'
                ).classes("text-body2")
            ui.button(icon="close", on_click=dialog.close).props(
                "flat round dense aria-label='Fechar comparação'"
            )

        ui.separator()

        with ui.element("div").classes("w-full p-5 max-h-[70vh] overflow-auto"):
            with ui.grid().classes("w-full grid-cols-1 lg:grid-cols-2 gap-5"):
                _render_budget_comparison("ORÇAMENTO A", budget_a)
                _render_budget_comparison("ORÇAMENTO B", budget_b)

            if current_decision != "PENDING_REVIEW":
                ui.separator().classes("my-5")
                with ui.column().classes("w-full gap-3"):
                    ui.label("DECISÃO REGISTRADA").classes("text-caption text-weight-bold")
                    ui.label(_decision_label(current_decision)).classes("text-body1 text-weight-bold")
                    ui.label("Justificativa registrada:").classes("text-caption")
                    ui.label(_text(relation.get("review_reason"))).classes("text-body2 whitespace-pre-wrap")
                    ui.label("A comparação está em modo de consulta. A decisão inicial não pode ser alterada.").classes("text-body2")

                    if access.can_write:
                        def open_rectification() -> None:
                            with ui.dialog() as rectify_dialog, ui.card().classes("w-full max-w-[650px] p-5 gap-3"):
                                ui.label("Retificar decisão").classes("text-h6 text-weight-bold")
                                ui.label(
                                    f"Decisão atual: {_decision_label(current_decision)}. "
                                    "A retificação será registrada com a decisão anterior e a nova justificativa."
                                ).classes("text-body2")
                                ui.label("Selecione uma classificação diferente da atual. Não inclua dados do paciente na justificativa.").classes("text-body2")
                                choices = {
                                    key: _decision_label(key)
                                    for key in ("CONFIRMED_DUPLICATE", "REBUDGET", "DISTINCT")
                                    if key != current_decision
                                }
                                new_decision = ui.radio(choices).props("inline")
                                new_reason = ui.textarea(
                                    "Nova justificativa",
                                    placeholder="Explique o motivo da correção, sem dados do paciente.",
                                ).props("outlined autogrow maxlength=1000 counter").classes("w-full")

                                def request_rectification() -> None:
                                    selected = str(new_decision.value or "").strip().upper()
                                    justification = str(new_reason.value or "").strip()
                                    if selected not in choices:
                                        ui.notify("Selecione uma classificação diferente da atual.", type="warning", position="top")
                                        return
                                    if not justification or len(justification) > 1000:
                                        ui.notify("Informe uma justificativa de até 1000 caracteres.", type="warning", position="top")
                                        return

                                    with ui.dialog() as confirm_dialog, ui.card().classes("w-full max-w-[560px] p-5 gap-3"):
                                        ui.label("Confirmar retificação").classes("text-h6 text-weight-bold")
                                        ui.label(
                                            f"De {_decision_label(current_decision)} para {_decision_label(selected)}."
                                        ).classes("text-body1")
                                        ui.label("A alteração será registrada no histórico e na auditoria do Particular.").classes("text-body2")

                                        def confirm_rectification() -> None:
                                            try:
                                                rectify_particular_relation(
                                                    access=access,
                                                    relation_id=relation_id,
                                                    new_decision=selected,
                                                    new_reason=justification,
                                                )
                                            except ParticularAccessDenied:
                                                ui.notify("Seu perfil não possui permissão para retificar esta relação.", type="negative", position="top")
                                                return
                                            except ValueError as exc:
                                                ui.notify(str(exc), type="warning", position="top")
                                                return
                                            except Exception:
                                                ui.notify("Não foi possível retificar a decisão. Atualize a página e confira o estado atual da relação.", type="negative", position="top")
                                                return

                                            confirm_dialog.close()
                                            rectify_dialog.close()
                                            dialog.close()
                                            ui.notify("Retificação registrada com sucesso.", type="positive", position="top")
                                            ui.navigate.to("/particular")

                                        with ui.row().classes("w-full justify-end items-center gap-3 mt-3"):
                                            ui.button("Cancelar", on_click=confirm_dialog.close).props("flat no-caps")
                                            ui.button("Confirmar retificação", icon="check", on_click=confirm_rectification).props("unelevated no-caps")
                                    confirm_dialog.open()

                                with ui.row().classes("w-full justify-end items-center gap-3 mt-3"):
                                    ui.button("Cancelar", on_click=rectify_dialog.close).props("flat no-caps")
                                    ui.button("Continuar", icon="edit", on_click=request_rectification).props("unelevated no-caps")
                            rectify_dialog.open()

                        ui.button("Retificar decisão", icon="edit", on_click=open_rectification).props("outline no-caps")

            if access.can_write and current_decision == "PENDING_REVIEW":
                ui.separator().classes("my-5")
                with ui.column().classes("w-full gap-3"):
                    ui.label("DECISÃO DO GESTOR").classes(
                        "text-caption text-weight-bold"
                    )
                    ui.label(
                        "Selecione a classificação e informe uma justificativa. "
                        "Não inclua dados do paciente na justificativa."
                    ).classes("text-body2")

                    decision = ui.radio(
                        {
                            "CONFIRMED_DUPLICATE": "Duplicidade confirmada",
                            "REBUDGET": "Reorçamento",
                            "DISTINCT": "Orçamentos distintos",
                        }
                    ).props("inline")

                    reason = ui.textarea(
                        "Justificativa",
                        placeholder="Descreva o motivo sem incluir dados do paciente.",
                    ).props("outlined autogrow maxlength=1000 counter").classes("w-full")

                    def request_confirmation() -> None:
                        selected = str(decision.value or "").strip().upper()
                        justification = str(reason.value or "").strip()

                        if selected not in {
                            "CONFIRMED_DUPLICATE",
                            "REBUDGET",
                            "DISTINCT",
                        }:
                            ui.notify("Selecione uma decisão.", type="warning", position="top")
                            return
                        if not justification:
                            ui.notify(
                                "Informe a justificativa da decisão.",
                                type="warning",
                                position="top",
                            )
                            return

                        with ui.dialog() as confirm_dialog, ui.card().classes(
                            "w-full max-w-[560px] p-5"
                        ):
                            ui.label("Confirmar decisão").classes("text-h6 text-weight-bold")
                            ui.label(
                                f'Você está prestes a registrar: '
                                f'{_decision_label(selected)}.'
                            ).classes("text-body1")
                            ui.label(
                                "A ação será vinculada ao seu perfil e registrada "
                                "na auditoria do módulo Particular."
                            ).classes("text-body2")

                            def confirm_decision() -> None:
                                try:
                                    decide_particular_relation(
                                        access=access,
                                        relation_id=relation_id,
                                        decision=selected,
                                        review_reason=justification,
                                    )
                                except ParticularAccessDenied:
                                    ui.notify(
                                        "Seu perfil não possui permissão para registrar esta decisão.",
                                        type="negative",
                                        position="top",
                                    )
                                    return
                                except ValueError as exc:
                                    ui.notify(str(exc), type="warning", position="top")
                                    return
                                except Exception:
                                    ui.notify(
                                        "Não foi possível registrar a decisão.",
                                        type="negative",
                                        position="top",
                                    )
                                    return

                                confirm_dialog.close()
                                dialog.close()
                                ui.notify(
                                    "Decisão registrada com sucesso.",
                                    type="positive",
                                    position="top",
                                )
                                ui.navigate.to("/particular")

                            with ui.row().classes(
                                "w-full justify-end items-center gap-3 mt-3"
                            ):
                                ui.button(
                                    "Cancelar",
                                    on_click=confirm_dialog.close,
                                ).props("flat no-caps")
                                ui.button(
                                    "Confirmar decisão",
                                    icon="check",
                                    on_click=confirm_decision,
                                ).props("unelevated no-caps")

                        confirm_dialog.open()

                    ui.button(
                        "Registrar decisão",
                        icon="gavel",
                        on_click=request_confirmation,
                    ).props("unelevated no-caps")

        ui.separator()

        with ui.row().classes("w-full justify-end items-center gap-3 p-4"):
            ui.button("Fechar", on_click=dialog.close).props("outline no-caps")

    dialog.open()


def render_particular(user: dict) -> None:
    try:
        access = resolve_particular_access(user)
        context = get_particular_context(access=access)
    except ParticularAccessDenied:
        _render_access_denied(user)
        return

    rows = list(context.relation_reviews)
    pending_count = sum(
        str(row.get("decision") or "").strip().upper() == "PENDING_REVIEW"
        for row in rows
    )
    reviewed_count = len(rows) - pending_count

    with portal_layout(user=user, active="particular"):
        with ui.column().classes("w-full gap-5"):
            with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("GESTÃO COMERCIAL  /  PARTICULAR").classes(
                        "text-caption text-weight-bold text-primary"
                    )
                    ui.label("Particular").classes("text-h4 text-weight-bold")
                    ui.label(
                        "Análise financeira dos orçamentos, com conferências e apontamentos de apoio."
                    ).classes("text-body1 text-grey-7")
                ui.badge(
                    "Gestor" if access.module_role == "MANAGER" else "Operador",
                    color="primary",
                ).props("outline")

            with ui.tabs().classes("w-full") as tabs:
                overview_tab = ui.tab("Visão geral", icon="dashboard")
                operation_tab = ui.tab("Orçamentos", icon="receipt_long")
                review_tab = ui.tab("Duplicidades", icon="compare_arrows")

            with ui.tab_panels(tabs, value=overview_tab).classes("w-full"):
                with ui.tab_panel(overview_tab):
                    with ui.column().classes("w-full gap-5"):
                        render_particular_monthly_dashboard(access)
                        ui.label("Conferências e apontamentos").classes(
                            "text-h6 text-weight-bold mt-2"
                        )
                        ui.label(
                            "Consultas complementares para validar a base e acompanhar "
                            "pendências. Não representam receita realizada."
                        ).classes("text-body2 text-grey-7")

                        with ui.expansion(
                            "Indicadores das grades · Google Sheets",
                            icon="table_chart",
                            value=False,
                        ).classes("w-full border rounded-lg"):
                            with ui.card().classes("w-full p-5 gap-4"):
                                ui.label("Indicadores das grades").classes(
                                    "text-h6 text-weight-bold"
                                )
                                ui.label(
                                    "Dados da cópia de testes do Google Sheets. "
                                    "Os totais representam números de orçamento distintos "
                                    "nas grades, não procedimentos realizados no MV."
                                ).classes("text-body2 text-grey-7")

                                sheets_result = ui.column().classes("w-full gap-3")

                                async def load_sheets_summary():
                                    from nicegui import run

                                    load_button.disable()
                                    sheets_result.clear()

                                    with sheets_result:
                                        ui.label("Consultando as três grades...").classes(
                                            "text-body2 text-grey-7"
                                        )

                                    try:
                                        summary = await run.io_bound(
                                            get_particular_sheets_summary,
                                            access,
                                        )
                                    except Exception:
                                        sheets_result.clear()
                                        with sheets_result:
                                            ui.label(
                                                "Não foi possível carregar os indicadores "
                                                "das grades. Tente novamente mais tarde."
                                            ).classes("text-negative")
                                        return
                                    finally:
                                        load_button.enable()

                                    sheets_result.clear()

                                    with sheets_result:
                                        with ui.row().classes("w-full gap-4 flex-wrap"):
                                            with ui.card().classes(
                                                "flex-1 min-w-[180px] p-4 gap-2"
                                            ):
                                                ui.label("Orçamentos distintos nas três grades")
                                                ui.label(
                                                    f'{summary["orcamentos_distintos_total"]:,}'
                                                    .replace(",", ".")
                                                ).classes("text-h4 text-weight-bold")

                                            with ui.card().classes(
                                                "flex-1 min-w-[180px] p-4 gap-2"
                                            ):
                                                ui.label("Presentes em mais de uma grade")
                                                ui.label(
                                                    f'{summary["orcamentos_em_mais_de_uma_aba"]:,}'
                                                    .replace(",", ".")
                                                ).classes("text-h4 text-weight-bold")

                                        with ui.row().classes("w-full gap-4 flex-wrap"):
                                            for name, stats in summary["abas"].items():
                                                with ui.card().classes(
                                                    "flex-1 min-w-[180px] p-4 gap-2"
                                                ):
                                                    ui.label(name).classes(
                                                        "text-subtitle2 text-weight-bold"
                                                    )
                                                    ui.label(
                                                        f'{stats["orcamentos_distintos"]:,}'
                                                        .replace(",", ".")
                                                    ).classes("text-h5 text-weight-bold")
                                                    ui.label(
                                                        "Orçamentos distintos nesta grade"
                                                    ).classes("text-caption text-grey-7")

                                        ui.label(
                                            "Um mesmo orçamento pode constar em várias grades. "
                                            "A presença de aviso ou contato não comprova "
                                            "a realização do procedimento."
                                        ).classes("text-caption text-grey-7")

                                load_button = ui.button(
                                    "Atualizar indicadores das grades",
                                    icon="refresh",
                                    on_click=load_sheets_summary,
                                ).props("outline no-caps")

                        with ui.expansion(
                            f"Revisão de duplicidades · {pending_count} pendente(s)",
                            icon="fact_check",
                            value=False,
                        ).classes("w-full border rounded-lg"):
                            with ui.row().classes("w-full gap-4 flex-wrap"):
                                for label, value, icon in (
                                    ("Relações identificadas", len(rows), "account_tree"),
                                    ("Aguardando revisão", pending_count, "pending_actions"),
                                    ("Relações revisadas", reviewed_count, "task_alt"),
                                ):
                                    with ui.card().classes("flex-1 min-w-[180px] p-5 gap-2"):
                                        ui.icon(icon, size="28px").classes("text-primary")
                                        ui.label(label).classes("text-caption text-grey-7")
                                        ui.label(str(value)).classes("text-h4 text-weight-bold")
                            with ui.row().classes("w-full gap-4 flex-wrap"):
                                with ui.card().classes("flex-1 min-w-[250px] p-5 gap-3"):
                                    ui.icon("receipt_long", size="30px").classes("text-primary")
                                    ui.label("Operação de orçamentos").classes("text-h6 text-weight-bold")
                                    ui.label(
                                        "Busque pelo número do orçamento e consulte os detalhes "
                                        "e o histórico de conferências no MV."
                                    ).classes("text-body2 text-grey-7")
                                    ui.button(
                                        "Consultar orçamentos",
                                        icon="arrow_forward",
                                        on_click=lambda: tabs.set_value(operation_tab),
                                    ).props("unelevated no-caps")
                                with ui.card().classes("flex-1 min-w-[250px] p-5 gap-3"):
                                    ui.icon("compare_arrows", size="30px").classes("text-primary")
                                    ui.label("Revisão de duplicidades").classes("text-h6 text-weight-bold")
                                    ui.label(
                                        "Analise as relações detectadas, registre decisões "
                                        "e consulte o histórico das revisões."
                                    ).classes("text-body2 text-grey-7")
                                    ui.button(
                                        "Abrir revisão",
                                        icon="arrow_forward",
                                        on_click=lambda: tabs.set_value(review_tab),
                                    ).props("outline no-caps")

                with ui.tab_panel(operation_tab):
                    render_particular_operational_budgets(access=access)

                with ui.tab_panel(review_tab):
                    with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
                        with ui.column().classes("gap-1"):
                            ui.label("PARTICULAR").classes("text-caption text-weight-bold")
                            ui.label("Revisão de possíveis duplicidades").classes(
                                "text-h4 text-weight-bold"
                            )
                            ui.label(
                                "Compare os orçamentos identificados pelo detector "
                                "antes de qualquer decisão manual."
                            ).classes("text-body1")

                        with ui.column().classes("items-end gap-1"):
                            ui.label(
                                "Gestor" if access.module_role == "MANAGER" else "Operador"
                            ).classes("text-weight-bold")
                            ui.label(f"{len(rows)} relações para análise").classes(
                                "text-caption"
                            )

                    if not rows:
                        with ui.card().classes("w-full p-6"):
                            ui.label("Nenhuma relação encontrada.").classes("text-h6")
                            ui.label(
                                "Não existem possíveis duplicidades aguardando análise."
                            )
                        return

                    with ui.card().classes("w-full"):
                        with ui.column().classes("w-full gap-0"):
                            for index, row in enumerate(rows):
                                if index:
                                    ui.separator()

                                with ui.row().classes(
                                    "w-full items-center justify-between gap-4 p-4 flex-wrap"
                                ):
                                    with ui.column().classes("gap-1"):
                                        ui.label(
                                            f'Orçamento {row["budget_a_number"]} '
                                            f'× {row["budget_b_number"]}'
                                        ).classes("text-subtitle1 text-weight-bold")
                                        ui.label(
                                            f'{_date(row.get("budget_a_date"))} '
                                            f'× {_date(row.get("budget_b_date"))}'
                                        ).classes("text-caption")

                                    with ui.column().classes("gap-1"):
                                        ui.label(
                                            _signal_label(row.get("detector_signal"))
                                        ).classes("text-body2 text-weight-medium")
                                        ui.label(
                                            _decision_label(row.get("decision"))
                                        ).classes("text-caption")

                                    with ui.column().classes("gap-1"):
                                        ui.label(
                                            f'Diferença total: '
                                            f'{_money(row.get("total_difference"))}'
                                        ).classes("text-body2")

                                        days = row.get("days_apart")
                                        ui.label(
                                            "Mesmo dia"
                                            if days == 0
                                            else (
                                                f"{days} dia de diferença"
                                                if days == 1
                                                else f"{days} dias de diferença"
                                            )
                                        ).classes("text-caption")

                                    relation_id = str(row.get("relation_id") or "").strip()

                                    ui.button(
                                        "Comparar",
                                        icon="compare_arrows",
                                        on_click=lambda relation_id=relation_id: (
                                            _open_relation_comparison(access, relation_id)
                                        ),
                                    ).props("outline no-caps")

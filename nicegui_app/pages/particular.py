from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.hero_art import render_hero_art
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
from nicegui_app.components.particular_work_queue import (
    render_particular_work_queue,
)
from nicegui_app.components.particular_home_dashboard import (
    render_particular_home_dashboard,
)
from nicegui_app.components.particular_import import render_particular_import
from nicegui_app.services.particular_competence import (
    get_particular_closing_breakdown,
    get_particular_closing_snapshot,
    get_particular_competence_sources,
    resolve_active_competence,
    set_active_competence,
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
                                    if key != current_decision or key == "CONFIRMED_DUPLICATE"
                                }
                                new_decision = ui.radio(choices).props("inline")
                                retained_options = {
                                    str(budget_a.get("id")): f'Manter orçamento {_text(budget_a.get("budget_number"))}',
                                    str(budget_b.get("id")): f'Manter orçamento {_text(budget_b.get("budget_number"))}',
                                }
                                retained_budget = ui.radio(retained_options).props("inline")
                                ui.label("Ao confirmar duplicidade, selecione obrigatoriamente qual orçamento deve ser mantido.").classes("text-caption")
                                new_reason = ui.textarea(
                                    "Nova justificativa",
                                    placeholder="Explique o motivo da correção, sem dados do paciente.",
                                ).props("outlined autogrow maxlength=1000 counter").classes("w-full")

                                def request_rectification() -> None:
                                    selected = str(new_decision.value or "").strip().upper()
                                    justification = str(new_reason.value or "").strip()
                                    retained_id = str(retained_budget.value or "").strip() or None
                                    if selected not in choices:
                                        ui.notify("Selecione uma classificação diferente da atual.", type="warning", position="top")
                                        return
                                    if selected == "CONFIRMED_DUPLICATE" and retained_id not in retained_options:
                                        ui.notify("Selecione qual orçamento deve ser mantido.", type="warning", position="top")
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
                                                    retained_budget_id=retained_id if selected == "CONFIRMED_DUPLICATE" else None,
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

                    retained_options = {
                        str(budget_a.get("id")): f'Manter orçamento {_text(budget_a.get("budget_number"))}',
                        str(budget_b.get("id")): f'Manter orçamento {_text(budget_b.get("budget_number"))}',
                    }
                    retained_budget = ui.radio(retained_options).props("inline")
                    ui.label("Ao confirmar duplicidade, selecione obrigatoriamente qual orçamento deve ser mantido.").classes("text-caption")

                    reason = ui.textarea(
                        "Justificativa",
                        placeholder="Descreva o motivo sem incluir dados do paciente.",
                    ).props("outlined autogrow maxlength=1000 counter").classes("w-full")

                    def request_confirmation() -> None:
                        selected = str(decision.value or "").strip().upper()
                        justification = str(reason.value or "").strip()
                        retained_id = str(retained_budget.value or "").strip() or None

                        if selected not in {
                            "CONFIRMED_DUPLICATE",
                            "REBUDGET",
                            "DISTINCT",
                        }:
                            ui.notify("Selecione uma decisão.", type="warning", position="top")
                            return
                        if selected == "CONFIRMED_DUPLICATE" and retained_id not in retained_options:
                            ui.notify("Selecione qual orçamento deve ser mantido.", type="warning", position="top")
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
                                        retained_budget_id=retained_id if selected == "CONFIRMED_DUPLICATE" else None,
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
        active_competence, competences = resolve_active_competence(access)
        competence_sources = get_particular_competence_sources(access, active_competence)
        closing_snapshot = get_particular_closing_snapshot(access, active_competence)
        closing_breakdown = get_particular_closing_breakdown(access, active_competence)
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
        with ui.column().classes("w-full gap-3"):
            def change_active_competence(reference_date: str) -> None:
                try:
                    set_active_competence(reference_date, competences)
                except ValueError as exc:
                    ui.notify(str(exc), type="warning", position="top")
                    return
                ui.navigate.to("/particular")

            # Calendário operacional: sempre mostra dois meses anteriores,
            # a competência ativa e dois meses seguintes, mesmo que ainda não exista
            # registro em particular_competencies.
            competence_by_reference = {item.reference_date: item for item in competences}

            def shift_month(reference: str, offset: int) -> str:
                base = date.fromisoformat(reference[:10])
                absolute = base.year * 12 + (base.month - 1) + offset
                year, month_zero = divmod(absolute, 12)
                return date(year, month_zero + 1, 1).isoformat()

            calendar_references = [
                shift_month(active_competence.reference_date, offset)
                for offset in (-2, -1, 0, 1, 2)
            ]
            month_names = (
                "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
                "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
            )

            with ui.element("section").classes("portal-particular-hero"):
                with ui.column().classes("portal-particular-hero-copy pt-[56px]"):
                    ui.label("GESTÃO PARTICULAR").classes("portal-particular-hero-kicker")
                    ui.label("Da proposta à jornada operacional.").classes(
                        "portal-particular-hero-title"
                    )
                    ui.label(
                        "Acompanhe a carteira, evidências operacionais, movimentações e pontos que exigem revisão."
                    ).classes("portal-particular-hero-description")

                with ui.element("div").classes("portal-particular-hero-side mt-[56px]"):
                    for icon, title, subtitle in (
                        ("account_balance_wallet", "Carteira", "visão consolidada"),
                        ("timeline", "Operação", "evidências rastreáveis"),
                        (
                            "fact_check",
                            "Revisões",
                            f"{pending_count} pendente(s)" if pending_count else "sem pendências",
                        ),
                    ):
                        with ui.element("div").classes("portal-particular-hero-point"):
                            with ui.element("div").classes("portal-particular-hero-point-icon"):
                                ui.icon(icon)
                            with ui.column().classes("portal-particular-hero-point-copy"):
                                ui.label(title).classes("portal-particular-hero-point-title")
                                ui.label(subtitle).classes("portal-particular-hero-point-subtitle")

                render_hero_art(variant="particular", icon="insights")

                # Faixa mensal encaixada na largura reservada ao conteúdo principal
                # do hero, sem alterar o grid original de título, cards e abas.
                with ui.element("div").classes(
                    "absolute left-0 right-0 top-0 h-[58px] z-20 overflow-hidden "
                    "rounded-t-[20px] bg-[#0B6FA4] border-b border-white/20 shadow-sm"
                ):
                    with ui.row().classes("w-full h-full items-stretch gap-0 no-wrap"):
                        for reference in calendar_references:
                            month = date.fromisoformat(reference)
                            item = competence_by_reference.get(reference)
                            is_active = reference == active_competence.reference_date
                            label = f"{month_names[month.month - 1]}/{month.year}"

                            def select_calendar_month(
                                selected_reference: str = reference,
                                selected_item=item,
                                selected_label: str = label,
                            ) -> None:
                                if selected_item is None:
                                    ui.notify(
                                        f"{selected_label.title()} ainda não possui competência cadastrada.",
                                        type="info",
                                        position="top",
                                    )
                                    return
                                change_active_competence(selected_reference)

                            status = item.status if item is not None else ""
                            status_icon = {
                                "CLOSED": "check_circle",
                                "IN_CLOSING": "pending",
                                "OPEN": "radio_button_unchecked",
                            }.get(status)

                            button = ui.button(
                                on_click=select_calendar_month,
                            ).props("flat no-caps").classes(
                                "flex-1 min-w-0 h-full rounded-none border-r border-slate-200 "
                                "transition-all duration-150 "
                                + (
                                    "bg-white/22 text-white text-weight-bold "
                                    "border-b-[4px] border-b-white shadow-lg ring-1 ring-inset ring-white/25"
                                    if is_active
                                    else "bg-[#0B6FA4] text-white hover:bg-white/10"
                                )
                            )
                            with button:
                                with ui.row().classes("items-center justify-center gap-2 no-wrap"):
                                    if status_icon:
                                        ui.icon(status_icon, size="14px").classes(
                                            "text-white" if is_active else "text-white/80"
                                        )
                                    ui.label(label).classes(
                                        "text-[13px] tracking-wide text-white "
                                        + ("text-weight-bold" if is_active else "text-weight-medium")
                                    )
                            if item is not None:
                                button.tooltip(f"{item.label} · {item.status_label}")
                            else:
                                button.tooltip("Competência ainda não cadastrada")

                with ui.element("nav").classes("portal-particular-workspace-nav"):
                    with ui.tabs().props(
                        "dense no-caps indicator-color=transparent active-color=primary"
                    ).classes("portal-particular-tabs") as tabs:
                        overview_tab = ui.tab("Visão geral", icon="space_dashboard")
                        operation_tab = ui.tab("Carteira", icon="receipt_long")
                        review_tab = ui.tab(
                            f"Revisões ({pending_count})" if pending_count else "Revisões",
                            icon="fact_check",
                        )
                        import_tab = ui.tab("Dados", icon="database")

            with ui.tab_panels(tabs, value=overview_tab).classes("w-full bg-transparent p-0"):
                with ui.tab_panel(overview_tab).classes("px-0 py-2"):
                    with ui.column().classes("w-full gap-5"):
                        render_particular_home_dashboard(access, competence=active_competence.reference_date)
                        with ui.element("section").classes("w-full pt-1"):
                            ui.label("FECHAMENTO DA COMPETÊNCIA").classes("text-caption text-weight-bold text-primary")
                            ui.label("Maturidade de " + active_competence.label).classes("text-h5 text-weight-bold")
                            ui.label("Leitura diagnóstica da coorte. Ainda não altera a classificação dos casos.").classes("text-body2 text-grey-7")

                            with ui.row().classes("w-full gap-3 flex-wrap mt-3"):
                                closing_cards = [
                                    ("check_circle", "Resolvidos na operação", closing_snapshot.operational_resolved),
                                    ("event", "Maturação futura", closing_snapshot.future_maturation),
                                    ("priority_high", "Exigem ação humana", closing_snapshot.human_action),
                                    ("paid", "Contas fechadas", closing_snapshot.financially_closed),
                                ]
                                for icon, label, value in closing_cards:
                                    with ui.card().classes("flex-1 min-w-[190px] p-4 gap-1 shadow-sm"):
                                        with ui.row().classes("items-center gap-2"):
                                            ui.icon(icon, size="20px").classes("text-primary")
                                            ui.label(label).classes("text-caption text-grey-7")
                                        ui.label(str(value)).classes("text-h5 text-weight-bold")

                            with ui.card().classes("w-full p-5 gap-3 shadow-sm"):
                                with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
                                    with ui.column().classes("gap-0"):
                                        ui.label("Maturidade financeira").classes("text-subtitle1 text-weight-bold")
                                        ui.label("Somente contas com valor final conhecido entram no comparativo.").classes("text-caption text-grey-7")
                                    ui.badge(
                                        str(closing_snapshot.financially_closed_with_value) + " comparáveis",
                                        color="primary",
                                    )
                                with ui.row().classes("w-full gap-8 flex-wrap"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(str(closing_snapshot.financially_open)).classes("text-h6 text-weight-bold")
                                        ui.label("contas abertas").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(str(closing_snapshot.financially_unknown)).classes("text-h6 text-weight-bold")
                                        ui.label("situação financeira desconhecida").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(_money(closing_snapshot.comparable_original_value)).classes("text-h6 text-weight-bold")
                                        ui.label("orçado comparável").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(_money(closing_snapshot.realized_value_total)).classes("text-h6 text-weight-bold")
                                        ui.label("realizado conhecido").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(_money(closing_snapshot.comparable_difference)).classes("text-h6 text-weight-bold")
                                        ui.label("diferença").classes("text-caption text-grey-7")


                            with ui.expansion("Diagnóstico técnico do fechamento", icon="analytics").classes("w-full bg-white shadow-sm"):
                                ui.label(
                                    "Decomposição temporária para validar as regras de Agosto antes de consolidar o fechamento."
                                ).classes("text-caption text-grey-7 mb-3")
                                with ui.row().classes("w-full gap-6 flex-wrap"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(str(closing_breakdown.closed_with_value)).classes("text-h6 text-weight-bold")
                                        ui.label("fechadas com valor final").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(str(closing_breakdown.closed_without_value)).classes("text-h6 text-weight-bold")
                                        ui.label("fechadas sem valor final").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(str(closing_breakdown.future_without_financial_state)).classes("text-h6 text-weight-bold")
                                        ui.label("futuras sem estado financeiro").classes("text-caption text-grey-7")
                                    with ui.column().classes("gap-0"):
                                        ui.label(str(closing_breakdown.human_action_without_financial_state)).classes("text-h6 text-weight-bold")
                                        ui.label("ação humana sem estado financeiro").classes("text-caption text-grey-7")

                                ui.separator()
                                ui.label("Distribuição por grupo de trabalho").classes("text-subtitle2 text-weight-bold")
                                with ui.column().classes("w-full gap-1"):
                                    for item in closing_breakdown.work_groups:
                                        with ui.row().classes("w-full items-center justify-between gap-3 py-1"):
                                            ui.label(
                                                str(item["stage"]) + " · " + str(item["work_group"]) + " · " + str(item["work_action"])
                                            ).classes("text-body2")
                                            ui.badge(str(item["count"])).props("outline")

                                ui.separator()
                                ui.label("Financeiro × estágio operacional").classes("text-subtitle2 text-weight-bold")
                                with ui.column().classes("w-full gap-1"):
                                    for item in closing_breakdown.financial_by_operational_stage:
                                        with ui.row().classes("w-full items-center justify-between gap-3 py-1"):
                                            ui.label(
                                                str(item["stage"]) + " · " + str(item["financial_state"])
                                            ).classes("text-body2")
                                            ui.badge(str(item["count"])).props("outline")
                        with ui.element("section").classes("w-full pt-3"):
                            ui.label("CONFERÊNCIAS").classes(
                                "text-caption text-weight-bold text-primary"
                            )
                            ui.label("Qualidade e revisão da carteira").classes(
                                "text-h5 text-weight-bold"
                            )
                            ui.label(
                                "Ferramentas de apoio para conferir fontes e tratar pendências sem misturá-las à leitura gerencial."
                            ).classes("text-body2 text-grey-7")

                            with ui.row().classes("w-full gap-3 flex-wrap mt-3"):
                                with ui.card().classes(
                                    "flex-1 min-w-[300px] p-5 gap-3 shadow-sm"
                                ):
                                    with ui.row().classes("w-full items-start justify-between gap-3"):
                                        with ui.row().classes("items-center gap-3"):
                                            ui.icon("fact_check", size="26px").classes("text-primary")
                                            with ui.column().classes("gap-0"):
                                                ui.label("Duplicidades").classes("text-subtitle1 text-weight-bold")
                                                ui.label("Revisão humana da carteira").classes("text-caption text-grey-7")
                                        ui.badge(str(pending_count), color="warning" if pending_count else "positive")
                                    with ui.row().classes("w-full gap-6"):
                                        with ui.column().classes("gap-0"):
                                            ui.label(str(len(rows))).classes("text-h6 text-weight-bold")
                                            ui.label("identificadas").classes("text-caption text-grey-7")
                                        with ui.column().classes("gap-0"):
                                            ui.label(str(reviewed_count)).classes("text-h6 text-weight-bold")
                                            ui.label("revisadas").classes("text-caption text-grey-7")
                                    ui.button(
                                        "Abrir fila de revisão",
                                        icon="arrow_forward",
                                        on_click=lambda: tabs.set_value(review_tab),
                                    ).props("flat no-caps").classes("self-start")

                                with ui.card().classes(
                                    "flex-1 min-w-[300px] p-5 gap-3 shadow-sm"
                                ):
                                    with ui.row().classes("w-full items-start justify-between gap-3"):
                                        with ui.row().classes("items-center gap-3"):
                                            ui.icon("table_chart", size="26px").classes("text-primary")
                                            with ui.column().classes("gap-0"):
                                                ui.label("Fontes operacionais").classes("text-subtitle1 text-weight-bold")
                                                ui.label("Conferência das grades Google Sheets").classes("text-caption text-grey-7")
                                        ui.badge("Sob demanda").props("outline")
                                    ui.label(
                                        "Consulta complementar das três grades. Um mesmo orçamento pode aparecer em mais de uma fonte."
                                    ).classes("text-body2 text-grey-7")
                                    sheets_result = ui.column().classes("w-full gap-2")

                                    async def load_sheets_summary():
                                        from nicegui import run

                                        load_button.disable()
                                        sheets_result.clear()
                                        with sheets_result:
                                            ui.label("Consultando as três grades...").classes("text-body2 text-grey-7")
                                        try:
                                            summary = await run.io_bound(get_particular_sheets_summary, access)
                                        except Exception:
                                            sheets_result.clear()
                                            with sheets_result:
                                                ui.label(
                                                    "Não foi possível carregar os indicadores das grades."
                                                ).classes("text-negative")
                                            return
                                        finally:
                                            load_button.enable()

                                        sheets_result.clear()
                                        with sheets_result:
                                            with ui.row().classes("w-full gap-5 flex-wrap"):
                                                with ui.column().classes("gap-0"):
                                                    ui.label(
                                                        f'{summary["orcamentos_distintos_total"]:,}'.replace(",", ".")
                                                    ).classes("text-h6 text-weight-bold")
                                                    ui.label("orçamentos distintos").classes("text-caption text-grey-7")
                                                with ui.column().classes("gap-0"):
                                                    ui.label(
                                                        f'{summary["orcamentos_em_mais_de_uma_aba"]:,}'.replace(",", ".")
                                                    ).classes("text-h6 text-weight-bold")
                                                    ui.label("em mais de uma grade").classes("text-caption text-grey-7")
                                            with ui.row().classes("w-full gap-4 flex-wrap"):
                                                for name, stats in summary["abas"].items():
                                                    with ui.column().classes("gap-0 min-w-[120px]"):
                                                        ui.label(name).classes("text-caption text-grey-7")
                                                        ui.label(
                                                            f'{stats["orcamentos_distintos"]:,}'.replace(",", ".")
                                                        ).classes("text-subtitle1 text-weight-bold")
                                            ui.label(
                                                "Presença em grade é evidência operacional e não comprova realização."
                                            ).classes("text-caption text-grey-7")

                                    load_button = ui.button(
                                        "Consultar fontes",
                                        icon="refresh",
                                        on_click=load_sheets_summary,
                                    ).props("flat no-caps").classes("self-start")


                with ui.tab_panel(operation_tab).classes("px-0 py-2"):
                    render_particular_work_queue(access=access, competence=active_competence.reference_date)

                with ui.tab_panel(import_tab).classes("px-0 py-2"):
                    with ui.column().classes("w-full gap-5"):
                            with ui.element("section").classes("w-full pt-1"):
                                ui.label("FONTES DA COMPETÊNCIA").classes("text-caption text-weight-bold text-primary")
                                ui.label("Base informacional do mês").classes("text-h5 text-weight-bold")
                                ui.label("Últimas fontes concluídas que sustentam a leitura desta competência.").classes("text-body2 text-grey-7")
                                with ui.row().classes("w-full gap-3 flex-wrap mt-3"):
                                    source_icons = {"XML": "description", "GRADES": "table_view", "EVOLUTION": "history_edu"}
                                    for source in competence_sources:
                                        available = source.status == "AVAILABLE"
                                        with ui.card().classes("flex-1 min-w-[260px] p-4 gap-2 shadow-sm"):
                                            with ui.row().classes("w-full items-center justify-between gap-3"):
                                                with ui.row().classes("items-center gap-3"):
                                                    ui.icon(source_icons.get(source.source, "database"), size="24px").classes("text-primary" if available else "text-grey-5")
                                                    ui.label(source.label).classes("text-subtitle1 text-weight-bold")
                                                ui.icon("check_circle" if available else "warning", size="20px").classes("text-positive" if available else "text-warning")
                                            ui.label("Disponível" if available else "Não identificada").classes("text-caption text-positive" if available else "text-caption text-warning")
                                            ui.label(source.detail).classes("text-body2 text-grey-7")
                                            if source.filename:
                                                ui.label(source.filename).classes("text-caption text-grey-7 ellipsis")
                                            if source.processed_at:
                                                ui.label("Último processamento: " + _date(source.processed_at)).classes("text-caption text-grey-7")
                                            if available:
                                                source_summary = str(source.records_processed) + " registros processados"
                                                source_summary += (" · " + str(source.records_error) + " erro(s)") if source.records_error else " · sem erros"
                                                ui.label(source_summary).classes("text-caption text-grey-7")
                            render_particular_import(access=access)

                with ui.tab_panel(review_tab).classes("px-0 py-2"):
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

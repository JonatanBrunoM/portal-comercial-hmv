from __future__ import annotations

from nicegui import ui

from nicegui_app.hero_art import render_hero_art
from nicegui_app.layout import portal_layout
from nicegui_app.services.consultores_service import (
    CarteiraPreview,
    ConsultorPreview,
    get_consultor_detail,
    get_consultores_preview,
)


def _normalized(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _is_active(status: str) -> bool:
    return _normalized(status) == "ativo"


def _initials(name: str) -> str:
    parts = [part for part in name.split() if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _hero_step(icon: str, title: str, subtitle: str) -> None:
    with ui.element("div").classes("portal-consultants-hero-step"):
        with ui.element("div").classes("portal-consultants-hero-step-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-consultants-hero-step-copy"):
            ui.label(title).classes("portal-consultants-hero-step-title")
            ui.label(subtitle).classes("portal-consultants-hero-step-subtitle")


def _operator_names(consultant: ConsultorPreview) -> list[str]:
    names: list[str] = []
    for wallet in consultant.wallets:
        name = wallet.operator_name.strip()
        if name and name not in names:
            names.append(name)
    return names


def _consultant_card(consultant: ConsultorPreview) -> None:
    operator_names = _operator_names(consultant)

    with ui.element("article").classes("portal-consultant-card"):
        with ui.row().classes("portal-consultant-card-head"):
            with ui.row().classes("portal-consultant-card-identity"):
                ui.avatar(_initials(consultant.name)).classes("portal-consultant-avatar")
                with ui.column().classes("portal-consultant-card-heading"):
                    ui.label(consultant.name).classes("portal-consultant-card-title")
                    if consultant.job_title:
                        ui.label(consultant.job_title).classes("portal-consultant-card-role")

            with ui.element("div").classes(
                "portal-consultant-status is-active"
                if _is_active(consultant.status)
                else "portal-consultant-status"
            ):
                ui.element("span").classes("portal-consultant-status-dot")
                ui.label(consultant.status)

        with ui.element("div").classes("portal-consultant-scope"):
            with ui.row().classes("portal-consultant-scope-head"):
                ui.icon("business_center")
                ui.label("CARTEIRA DE RELACIONAMENTO").classes("portal-consultant-scope-label")

            if operator_names:
                with ui.row().classes("portal-consultant-operator-chips"):
                    for operator_name in operator_names[:3]:
                        ui.label(operator_name).classes("portal-consultant-operator-chip")
                    if len(operator_names) > 3:
                        ui.label(f"+{len(operator_names) - 3}").classes(
                            "portal-consultant-operator-chip is-more"
                        )
            else:
                ui.label("Nenhuma operadora vinculada").classes(
                    "portal-consultant-scope-empty"
                )

        with ui.row().classes("portal-consultant-card-metrics"):
            with ui.column().classes("portal-consultant-card-metric"):
                ui.label(str(consultant.operators_count).zfill(2)).classes(
                    "portal-consultant-card-metric-value"
                )
                ui.label("Operadoras").classes("portal-consultant-card-metric-label")

            with ui.column().classes("portal-consultant-card-metric"):
                ui.label(str(consultant.plans_count).zfill(2)).classes(
                    "portal-consultant-card-metric-value"
                )
                ui.label("Planos").classes("portal-consultant-card-metric-label")

        with ui.element("div").classes("portal-consultant-contact-block"):
            if consultant.email:
                with ui.row().classes("portal-consultant-detail-line"):
                    ui.icon("mail")
                    with ui.column().classes("portal-consultant-detail-line-copy"):
                        ui.label("E-mail").classes("portal-consultant-detail-line-label")
                        ui.label(consultant.email).classes("portal-consultant-detail-line-value")

            if consultant.phone:
                with ui.row().classes("portal-consultant-detail-line"):
                    ui.icon("phone")
                    with ui.column().classes("portal-consultant-detail-line-copy"):
                        ui.label("Telefone").classes("portal-consultant-detail-line-label")
                        ui.label(consultant.phone).classes("portal-consultant-detail-line-value")

        with ui.row().classes("portal-consultant-card-actions"):
            ui.button(
                "Ver carteira",
                icon="arrow_forward",
                on_click=lambda cid=consultant.consultant_id: ui.navigate.to(
                    f"/consultores/{cid}"
                ),
            ).props("flat no-caps").classes("portal-consultant-detail-button")

            if consultant.email:
                ui.link("Enviar e-mail", target=f"mailto:{consultant.email}").classes(
                    "portal-consultant-action-link"
                )


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-consultants-empty"):
        ui.icon("support_agent")
        ui.label(title).classes("portal-consultants-empty-title")
        ui.label(description).classes("portal-consultants-empty-description")


def render_consultores(user: dict) -> None:
    consultants = get_consultores_preview()

    with portal_layout(user=user, active="consultants"):
        operators = sorted(
            {
                wallet.operator_name
                for consultant in consultants
                for wallet in consultant.wallets
                if wallet.operator_name
            }
        )
        statuses = sorted({consultant.status for consultant in consultants if consultant.status})

        with ui.element("section").classes("portal-consultants-hero"):
            with ui.column().classes("portal-consultants-hero-copy"):
                ui.label("CARTEIRAS & RELACIONAMENTO").classes(
                    "portal-consultants-hero-kicker"
                )
                ui.label("Encontre quem cuida de cada relacionamento.").classes(
                    "portal-consultants-hero-title"
                )
                ui.label(
                    "Consulte responsáveis comerciais, canais de contato e vínculos com "
                    "operadoras e planos em uma única visão."
                ).classes("portal-consultants-hero-description")

            render_hero_art(variant="consultants", icon="support_agent")

            with ui.element("div").classes("portal-consultants-hero-flow"):
                _hero_step("person_search", "IDENTIFIQUE", "o responsável")
                _hero_step("business_center", "CONFIRA", "a carteira atendida")
                _hero_step("alternate_email", "ACIONE", "pelo canal correto")

        with ui.element("section").classes("portal-consultants-searchbar"):
            search = ui.input(
                placeholder="Buscar consultor, cargo, e-mail, telefone, operadora ou plano..."
            ).props("borderless clearable prepend-icon=search").classes(
                "portal-consultants-search"
            )
            ui.button(
                "Pesquisar",
                icon="arrow_forward",
                on_click=lambda: refresh(),
            ).props("unelevated no-caps").classes("portal-consultants-search-button")

        selected_operator = {"value": "Todas"}
        operator_buttons: dict[str, object] = {}

        with ui.element("section").classes("portal-consultants-filterbar"):
            with ui.row().classes("portal-consultants-operator-filter"):
                ui.label("OPERADORA").classes("portal-consultants-filter-caption")
                for name in ["Todas"] + operators:
                    button = ui.button(name).props("flat no-caps").classes(
                        "portal-consultants-chip"
                    )
                    operator_buttons[name] = button

            with ui.row().classes("portal-consultants-selects"):
                status = ui.select(
                    options=["Todos"] + statuses,
                    value="Todos",
                    label="Status",
                ).props("outlined dense").classes("portal-consultants-filter")

        with ui.element("section").classes("portal-consultants-guidance"):
            with ui.element("div").classes("portal-consultants-guidance-icon"):
                ui.icon("hub")
            with ui.column().classes("portal-consultants-guidance-copy"):
                ui.label("CARTEIRAS OFICIAIS").classes("portal-consultants-guidance-title")
                ui.label(
                    "Os vínculos exibidos refletem as carteiras cadastradas no Portal Comercial. "
                    "Use esta tela para localizar rapidamente o responsável por cada operadora."
                ).classes("portal-consultants-guidance-text")
            ui.label("Relacionamento comercial").classes("portal-consultants-guidance-side")

        with ui.row().classes("portal-consultants-results-head"):
            with ui.column().classes("portal-consultants-results-copy"):
                ui.label("CONSULTORES DISPONÍVEIS").classes(
                    "portal-consultants-results-kicker"
                )
                result_label = ui.label("").classes("portal-consultants-result-label")
            ui.label(
                "Contato e principais vínculos já aparecem no card para reduzir cliques."
            ).classes("portal-consultants-results-note")

        cards = ui.element("div").classes("portal-consultants-grid")

        def update_operator_buttons() -> None:
            for name, button in operator_buttons.items():
                button.classes(
                    add="is-active" if name == selected_operator["value"] else "",
                    remove="" if name == selected_operator["value"] else "is-active",
                )

        def choose_operator(name: str) -> None:
            selected_operator["value"] = name
            update_operator_buttons()
            refresh()

        for name, button in operator_buttons.items():
            button.on_click(lambda _, current=name: choose_operator(current))

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_status = status.value or "Todos"
            selected = selected_operator["value"]
            filtered: list[ConsultorPreview] = []

            for consultant in consultants:
                wallet_text = " ".join(
                    f"{wallet.operator_name} {wallet.plan_name} {wallet.role}"
                    for wallet in consultant.wallets
                )
                haystack = _normalized(
                    " ".join(
                        (
                            consultant.name,
                            consultant.job_title,
                            consultant.email,
                            consultant.phone,
                            consultant.code,
                            consultant.observations,
                            wallet_text,
                        )
                    )
                )
                operator_ok = selected == "Todas" or any(
                    wallet.operator_name == selected for wallet in consultant.wallets
                )
                status_ok = selected_status == "Todos" or consultant.status == selected_status

                if (not term or term in haystack) and operator_ok and status_ok:
                    filtered.append(consultant)

            result_label.set_text(f"{len(filtered)} consultor(es) encontrado(s)")
            cards.clear()

            with cards:
                if not filtered:
                    _empty(
                        "Nenhum consultor encontrado.",
                        "Revise a pesquisa ou altere os filtros selecionados.",
                    )
                    return
                for consultant in filtered:
                    _consultant_card(consultant)

        search.on("keydown.enter", lambda _: refresh())
        status.on_value_change(lambda _: refresh())
        update_operator_buttons()
        refresh()


def _detail_item(icon: str, label: str, value: str) -> None:
    if not value:
        return

    with ui.element("div").classes("portal-consultant-detail-item"):
        ui.icon(icon)
        with ui.column().classes("portal-consultant-detail-item-copy"):
            ui.label(label).classes("portal-consultant-detail-label")
            ui.label(value).classes("portal-consultant-detail-value")


def _wallet_card(wallet: CarteiraPreview) -> None:
    with ui.element("article").classes("portal-wallet-card"):
        with ui.row().classes("portal-wallet-card-top"):
            with ui.element("div").classes("portal-wallet-icon"):
                ui.icon("business_center")
            with ui.element("div").classes(
                "portal-wallet-status is-active"
                if _is_active(wallet.status)
                else "portal-wallet-status"
            ):
                ui.element("span").classes("portal-wallet-status-dot")
                ui.label(wallet.status)

        ui.label(wallet.operator_name).classes("portal-wallet-title")

        if wallet.plan_name:
            ui.label(wallet.plan_name).classes("portal-wallet-plan")

        if wallet.role:
            with ui.row().classes("portal-wallet-role"):
                ui.icon("badge")
                ui.label(wallet.role)

        if wallet.observations:
            ui.label(wallet.observations).classes("portal-wallet-observations")


def render_consultor_detail(user: dict, consultant_id: str) -> None:
    consultant = get_consultor_detail(consultant_id)

    with portal_layout(user=user, active="consultants"):
        if consultant is None:
            _empty(
                "Consultor não encontrado.",
                "O registro pode ter sido removido ou o endereço está incorreto.",
            )
            return

        ui.button(
            "Voltar para Consultores",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/consultores"),
        ).props("flat no-caps").classes("portal-consultant-back-button")

        with ui.element("section").classes("portal-consultant-detail-hero"):
            ui.avatar(_initials(consultant.name)).classes("portal-consultant-detail-avatar")

            with ui.column().classes("portal-consultant-detail-copy"):
                ui.label("FICHA DO CONSULTOR").classes("portal-section-kicker")
                ui.label(consultant.name).classes("portal-consultant-detail-title")
                if consultant.job_title:
                    ui.label(consultant.job_title).classes("portal-consultant-detail-role")

            if consultant.email:
                ui.link("Enviar e-mail", target=f"mailto:{consultant.email}").classes(
                    "portal-consultant-primary-action"
                )

        with ui.element("section").classes("portal-consultant-detail-grid"):
            _detail_item("mail", "E-mail", consultant.email)
            _detail_item("phone", "Telefone", consultant.phone)
            _detail_item("business", "Operadoras", str(consultant.operators_count))
            _detail_item("view_list", "Planos", str(consultant.plans_count))
            _detail_item("tag", "Código", consultant.code)
            _detail_item("fact_check", "Status", consultant.status)

        with ui.element("section").classes("portal-wallet-section"):
            ui.label("CARTEIRA DE RELACIONAMENTO").classes("portal-section-kicker")
            ui.label("Operadoras e planos sob responsabilidade").classes(
                "portal-wallet-section-title"
            )
            ui.label(
                "Os vínculos abaixo são carregados da tabela de carteiras."
            ).classes("portal-wallet-section-description")

            with ui.element("div").classes("portal-wallet-grid"):
                if consultant.wallets:
                    for wallet in consultant.wallets:
                        _wallet_card(wallet)
                else:
                    _empty(
                        "Nenhuma carteira vinculada.",
                        "Este consultor ainda não possui operadoras ou planos associados.",
                    )

        if consultant.observations:
            with ui.element("section").classes("portal-consultant-notes-card"):
                with ui.row().classes("portal-consultant-notes-head"):
                    ui.icon("info")
                    ui.label("Observações").classes("portal-consultant-notes-title")
                ui.label(consultant.observations).classes("portal-consultant-notes-text")

from __future__ import annotations

from nicegui import ui

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


def _consultant_card(consultant: ConsultorPreview) -> None:
    with ui.element("article").classes("portal-consultant-card"):
        with ui.row().classes("portal-consultant-card-top"):
            ui.avatar(_initials(consultant.name)).classes(
                "portal-consultant-avatar"
            )

            with ui.element("div").classes(
                "portal-consultant-status is-active"
                if _is_active(consultant.status)
                else "portal-consultant-status"
            ):
                ui.element("span").classes("portal-consultant-status-dot")
                ui.label(consultant.status)

        ui.label(consultant.name).classes("portal-consultant-card-title")

        if consultant.job_title:
            ui.label(consultant.job_title).classes("portal-consultant-card-role")

        with ui.row().classes("portal-consultant-card-metrics"):
            with ui.column().classes("portal-consultant-card-metric"):
                ui.label(str(consultant.operators_count).zfill(2)).classes(
                    "portal-consultant-card-metric-value"
                )
                ui.label("Operadoras").classes(
                    "portal-consultant-card-metric-label"
                )

            with ui.column().classes("portal-consultant-card-metric"):
                ui.label(str(consultant.plans_count).zfill(2)).classes(
                    "portal-consultant-card-metric-value"
                )
                ui.label("Planos").classes(
                    "portal-consultant-card-metric-label"
                )

        if consultant.email:
            with ui.row().classes("portal-consultant-detail-line"):
                ui.icon("mail")
                ui.label(consultant.email)

        if consultant.phone:
            with ui.row().classes("portal-consultant-detail-line"):
                ui.icon("phone")
                ui.label(consultant.phone)

        with ui.row().classes("portal-consultant-card-actions"):
            ui.button(
                "Ver carteira",
                icon="arrow_forward",
                on_click=lambda cid=consultant.consultant_id: ui.navigate.to(
                    f"/consultores/{cid}"
                ),
            ).props("flat no-caps").classes(
                "portal-consultant-detail-button"
            )

            if consultant.email:
                ui.link(
                    "Enviar e-mail",
                    target=f"mailto:{consultant.email}",
                ).classes("portal-consultant-action-link")


def _empty(title: str, description: str) -> None:
    with ui.element("div").classes("portal-consultants-empty"):
        ui.icon("support_agent")
        ui.label(title).classes("portal-consultants-empty-title")
        ui.label(description).classes(
            "portal-consultants-empty-description"
        )


def render_consultores(user: dict) -> None:
    consultants = get_consultores_preview()

    with portal_layout(
        user=user,
        active="consultants",
        page_eyebrow="RELACIONAMENTO COMERCIAL",
        page_title="Quem cuida de cada carteira.",
        page_description=(
            "Consulte consultores, contatos e vínculos com operadoras e planos."
        ),
    ):
        operators = sorted({
            wallet.operator_name
            for consultant in consultants
            for wallet in consultant.wallets
            if wallet.operator_name
        })

        with ui.element("section").classes("portal-consultants-summary"):
            with ui.column().classes("portal-consultants-summary-copy"):
                ui.label("CONSULTORES").classes("portal-section-kicker")
                ui.label(f"{len(consultants):02d} consultores cadastrados").classes(
                    "portal-consultants-summary-value"
                )
                ui.label(
                    "Responsáveis e respectivas carteiras de relacionamento."
                ).classes("portal-consultants-summary-description")

            with ui.row().classes("portal-consultants-summary-stats"):
                with ui.column().classes("portal-consultants-mini-stat"):
                    ui.label(
                        str(sum(1 for c in consultants if _is_active(c.status))).zfill(2)
                    ).classes("portal-consultants-mini-value")
                    ui.label("Ativos").classes("portal-consultants-mini-label")

                with ui.column().classes("portal-consultants-mini-stat"):
                    ui.label(str(len(operators)).zfill(2)).classes(
                        "portal-consultants-mini-value"
                    )
                    ui.label("Operadoras").classes(
                        "portal-consultants-mini-label"
                    )

        with ui.element("section").classes("portal-consultants-toolbar"):
            search = ui.input(
                placeholder="Buscar consultor, cargo, e-mail ou operadora"
            ).props("outlined dense clearable prepend-icon=search").classes(
                "portal-consultants-search"
            )

            operator = ui.select(
                options=["Todas"] + operators,
                value="Todas",
                label="Operadora",
            ).props("outlined dense").classes("portal-consultants-filter")

        result_label = ui.label("").classes("portal-consultants-result-label")
        cards = ui.element("div").classes("portal-consultants-grid")

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected_operator = operator.value or "Todas"

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
                            wallet_text,
                        )
                    )
                )

                operator_ok = (
                    selected_operator == "Todas"
                    or any(
                        wallet.operator_name == selected_operator
                        for wallet in consultant.wallets
                    )
                )

                if (not term or term in haystack) and operator_ok:
                    filtered.append(consultant)

            result_label.set_text(
                f"{len(filtered)} consultor(es) encontrado(s)"
            )
            cards.clear()

            with cards:
                if not filtered:
                    _empty(
                        "Nenhum consultor encontrado.",
                        "Revise a pesquisa ou altere o filtro.",
                    )
                    return

                for consultant in filtered:
                    _consultant_card(consultant)

        search.on_value_change(lambda _: refresh())
        operator.on_value_change(lambda _: refresh())
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
            ui.label(wallet.observations).classes(
                "portal-wallet-observations"
            )


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
            ui.avatar(_initials(consultant.name)).classes(
                "portal-consultant-detail-avatar"
            )

            with ui.column().classes("portal-consultant-detail-copy"):
                ui.label("FICHA DO CONSULTOR").classes("portal-section-kicker")
                ui.label(consultant.name).classes(
                    "portal-consultant-detail-title"
                )
                if consultant.job_title:
                    ui.label(consultant.job_title).classes(
                        "portal-consultant-detail-role"
                    )

            if consultant.email:
                ui.link(
                    "Enviar e-mail",
                    target=f"mailto:{consultant.email}",
                ).classes("portal-consultant-primary-action")

        with ui.element("section").classes("portal-consultant-detail-grid"):
            _detail_item("mail", "E-mail", consultant.email)
            _detail_item("phone", "Telefone", consultant.phone)
            _detail_item(
                "business",
                "Operadoras",
                str(consultant.operators_count),
            )
            _detail_item(
                "view_list",
                "Planos",
                str(consultant.plans_count),
            )
            _detail_item("tag", "Código", consultant.code)
            _detail_item("fact_check", "Status", consultant.status)

        with ui.element("section").classes("portal-wallet-section"):
            ui.label("CARTEIRA DE RELACIONAMENTO").classes(
                "portal-section-kicker"
            )
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
            with ui.element("section").classes(
                "portal-consultant-notes-card"
            ):
                with ui.row().classes("portal-consultant-notes-head"):
                    ui.icon("info")
                    ui.label("Observações").classes(
                        "portal-consultant-notes-title"
                    )
                ui.label(consultant.observations).classes(
                    "portal-consultant-notes-text"
                )

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from nicegui import ui

from nicegui_app.layout import portal_layout
from nicegui_app.services.operadoras_service import (
    OperadoraPreview,
    get_operadora_detail,
    get_operadoras_preview,
)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _normalized(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _is_active(status: str) -> bool:
    return _normalized(status) == "ativo"


def _safe_external_url(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return None


def _operator_mark(operator: OperadoraPreview) -> None:
    if operator.logo_url:
        ui.image(operator.logo_url).classes("portal-operator-logo-image")
        return

    initials = (
        "".join(word[0] for word in operator.short_name.split() if word)[:2].upper()
        or "OP"
    )
    ui.label(initials).classes("portal-operator-initials")


def _operator_feature(icon: str, title: str, description: str) -> None:
    with ui.element("div").classes("portal-operator-feature"):
        with ui.element("div").classes("portal-operator-feature-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-operator-feature-copy"):
            ui.label(title).classes("portal-operator-feature-title")
            ui.label(description).classes("portal-operator-feature-description")


def _operator_card(operator: OperadoraPreview, *, list_mode: bool = False) -> None:
    website = _safe_external_url(operator.site_url)
    card_class = "portal-operator-card is-list" if list_mode else "portal-operator-card"

    with ui.element("article").classes(card_class):
        with ui.element("div").classes("portal-operator-card-top"):
            with ui.element("div").classes("portal-operator-card-mark"):
                _operator_mark(operator)

            with ui.column().classes("portal-operator-card-copy"):
                with ui.row().classes("portal-operator-card-heading"):
                    ui.label(operator.short_name).classes("portal-operator-card-title")
                    with ui.element(
                        "span"
                    ).classes(
                        "portal-operator-status is-active"
                        if _is_active(operator.status)
                        else "portal-operator-status"
                    ):
                        ui.element("span").classes("portal-operator-status-dot")
                        ui.label(operator.status)

                if operator.name != operator.short_name:
                    ui.label(operator.name).classes("portal-operator-card-full-name")

                with ui.row().classes("portal-operator-card-meta"):
                    if operator.code:
                        with ui.element("span").classes("portal-operator-card-meta-item"):
                            ui.icon("settings")
                            ui.label(operator.code)

                    with ui.element("span").classes("portal-operator-card-meta-item"):
                        ui.icon("account_tree")
                        ui.label("Central de informações")

                ui.label(
                    operator.observations
                    or (
                        "Consulte orientações, acessos, documentos, contatos, "
                        "autorizações e demais informações desta operadora."
                    )
                ).classes("portal-operator-card-description")

        with ui.element("div").classes("portal-operator-card-features"):
            _operator_feature(
                "vpn_key",
                "Portais e acessos",
                "Sistemas, links e orientações.",
            )
            _operator_feature(
                "description",
                "Guias e documentos",
                "Referências para atendimento.",
            )
            _operator_feature(
                "contacts",
                "Contatos",
                "Centrais e responsáveis.",
            )

        with ui.element("div").classes("portal-operator-card-footer"):
            if website:
                ui.link(
                    "Site da operadora",
                    target=website,
                    new_tab=True,
                ).classes("portal-operator-site-action")
            else:
                ui.label("Informações institucionais").classes(
                    "portal-operator-site-action is-disabled"
                )

            ui.button(
                "Ver detalhes da operadora",
                icon="arrow_forward",
                on_click=lambda oid=operator.operator_id: ui.navigate.to(
                    f"/operadoras/{oid}"
                ),
            ).props("unelevated no-caps").classes("portal-operator-detail-action")


def render_operadoras(user: dict) -> None:
    operators = get_operadoras_preview()

    with portal_layout(user=user, active="operators"):
        with ui.element("section").classes("portal-operators-hero"):
            with ui.column().classes("portal-operators-hero-copy"):
                ui.label("CENTRAL DE OPERADORAS").classes("portal-operators-hero-kicker")
                ui.label(
                    "Tudo sobre as operadoras, em um só lugar."
                ).classes("portal-operators-hero-title")
                ui.label(
                    "Acesse rapidamente portais, orientações, contatos, documentos "
                    "e informações atualizadas para conduzir o atendimento."
                ).classes("portal-operators-hero-description")

            with ui.element("div").classes("portal-operators-hero-side"):
                for icon, title, subtitle in (
                    ("bolt", "Atendimento", "mais ágil"),
                    ("verified_user", "Informação", "segura"),
                    ("groups", "Parceria", "pela saúde"),
                ):
                    with ui.element("div").classes("portal-operators-hero-point"):
                        with ui.element("div").classes("portal-operators-hero-point-icon"):
                            ui.icon(icon)
                        with ui.column().classes("portal-operators-hero-point-copy"):
                            ui.label(title).classes("portal-operators-hero-point-title")
                            ui.label(subtitle).classes("portal-operators-hero-point-subtitle")

            with ui.element("div").classes("portal-operators-hero-watermark"):
                ui.icon("domain")

        filter_state = {"value": "Todos"}
        sort_state = {"value": "Nome (A–Z)"}
        view_state = {"value": "grid"}
        filter_buttons: dict[str, Any] = {}
        view_buttons: dict[str, Any] = {}

        with ui.element("section").classes("portal-operators-toolbar"):
            with ui.element("div").classes("portal-operators-search-box"):
                ui.icon("search")
                search = ui.input(
                    placeholder="Buscar operadora por nome, código ou palavra-chave..."
                ).props(
                    "borderless dense clearable autocomplete='off'"
                ).classes("portal-operators-search-input")
                ui.button(
                    "Pesquisar",
                    icon="arrow_forward",
                    on_click=lambda: refresh(),
                ).props("unelevated no-caps").classes("portal-operators-search-button")

            with ui.element("div").classes("portal-operators-status-filter"):
                ui.label("FILTRAR POR STATUS").classes("portal-operators-control-label")
                with ui.element("div").classes("portal-operators-status-actions"):
                    for value, label in (
                        ("Todos", "Todas"),
                        ("Ativo", "Ativas"),
                        ("Outros", "Outras"),
                    ):
                        button = ui.button(
                            label,
                            on_click=lambda selected=value: set_filter(selected),
                        ).props("flat no-caps").classes("portal-operators-status-button")
                        filter_buttons[value] = button

        with ui.element("section").classes("portal-operators-directory-head"):
            with ui.column().classes("portal-operators-directory-title-copy"):
                ui.label("OPERADORAS CADASTRADAS").classes("portal-section-kicker")
                results_label = ui.label("").classes("portal-operators-directory-count")

            with ui.element("div").classes("portal-operators-directory-tools"):
                ui.label("Ordenar por").classes("portal-operators-order-label")
                order_select = ui.select(
                    ["Nome (A–Z)", "Nome (Z–A)", "Código"],
                    value="Nome (A–Z)",
                ).props("outlined dense options-dense").classes("portal-operators-order-select")

                with ui.element("div").classes("portal-operators-view-switch"):
                    grid_button = ui.button(
                        icon="grid_view",
                        on_click=lambda: set_view("grid"),
                    ).props("flat dense round").classes("portal-operators-view-button")
                    list_button = ui.button(
                        icon="view_list",
                        on_click=lambda: set_view("list"),
                    ).props("flat dense round").classes("portal-operators-view-button")
                    view_buttons["grid"] = grid_button
                    view_buttons["list"] = list_button

        directory = ui.element("div").classes("portal-operators-card-grid")

        def ordered(items: list[OperadoraPreview]) -> list[OperadoraPreview]:
            mode = sort_state["value"]
            if mode == "Nome (Z–A)":
                return sorted(items, key=lambda item: item.short_name.casefold(), reverse=True)
            if mode == "Código":
                return sorted(items, key=lambda item: item.code.casefold())
            return sorted(items, key=lambda item: item.short_name.casefold())

        def refresh() -> None:
            term = _normalized(search.value or "")
            selected = filter_state["value"]
            sort_state["value"] = str(order_select.value or "Nome (A–Z)")

            filtered: list[OperadoraPreview] = []
            for operator in operators:
                haystack = _normalized(
                    " ".join(
                        (
                            operator.name,
                            operator.short_name,
                            operator.code,
                            operator.observations,
                        )
                    )
                )
                status_ok = (
                    selected == "Todos"
                    or (selected == "Ativo" and _is_active(operator.status))
                    or (selected == "Outros" and not _is_active(operator.status))
                )
                if (not term or term in haystack) and status_ok:
                    filtered.append(operator)

            filtered = ordered(filtered)

            for value, button in filter_buttons.items():
                button.classes(
                    add="is-selected" if value == selected else "",
                    remove="" if value == selected else "is-selected",
                )

            for value, button in view_buttons.items():
                button.classes(
                    add="is-selected" if value == view_state["value"] else "",
                    remove="" if value == view_state["value"] else "is-selected",
                )

            count = len(filtered)
            results_label.set_text(
                f"{count} operadora{'s' if count != 1 else ''} encontrada"
                f"{'s' if count != 1 else ''}"
            )

            directory.classes(
                add="is-list" if view_state["value"] == "list" else "",
                remove="" if view_state["value"] == "list" else "is-list",
            )
            directory.clear()

            with directory:
                if not filtered:
                    _empty(
                        "Nenhuma operadora encontrada.",
                        "Tente outro nome ou ajuste os filtros.",
                        "search_off",
                    )
                    return

                for operator in filtered:
                    _operator_card(
                        operator,
                        list_mode=view_state["value"] == "list",
                    )

        def set_filter(value: str) -> None:
            filter_state["value"] = value
            refresh()

        def set_view(value: str) -> None:
            view_state["value"] = value
            refresh()

        search.on_value_change(lambda _: refresh())
        order_select.on_value_change(lambda _: refresh())

        refresh()

        with ui.element("section").classes("portal-operators-help"):
            with ui.element("div").classes("portal-operators-help-message"):
                with ui.element("div").classes("portal-operators-help-icon"):
                    ui.icon("info")
                with ui.column().classes("portal-operators-help-copy"):
                    ui.label("Não encontrou o que precisa?").classes(
                        "portal-operators-help-title"
                    )
                    ui.label(
                        "Use a pesquisa do Portal ou fale com o time responsável."
                    ).classes("portal-operators-help-description")

            ui.button(
                "Falar com um consultor",
                icon="support_agent",
                on_click=lambda: ui.navigate.to("/consultores"),
            ).props("flat no-caps").classes("portal-operators-help-action")

def _empty(title: str, description: str, icon: str = "inventory_2") -> None:
    with ui.element("div").classes("portal-operators-empty"):
        ui.icon(icon)
        ui.label(title).classes("portal-operators-empty-title")
        ui.label(description).classes("portal-operators-empty-description")



def _detail_summary_item(icon: str, label: str, value: str, helper: str = "") -> None:
    with ui.element("div").classes("portal-operator-summary-item"):
        with ui.element("div").classes("portal-operator-summary-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-operator-summary-copy"):
            ui.label(label).classes("portal-operator-summary-label")
            ui.label(value).classes("portal-operator-summary-value")
            if helper:
                ui.label(helper).classes("portal-operator-summary-helper")


def _info_row(title: str, lines: list[tuple[str, str]], icon: str = "article") -> None:
    with ui.element("article").classes("portal-hub-card"):
        with ui.element("div").classes("portal-hub-card-icon"):
            ui.icon(icon)

        with ui.column().classes("portal-hub-card-copy"):
            ui.label(title).classes("portal-hub-card-title")

            with ui.element("div").classes("portal-hub-card-fields"):
                for label, value in lines:
                    if value:
                        with ui.element("div").classes("portal-hub-card-field"):
                            ui.label(label).classes("portal-hub-card-field-label")
                            ui.label(value).classes("portal-hub-card-field-value")


def _render_planos(rows: tuple[dict[str, Any], ...]) -> None:
    if not rows:
        _empty("Nenhum plano cadastrado.", "Ainda não há planos vinculados.")
        return

    with ui.element("div").classes("portal-hub-card-grid"):
        for row in rows:
            _info_row(
                _text(row, "nome_padronizado", "nome") or "Plano sem nome",
                [
                    ("Código", _text(row, "codigo")),
                    ("Tipo", _text(row, "tipo_plano")),
                    ("Resumo", _text(row, "observacao_resumida")),
                    ("Status", _text(row, "status")),
                ],
                "view_list",
            )


def _render_portais(rows: tuple[dict[str, Any], ...]) -> None:
    if not rows:
        _empty(
            "Nenhum portal cadastrado.",
            "Ainda não há portais vinculados.",
            "vpn_key",
        )
        return

    with ui.element("div").classes("portal-hub-card-grid"):
        for row in rows:
            with ui.element("article").classes("portal-hub-card is-portal"):
                with ui.element("div").classes("portal-hub-card-icon"):
                    ui.icon("vpn_key")

                with ui.column().classes("portal-hub-card-copy"):
                    ui.label(_text(row, "nome") or "Portal").classes(
                        "portal-hub-card-title"
                    )

                    with ui.element("div").classes("portal-hub-card-fields"):
                        for label, value in [
                            ("Tipo", _text(row, "tipo")),
                            ("Instrução", _text(row, "instrucao_acesso")),
                            ("Dica", _text(row, "dica_geral_acesso")),
                            ("Observações", _text(row, "observacoes")),
                            ("Status", _text(row, "status")),
                        ]:
                            if value:
                                with ui.element("div").classes("portal-hub-card-field"):
                                    ui.label(label).classes(
                                        "portal-hub-card-field-label"
                                    )
                                    ui.label(value).classes(
                                        "portal-hub-card-field-value"
                                    )

                url = _safe_external_url(_text(row, "url"))
                if url:
                    ui.link(
                        "Abrir portal",
                        target=url,
                        new_tab=True,
                    ).classes("portal-hub-card-action")


def _render_generic(rows, title_keys, fields, icon, empty_title):
    if not rows:
        _empty(
            empty_title,
            "Nenhum registro vinculado a esta operadora.",
            icon,
        )
        return

    with ui.element("div").classes("portal-hub-card-grid"):
        for row in rows:
            title = _text(row, *title_keys) or "Informação cadastrada"
            lines = [(label, _text(row, *keys)) for label, keys in fields]
            _info_row(title, lines, icon)


def render_operadora_detail(user: dict, operator_id: str) -> None:
    detail = get_operadora_detail(operator_id)

    with portal_layout(user=user, active="operators"):
        if detail is None:
            _empty(
                "Operadora não encontrada.",
                "O registro pode ter sido removido.",
                "domain_disabled",
            )
            return

        operator = detail.operator
        external_url = _safe_external_url(operator.site_url)

        total_info = sum(
            len(rows)
            for rows in (
                detail.planos,
                detail.portais,
                detail.elegibilidade,
                detail.documentos,
                detail.autorizacoes,
                detail.coberturas,
                detail.contatos,
                detail.contingencias,
                detail.dicas,
                detail.comunicados,
                detail.carteiras,
            )
        )

        # Navegação contextual compacta.
        with ui.row().classes("portal-operator-detail-nav"):
            ui.button(
                "Operadoras",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/operadoras"),
            ).props("flat no-caps").classes("portal-operator-back-button")

            with ui.row().classes("portal-operator-detail-nav-actions"):
                if external_url:
                    ui.link(
                        "Site da operadora",
                        target=external_url,
                        new_tab=True,
                    ).classes("portal-operator-nav-link")

                if detail.portais:
                    ui.button(
                        "Ver portais",
                        icon="vpn_key",
                        on_click=lambda: tabs.set_value(t_portais),
                    ).props("flat no-caps").classes("portal-operator-nav-action")

        # Hero da operadora: identidade + contexto, sem ocupar a tela toda.
        with ui.element("section").classes("portal-operator-detail-hero"):
            with ui.element("div").classes("portal-operator-detail-hero-pattern"):
                pass

            with ui.element("div").classes("portal-operator-detail-mark"):
                _operator_mark(operator)

            with ui.column().classes("portal-operator-detail-copy"):
                with ui.row().classes("portal-operator-detail-meta"):
                    ui.label("OPERADORA").classes("portal-operator-detail-kicker")
                    with ui.element(
                        "span"
                    ).classes(
                        "portal-operator-status is-active"
                        if _is_active(operator.status)
                        else "portal-operator-status"
                    ):
                        ui.element("span").classes("portal-operator-status-dot")
                        ui.label(operator.status)

                ui.label(operator.short_name).classes("portal-operator-detail-title")

                if operator.name != operator.short_name:
                    ui.label(operator.name).classes(
                        "portal-operator-detail-full-name"
                    )

                ui.label(
                    operator.observations
                    or (
                        "Centralize nesta página os acessos, planos, documentos, "
                        "contatos e regras relacionadas à operadora."
                    )
                ).classes("portal-operator-detail-description")

            with ui.element("div").classes("portal-operator-detail-hero-side"):
                ui.label("VISÃO GERAL").classes("portal-operator-detail-side-kicker")
                ui.label(
                    f"{str(total_info).zfill(2)} informações vinculadas"
                ).classes("portal-operator-detail-side-value")
                ui.label(
                    "Use as áreas abaixo para encontrar rapidamente o que precisa."
                ).classes("portal-operator-detail-side-copy")

        # Resumo útil: não são KPI; servem de contexto para a consulta.
        with ui.element("section").classes("portal-operator-summary-strip"):
            _detail_summary_item(
                "tag",
                "Código",
                operator.code or "Não informado",
                "Identificador interno",
            )
            _detail_summary_item(
                "view_list",
                "Planos",
                str(len(detail.planos)).zfill(2),
                "vinculados à operadora",
            )
            _detail_summary_item(
                "vpn_key",
                "Portais",
                str(len(detail.portais)).zfill(2),
                "acessos cadastrados",
            )
            _detail_summary_item(
                "contacts",
                "Contatos",
                str(len(detail.contatos)).zfill(2),
                "canais disponíveis",
            )

        with ui.element("section").classes("portal-operator-workspace"):
            with ui.row().classes("portal-operator-workspace-heading"):
                with ui.column().classes("portal-operator-workspace-heading-copy"):
                    ui.label("CENTRAL DA OPERADORA").classes("portal-section-kicker")
                    ui.label(
                        "Encontre tudo sem sair desta página"
                    ).classes("portal-operator-workspace-title")
                    ui.label(
                        "Navegue pelas categorias para acessar as informações "
                        "relacionadas ao atendimento."
                    ).classes("portal-operator-workspace-description")

            tabs = ui.tabs().classes("portal-hub-tabs").props(
                "dense align=left no-caps"
            )
            with tabs:
                t_planos = ui.tab("Planos", icon="view_list")
                t_portais = ui.tab("Portais", icon="vpn_key")
                t_eleg = ui.tab("Elegibilidade", icon="verified")
                t_auth = ui.tab("Autorizações", icon="fact_check")
                t_cob = ui.tab("Coberturas", icon="health_and_safety")
                t_docs = ui.tab("Documentos", icon="description")
                t_cont = ui.tab("Contatos", icon="contacts")
                t_more = ui.tab("Mais", icon="more_horiz")

            with ui.tab_panels(tabs, value=t_planos).classes("portal-hub-panels"):
                with ui.tab_panel(t_planos):
                    _render_planos(detail.planos)

                with ui.tab_panel(t_portais):
                    _render_portais(detail.portais)

                with ui.tab_panel(t_eleg):
                    _render_generic(
                        detail.elegibilidade,
                        ("orientacao", "codigo"),
                        [
                            ("Tipo de atendimento", ("tipo_atendimento",)),
                            ("Orientação", ("orientacao",)),
                            ("Observações", ("observacoes",)),
                            ("Status", ("status",)),
                        ],
                        "verified",
                        "Nenhuma orientação de elegibilidade cadastrada.",
                    )

                with ui.tab_panel(t_auth):
                    _render_generic(
                        detail.autorizacoes,
                        ("orientacao", "codigo"),
                        [
                            ("Momento", ("momento_autorizacao",)),
                            ("Quem solicita", ("quem_solicita",)),
                            ("Meio", ("meio_solicitacao",)),
                            ("Prazo", ("prazo",)),
                            ("Observações", ("observacoes",)),
                            ("Status", ("status",)),
                        ],
                        "fact_check",
                        "Nenhuma regra de autorização cadastrada.",
                    )

                with ui.tab_panel(t_cob):
                    _render_generic(
                        detail.coberturas,
                        ("restricoes_cobertura", "acomodacao", "codigo"),
                        [
                            ("Acomodação", ("acomodacao",)),
                            ("Acompanhante", ("acompanhante",)),
                            ("Restrições", ("restricoes_cobertura",)),
                            ("Observações", ("observacoes",)),
                            ("Status", ("status",)),
                        ],
                        "health_and_safety",
                        "Nenhuma informação de cobertura cadastrada.",
                    )

                with ui.tab_panel(t_docs):
                    _render_generic(
                        detail.documentos,
                        ("nome", "codigo"),
                        [
                            ("Formato", ("formato",)),
                            ("Orientação", ("orientacao",)),
                            ("Observações", ("observacoes",)),
                            ("Status", ("status",)),
                        ],
                        "description",
                        "Nenhum documento cadastrado.",
                    )

                with ui.tab_panel(t_cont):
                    _render_generic(
                        detail.contatos,
                        ("finalidade", "nome_setor", "contato"),
                        [
                            ("Setor", ("nome_setor",)),
                            ("Tipo", ("tipo",)),
                            ("Contato", ("contato",)),
                            ("Responsável", ("responsavel",)),
                            ("Horário", ("horario_atendimento",)),
                            ("Observações", ("observacoes",)),
                            ("Status", ("status",)),
                        ],
                        "contacts",
                        "Nenhum contato cadastrado.",
                    )

                with ui.tab_panel(t_more):
                    with ui.element("div").classes("portal-hub-more-grid"):
                        with ui.element("section").classes("portal-hub-more-section"):
                            ui.label("Contingências").classes("portal-hub-subtitle")
                            _render_generic(
                                detail.contingencias,
                                ("titulo", "codigo"),
                                [
                                    ("Descrição", ("descricao",)),
                                    ("Como proceder", ("orientacao_alternativa",)),
                                    ("Contato alternativo", ("contato_alternativo",)),
                                    ("Prioridade", ("prioridade",)),
                                    ("Status", ("status",)),
                                ],
                                "warning_amber",
                                "Nenhuma contingência cadastrada.",
                            )

                        with ui.element("section").classes("portal-hub-more-section"):
                            ui.label("Dicas operacionais").classes("portal-hub-subtitle")
                            _render_generic(
                                detail.dicas,
                                ("titulo", "dica", "orientacao"),
                                [
                                    ("Dica", ("dica", "orientacao", "descricao")),
                                    ("Status", ("status",)),
                                ],
                                "lightbulb",
                                "Nenhuma dica operacional cadastrada.",
                            )

                        with ui.element("section").classes("portal-hub-more-section"):
                            ui.label("Comunicados").classes("portal-hub-subtitle")
                            _render_generic(
                                detail.comunicados,
                                ("titulo", "assunto", "codigo"),
                                [
                                    ("Resumo", ("resumo", "conteudo", "descricao")),
                                    ("Status", ("status",)),
                                ],
                                "campaign",
                                "Nenhum comunicado cadastrado.",
                            )

                        with ui.element("section").classes("portal-hub-more-section"):
                            ui.label("Carteiras / consultoria").classes(
                                "portal-hub-subtitle"
                            )
                            _render_generic(
                                detail.carteiras,
                                ("consultor_nome", "papel", "codigo"),
                                [
                                    ("Papel", ("papel",)),
                                    ("Cargo", ("consultor_cargo",)),
                                    ("E-mail", ("consultor_email",)),
                                    ("Telefone", ("consultor_telefone",)),
                                    ("Observações", ("observacoes",)),
                                    ("Status", ("status",)),
                                ],
                                "support_agent",
                                "Nenhuma carteira vinculada.",
                            )

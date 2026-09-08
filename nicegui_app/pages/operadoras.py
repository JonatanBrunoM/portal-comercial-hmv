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
                operator.portal_name or "Portais e acessos",
                operator.portal_detail or "Nenhum portal ativo em destaque.",
            )
            _operator_feature(
                "description",
                operator.document_name or "Guias e documentos",
                operator.document_detail or "Nenhum documento ativo em destaque.",
            )
            _operator_feature(
                "contacts",
                operator.contact_name or "Contatos",
                operator.contact_value or "Nenhum contato ativo em destaque.",
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




def _compact_value(value: str, fallback: str = "Não informado") -> str:
    return value.strip() if value and value.strip() else fallback


def _first(rows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return rows[0] if rows else {}


def _quick_panel(
    *,
    icon: str,
    eyebrow: str,
    title: str,
    value: str,
    helper: str,
    action_label: str = "",
    action=None,
    tone: str = "",
) -> None:
    classes = "portal-operator-quick-panel"
    if tone:
        classes += f" is-{tone}"

    with ui.element("article").classes(classes):
        with ui.row().classes("portal-operator-quick-head"):
            with ui.element("div").classes("portal-operator-quick-icon"):
                ui.icon(icon)
            ui.label(eyebrow).classes("portal-operator-quick-eyebrow")

        ui.label(title).classes("portal-operator-quick-title")
        ui.label(value).classes("portal-operator-quick-value")
        ui.label(helper).classes("portal-operator-quick-helper")

        if action_label and action is not None:
            ui.button(
                action_label,
                icon="arrow_forward",
                on_click=action,
            ).props("flat no-caps").classes("portal-operator-quick-action")


def _rule_card(
    icon: str,
    title: str,
    rows: tuple[dict[str, Any], ...],
    fields: list[tuple[str, tuple[str, ...]]],
    empty_text: str,
) -> None:
    with ui.element("article").classes("portal-operator-rule-card"):
        with ui.row().classes("portal-operator-rule-head"):
            with ui.element("div").classes("portal-operator-rule-icon"):
                ui.icon(icon)
            with ui.column().classes("portal-operator-rule-head-copy"):
                ui.label(title).classes("portal-operator-rule-title")
                ui.label(
                    f"{len(rows)} registro{'s' if len(rows) != 1 else ''}"
                ).classes("portal-operator-rule-count")

        if not rows:
            ui.label(empty_text).classes("portal-operator-rule-empty")
            return

        row = rows[0]
        with ui.element("div").classes("portal-operator-rule-fields"):
            for label, keys in fields:
                value = _text(row, *keys)
                if value:
                    with ui.element("div").classes("portal-operator-rule-field"):
                        ui.label(label).classes("portal-operator-rule-label")
                        ui.label(value).classes("portal-operator-rule-value")

        if len(rows) > 1:
            ui.label(
                f"+ {len(rows) - 1} outro{'s' if len(rows) - 1 != 1 else ''} registro"
                f"{'s' if len(rows) - 1 != 1 else ''}"
            ).classes("portal-operator-rule-more")


def _resource_item(
    icon: str,
    title: str,
    subtitle: str,
    meta: str = "",
    action_label: str = "",
    action=None,
) -> None:
    with ui.element("article").classes("portal-operator-resource-item"):
        with ui.element("div").classes("portal-operator-resource-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-operator-resource-copy"):
            ui.label(title).classes("portal-operator-resource-title")
            if subtitle:
                ui.label(subtitle).classes("portal-operator-resource-subtitle")
            if meta:
                ui.label(meta).classes("portal-operator-resource-meta")
        if action_label and action is not None:
            ui.button(
                action_label,
                icon="arrow_forward",
                on_click=action,
            ).props("flat no-caps").classes("portal-operator-resource-action")


def _section_heading(kicker: str, title: str, description: str) -> None:
    with ui.column().classes("portal-operator-section-heading"):
        ui.label(kicker).classes("portal-section-kicker")
        ui.label(title).classes("portal-operator-section-title")
        ui.label(description).classes("portal-operator-section-description")


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

        first_portal = _first(detail.portais)
        first_contact = _first(detail.contatos)
        first_contingency = _first(detail.contingencias)
        first_communication = _first(detail.comunicados)

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

        # Breadcrumb / contextual actions.
        with ui.row().classes("portal-operator-cockpit-nav"):
            ui.button(
                "Todas as operadoras",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/operadoras"),
            ).props("flat no-caps").classes("portal-operator-cockpit-back")

            with ui.row().classes("portal-operator-cockpit-nav-actions"):
                if external_url:
                    ui.link(
                        "Site institucional",
                        target=external_url,
                        new_tab=True,
                    ).classes("portal-operator-cockpit-external")

                ui.button(
                    "Pesquisar nesta operadora",
                    icon="search",
                    on_click=lambda: _search_operator(operator.short_name),
                ).props("flat no-caps").classes("portal-operator-cockpit-search")

        # Compact identity header.
        with ui.element("section").classes("portal-operator-cockpit-hero"):
            with ui.element("div").classes("portal-operator-cockpit-mark"):
                _operator_mark(operator)

            with ui.column().classes("portal-operator-cockpit-copy"):
                with ui.row().classes("portal-operator-cockpit-meta"):
                    ui.label("CENTRAL DA OPERADORA").classes(
                        "portal-operator-cockpit-kicker"
                    )
                    with ui.element(
                        "span"
                    ).classes(
                        "portal-operator-status is-active"
                        if _is_active(operator.status)
                        else "portal-operator-status"
                    ):
                        ui.element("span").classes("portal-operator-status-dot")
                        ui.label(operator.status)

                ui.label(operator.short_name).classes("portal-operator-cockpit-title")
                ui.label(
                    operator.observations
                    or (
                        "Informações operacionais reunidas para apoiar o atendimento "
                        "sem precisar alternar entre diferentes fontes."
                    )
                ).classes("portal-operator-cockpit-description")

            with ui.element("div").classes("portal-operator-cockpit-context"):
                ui.label("VISÃO GERAL").classes("portal-operator-cockpit-context-kicker")
                ui.label(str(total_info).zfill(2)).classes(
                    "portal-operator-cockpit-context-value"
                )
                ui.label("informações vinculadas").classes(
                    "portal-operator-cockpit-context-label"
                )
                ui.label(operator.code or "Sem código").classes(
                    "portal-operator-cockpit-context-code"
                )

        # 1. What the user normally needs first.
        _section_heading(
            "COMECE POR AQUI",
            "O essencial para conduzir o atendimento",
            "Acesso, contato e qualquer situação operacional que mereça atenção imediata.",
        )

        with ui.element("section").classes("portal-operator-quick-grid"):
            portal_url = _safe_external_url(_text(first_portal, "url"))
            _quick_panel(
                icon="vpn_key",
                eyebrow="PORTAL PRINCIPAL",
                title=_text(first_portal, "nome") or "Nenhum portal em destaque",
                value=(
                    _text(first_portal, "instrucao_acesso")
                    or _text(first_portal, "dica_geral_acesso")
                    or "Consulte os acessos cadastrados para esta operadora."
                ),
                helper=(
                    ("Exige autenticação" if first_portal.get("exige_login") is True else "Acesso sem login informado")
                    if first_portal
                    else "Nenhum portal ativo cadastrado."
                ),
                action_label="Abrir portal" if portal_url else "",
                action=(lambda url=portal_url: ui.navigate.to(url, new_tab=True))
                if portal_url
                else None,
            )

            _quick_panel(
                icon="contacts",
                eyebrow="CONTATO RÁPIDO",
                title=(
                    _text(first_contact, "finalidade")
                    or _text(first_contact, "nome_setor")
                    or "Nenhum contato em destaque"
                ),
                value=_text(first_contact, "contato") or "Contato ainda não cadastrado.",
                helper=(
                    " · ".join(
                        item
                        for item in (
                            _text(first_contact, "responsavel"),
                            _text(first_contact, "horario_atendimento"),
                        )
                        if item
                    )
                    or "Consulte os demais canais disponíveis abaixo."
                ),
            )

            if first_contingency:
                _quick_panel(
                    icon="warning_amber",
                    eyebrow="ATENÇÃO AGORA",
                    title=_text(first_contingency, "titulo") or "Contingência ativa",
                    value=(
                        _text(first_contingency, "orientacao_alternativa")
                        or _text(first_contingency, "descricao")
                        or "Consulte a orientação cadastrada."
                    ),
                    helper=(
                        _text(first_contingency, "prioridade")
                        or _text(first_contingency, "status")
                    ),
                    tone="warning",
                )
            elif first_communication:
                _quick_panel(
                    icon="campaign",
                    eyebrow="ÚLTIMA ORIENTAÇÃO",
                    title=_text(first_communication, "titulo") or "Comunicado vigente",
                    value=(
                        _text(first_communication, "resumo")
                        or _text(first_communication, "conteudo")
                        or "Consulte o comunicado."
                    ),
                    helper=_text(first_communication, "prioridade") or "Publicado",
                    tone="information",
                )
            else:
                _quick_panel(
                    icon="verified",
                    eyebrow="OPERAÇÃO AGORA",
                    title="Sem alertas vigentes",
                    value="Nenhuma contingência ou comunicado prioritário está ativo.",
                    helper="Cenário operacional sem alerta cadastrado.",
                    tone="success",
                )

        # 2. Rules as questions, not database tables.
        with ui.element("section").classes("portal-operator-section-block"):
            _section_heading(
                "COMO ATENDER",
                "Regras que orientam a jornada",
                "As primeiras informações de elegibilidade, autorização e cobertura já ficam visíveis.",
            )

            with ui.element("div").classes("portal-operator-rule-grid"):
                _rule_card(
                    "verified",
                    "Elegibilidade",
                    detail.elegibilidade,
                    [
                        ("Orientação", ("orientacao",)),
                        ("Observação", ("observacoes",)),
                    ],
                    "Nenhuma orientação de elegibilidade cadastrada.",
                )
                _rule_card(
                    "fact_check",
                    "Autorização",
                    detail.autorizacoes,
                    [
                        ("Quando", ("momento_autorizacao",)),
                        ("Quem solicita", ("quem_solicita",)),
                        ("Canal", ("meio_solicitacao",)),
                        ("Prazo", ("prazo",)),
                    ],
                    "Nenhuma regra de autorização cadastrada.",
                )
                _rule_card(
                    "health_and_safety",
                    "Cobertura",
                    detail.coberturas,
                    [
                        ("Acomodação", ("acomodacao",)),
                        ("Acompanhante", ("acompanhante",)),
                        ("Restrições", ("restricoes_cobertura",)),
                    ],
                    "Nenhuma informação de cobertura cadastrada.",
                )

        # 3. Plans and documents visible in the same page.
        with ui.element("section").classes("portal-operator-section-block"):
            _section_heading(
                "REFERÊNCIAS",
                "Planos e documentos",
                "Materiais que ajudam a identificar o produto e preparar o atendimento.",
            )

            with ui.element("div").classes("portal-operator-reference-layout"):
                with ui.element("div").classes("portal-operator-reference-column"):
                    with ui.row().classes("portal-operator-reference-head"):
                        ui.label("PLANOS").classes("portal-operator-reference-kicker")
                        ui.label(str(len(detail.planos)).zfill(2)).classes(
                            "portal-operator-reference-count"
                        )

                    if detail.planos:
                        for row in detail.planos[:4]:
                            _resource_item(
                                "view_list",
                                _text(row, "nome_padronizado", "nome") or "Plano",
                                _text(row, "tipo_plano") or "Tipo não informado",
                                (
                                    f"Código: {_text(row, 'codigo')}"
                                    if _text(row, "codigo")
                                    else ""
                                ),
                            )
                    else:
                        ui.label("Nenhum plano cadastrado.").classes(
                            "portal-operator-reference-empty"
                        )

                with ui.element("div").classes("portal-operator-reference-column"):
                    with ui.row().classes("portal-operator-reference-head"):
                        ui.label("DOCUMENTOS").classes("portal-operator-reference-kicker")
                        ui.label(str(len(detail.documentos)).zfill(2)).classes(
                            "portal-operator-reference-count"
                        )

                    if detail.documentos:
                        for row in detail.documentos[:4]:
                            file_url = _safe_external_url(_text(row, "arquivo_url"))
                            meta = " · ".join(
                                item
                                for item in (
                                    "Obrigatório" if row.get("obrigatorio") is True else "",
                                    _text(row, "formato"),
                                )
                                if item
                            )
                            _resource_item(
                                "description",
                                _text(row, "nome") or "Documento",
                                _text(row, "orientacao") or "Referência cadastrada.",
                                meta,
                                "Abrir arquivo" if file_url else "",
                                (
                                    lambda url=file_url: ui.navigate.to(url, new_tab=True)
                                    if url
                                    else None
                                )
                                if file_url
                                else None,
                            )
                    else:
                        ui.label("Nenhum documento cadastrado.").classes(
                            "portal-operator-reference-empty"
                        )

        # 4. Secondary information via native Quasar expansion panels.
        with ui.element("section").classes("portal-operator-section-block"):
            _section_heading(
                "OUTRAS INFORMAÇÕES",
                "Consulte quando precisar aprofundar",
                "Contatos adicionais, dicas, comunicados, contingências e consultoria ficam disponíveis sem sair da operadora.",
            )

            with ui.element("div").classes("portal-operator-expansion-list"):
                with ui.expansion(
                    "Contatos adicionais",
                    icon="contacts",
                    value=False,
                ).classes("portal-operator-expansion"):
                    if detail.contatos:
                        with ui.element("div").classes("portal-operator-expansion-content"):
                            for row in detail.contatos:
                                _resource_item(
                                    "phone",
                                    (
                                        _text(row, "finalidade")
                                        or _text(row, "nome_setor")
                                        or "Contato"
                                    ),
                                    _text(row, "contato"),
                                    " · ".join(
                                        item
                                        for item in (
                                            _text(row, "responsavel"),
                                            _text(row, "horario_atendimento"),
                                        )
                                        if item
                                    ),
                                )
                    else:
                        ui.label("Nenhum contato adicional cadastrado.")

                with ui.expansion(
                    "Dicas e orientações",
                    icon="lightbulb",
                    value=False,
                ).classes("portal-operator-expansion"):
                    if detail.dicas:
                        with ui.element("div").classes("portal-operator-expansion-content"):
                            for row in detail.dicas:
                                _resource_item(
                                    "lightbulb",
                                    _text(row, "titulo") or "Dica operacional",
                                    _text(row, "dica", "orientacao", "descricao"),
                                    _text(row, "categoria"),
                                )
                    else:
                        ui.label("Nenhuma dica operacional cadastrada.")

                with ui.expansion(
                    "Comunicados e contingências",
                    icon="campaign",
                    value=False,
                ).classes("portal-operator-expansion"):
                    with ui.element("div").classes("portal-operator-expansion-content"):
                        for row in detail.comunicados:
                            _resource_item(
                                "campaign",
                                _text(row, "titulo") or "Comunicado",
                                _text(row, "resumo", "conteudo"),
                                _text(row, "prioridade"),
                            )
                        for row in detail.contingencias:
                            _resource_item(
                                "warning_amber",
                                _text(row, "titulo") or "Contingência",
                                (
                                    _text(row, "orientacao_alternativa")
                                    or _text(row, "descricao")
                                ),
                                _text(row, "prioridade"),
                            )
                        if not detail.comunicados and not detail.contingencias:
                            ui.label("Nenhum comunicado ou contingência vigente.")

                with ui.expansion(
                    "Consultoria e carteiras",
                    icon="support_agent",
                    value=False,
                ).classes("portal-operator-expansion"):
                    if detail.carteiras:
                        with ui.element("div").classes("portal-operator-expansion-content"):
                            for row in detail.carteiras:
                                _resource_item(
                                    "support_agent",
                                    _text(row, "consultor_nome") or "Consultor",
                                    _text(row, "papel", "consultor_cargo"),
                                    " · ".join(
                                        item
                                        for item in (
                                            _text(row, "consultor_email"),
                                            _text(row, "consultor_telefone"),
                                        )
                                        if item
                                    ),
                                )
                    else:
                        ui.label("Nenhuma carteira vinculada.")


def _search_operator(operator_name: str) -> None:
    ui.context.client.storage["portal_pending_search_query"] = operator_name
    ui.navigate.to("/pesquisa")

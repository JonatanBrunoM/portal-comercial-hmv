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
    initials = "".join(word[0] for word in operator.short_name.split() if word)[:2].upper() or "OP"
    ui.label(initials).classes("portal-operator-initials")


def _operator_card(operator: OperadoraPreview) -> None:
    with ui.element("article").classes("portal-operator-card"):
        with ui.row().classes("portal-operator-card-top"):
            with ui.element("div").classes("portal-operator-mark"):
                _operator_mark(operator)
            with ui.element("div").classes(
                "portal-operator-status is-active" if _is_active(operator.status)
                else "portal-operator-status"
            ):
                ui.element("span").classes("portal-operator-status-dot")
                ui.label(operator.status)

        with ui.column().classes("portal-operator-card-copy"):
            ui.label(operator.short_name).classes("portal-operator-card-title")
            if operator.name != operator.short_name:
                ui.label(operator.name).classes("portal-operator-card-name")
            if operator.code:
                ui.label(f"Código {operator.code}").classes("portal-operator-card-code")
            ui.label(
                operator.observations
                or "Consulte planos, portais, orientações e informações vinculadas."
            ).classes("portal-operator-card-description")

        with ui.row().classes("portal-operator-card-footer"):
            ui.button(
                "Abrir operadora",
                icon="arrow_forward",
                on_click=lambda oid=operator.operator_id: ui.navigate.to(f"/operadoras/{oid}"),
            ).props("flat no-caps").classes("portal-operator-open-button")


def render_operadoras(user: dict) -> None:
    operators = get_operadoras_preview()
    with portal_layout(
        user=user,
        active="operators",
        page_eyebrow="CENTRAL DE OPERADORAS",
        page_title="Encontre a operadora. Acesse a informação.",
        page_description="Consulte a base institucional de operadoras e avance para todas as informações relacionadas.",
    ):
        active_count = sum(1 for op in operators if _is_active(op.status))
        with ui.element("section").classes("portal-operators-summary"):
            with ui.element("div").classes("portal-operators-summary-main"):
                ui.label("BASE ATUAL").classes("portal-section-kicker")
                ui.label(f"{len(operators):02d} operadoras cadastradas").classes("portal-operators-summary-value")
                ui.label("Dados carregados diretamente do Supabase.").classes("portal-operators-summary-description")
            with ui.row().classes("portal-operators-summary-stats"):
                for value, label in ((active_count, "Ativas"), (len(operators)-active_count, "Outros status")):
                    with ui.column().classes("portal-operators-mini-stat"):
                        ui.label(str(value).zfill(2)).classes("portal-operators-mini-value")
                        ui.label(label).classes("portal-operators-mini-label")

        with ui.element("section").classes("portal-operators-toolbar"):
            search = ui.input(placeholder="Buscar por nome, nome curto ou código").props(
                "outlined dense clearable prepend-icon=search"
            ).classes("portal-operators-search")
            status = ui.select(
                options=["Todos", "Ativo", "Outros"], value="Todos", label="Status"
            ).props("outlined dense").classes("portal-operators-filter")

        results_label = ui.label("").classes("portal-operators-result-label")
        cards = ui.element("div").classes("portal-operators-grid")

        def refresh_cards() -> None:
            term = _normalized(search.value or "")
            selected = status.value or "Todos"
            filtered = []
            for operator in operators:
                haystack = _normalized(" ".join((operator.name, operator.short_name, operator.code)))
                status_ok = (
                    selected == "Todos"
                    or (selected == "Ativo" and _is_active(operator.status))
                    or (selected == "Outros" and not _is_active(operator.status))
                )
                if (not term or term in haystack) and status_ok:
                    filtered.append(operator)
            results_label.set_text(f"{len(filtered)} operadora(s) encontrada(s)")
            cards.clear()
            with cards:
                if not filtered:
                    _empty("Nenhuma operadora encontrada.", "Revise a busca ou altere o filtro de status.", "search_off")
                else:
                    for operator in filtered:
                        _operator_card(operator)

        search.on_value_change(lambda _: refresh_cards())
        status.on_value_change(lambda _: refresh_cards())
        refresh_cards()


def _empty(title: str, description: str, icon: str = "inventory_2") -> None:
    with ui.element("div").classes("portal-operators-empty"):
        ui.icon(icon)
        ui.label(title).classes("portal-operators-empty-title")
        ui.label(description).classes("portal-operators-empty-description")


def _detail_metric(icon: str, label: str, value: str) -> None:
    with ui.element("div").classes("portal-operator-detail-metric"):
        ui.icon(icon)
        with ui.column().classes("portal-operator-detail-metric-copy"):
            ui.label(label).classes("portal-operator-detail-metric-label")
            ui.label(value).classes("portal-operator-detail-metric-value")


def _info_row(title: str, lines: list[tuple[str, str]], icon: str = "article") -> None:
    with ui.element("article").classes("portal-hub-row"):
        with ui.element("div").classes("portal-hub-row-icon"):
            ui.icon(icon)
        with ui.column().classes("portal-hub-row-copy"):
            ui.label(title).classes("portal-hub-row-title")
            for label, value in lines:
                if value:
                    ui.label(f"{label}: {value}").classes("portal-hub-row-line")


def _render_planos(rows: tuple[dict[str, Any], ...]) -> None:
    if not rows:
        _empty("Nenhum plano cadastrado.", "Ainda não há planos vinculados.")
        return
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
        _empty("Nenhum portal cadastrado.", "Ainda não há portais vinculados.", "vpn_key")
        return
    for row in rows:
        with ui.element("article").classes("portal-hub-row"):
            with ui.element("div").classes("portal-hub-row-icon"):
                ui.icon("vpn_key")
            with ui.column().classes("portal-hub-row-copy"):
                ui.label(_text(row, "nome") or "Portal").classes("portal-hub-row-title")
                for label, value in [
                    ("Tipo", _text(row, "tipo")),
                    ("Instrução", _text(row, "instrucao_acesso")),
                    ("Dica", _text(row, "dica_geral_acesso")),
                    ("Observações", _text(row, "observacoes")),
                    ("Status", _text(row, "status")),
                ]:
                    if value:
                        ui.label(f"{label}: {value}").classes("portal-hub-row-line")
            url = _safe_external_url(_text(row, "url"))
            if url:
                ui.link("Abrir portal", target=url, new_tab=True).classes("portal-operator-site-link")


def _render_generic(rows, title_keys, fields, icon, empty_title):
    if not rows:
        _empty(empty_title, "Nenhum registro vinculado a esta operadora.", icon)
        return
    for row in rows:
        title = _text(row, *title_keys) or "Informação cadastrada"
        lines = [(label, _text(row, *keys)) for label, keys in fields]
        _info_row(title, lines, icon)


def render_operadora_detail(user: dict, operator_id: str) -> None:
    detail = get_operadora_detail(operator_id)

    with portal_layout(user=user, active="operators"):
        if detail is None:
            _empty("Operadora não encontrada.", "O registro pode ter sido removido.", "domain_disabled")
            return

        operator = detail.operator
        external_url = _safe_external_url(operator.site_url)

        ui.button(
            "Voltar para Operadoras",
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/operadoras"),
        ).props("flat no-caps").classes("portal-operator-back-button")

        with ui.element("section").classes("portal-operator-detail-hero"):
            with ui.element("div").classes("portal-operator-detail-mark"):
                _operator_mark(operator)
            with ui.column().classes("portal-operator-detail-copy"):
                with ui.row().classes("portal-operator-detail-meta"):
                    ui.label("FICHA DA OPERADORA").classes("portal-section-kicker")
                    with ui.element("div").classes(
                        "portal-operator-status is-active" if _is_active(operator.status)
                        else "portal-operator-status"
                    ):
                        ui.element("span").classes("portal-operator-status-dot")
                        ui.label(operator.status)
                ui.label(operator.short_name).classes("portal-operator-detail-title")
                if operator.name != operator.short_name:
                    ui.label(operator.name).classes("portal-operator-detail-full-name")
                ui.label(
                    operator.observations or "Informações institucionais vinculadas a esta operadora."
                ).classes("portal-operator-detail-description")
            if external_url:
                ui.link("Abrir site", target=external_url, new_tab=True).classes("portal-operator-site-link")

        total_info = sum(len(rows) for rows in (
            detail.planos, detail.portais, detail.elegibilidade, detail.documentos,
            detail.autorizacoes, detail.coberturas, detail.contatos,
            detail.contingencias, detail.dicas, detail.comunicados, detail.carteiras,
        ))

        with ui.element("section").classes("portal-operator-detail-metrics"):
            _detail_metric("tag", "Código", operator.code or "Não informado")
            _detail_metric("view_list", "Planos", str(len(detail.planos)).zfill(2))
            _detail_metric("hub", "Informações vinculadas", str(total_info).zfill(2))

        ui.label("CENTRAL DA OPERADORA").classes("portal-section-kicker portal-hub-kicker")
        ui.label("Todas as informações em um só lugar").classes("portal-section-title")

        tabs = ui.tabs().classes("portal-hub-tabs").props("dense align=left")
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
                            ("titulo", "orientacao", "codigo"),
                            [("Orientação", ("orientacao", "descricao")), ("Observações", ("observacoes",)), ("Status", ("status",))],
                            "warning_amber",
                            "Nenhuma contingência cadastrada.",
                        )
                    with ui.element("section").classes("portal-hub-more-section"):
                        ui.label("Dicas operacionais").classes("portal-hub-subtitle")
                        _render_generic(
                            detail.dicas,
                            ("titulo", "dica", "orientacao"),
                            [("Dica", ("dica", "orientacao", "descricao")), ("Status", ("status",))],
                            "lightbulb",
                            "Nenhuma dica operacional cadastrada.",
                        )
                    with ui.element("section").classes("portal-hub-more-section"):
                        ui.label("Comunicados").classes("portal-hub-subtitle")
                        _render_generic(
                            detail.comunicados,
                            ("titulo", "assunto", "codigo"),
                            [("Resumo", ("resumo", "conteudo", "descricao")), ("Status", ("status",))],
                            "campaign",
                            "Nenhum comunicado cadastrado.",
                        )
                    with ui.element("section").classes("portal-hub-more-section"):
                        ui.label("Carteiras / consultoria").classes("portal-hub-subtitle")
                        _render_generic(
                            detail.carteiras,
                            ("nome", "codigo"),
                            [("Observações", ("observacoes",)), ("Status", ("status",))],
                            "support_agent",
                            "Nenhuma carteira vinculada.",
                        )

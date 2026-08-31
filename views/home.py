import html

import streamlit as st

from components.cards import render_module_card
from components.search_results import render_search_results
from components.sidebar import navigate_to
from core.dashboard_service import get_dashboard_summary
from core.search_service import search_global


def _safe(value) -> str:
    return html.escape(str(value or ""))


def _priority_icon(priority: str) -> str:
    normalized = (priority or "").strip().casefold()
    return {
        "alta": "🔴",
        "média": "🟠",
        "media": "🟠",
        "baixa": "🔵",
        "crítica": "🔴",
        "critica": "🔴",
    }.get(normalized, "📌")


def _section_header(eyebrow: str, title: str, description: str = "") -> None:
    description_html = (
        f'<div class="portal-home-section-description">{_safe(description)}</div>'
        if description
        else ""
    )
    st.html(
        f"""
        <div class="portal-home-section-head">
            <div class="portal-home-section-eyebrow">{_safe(eyebrow)}</div>
            <div class="portal-home-section-title">{_safe(title)}</div>
            {description_html}
        </div>
        """
    )


def _render_status_strip(summary) -> None:
    comunicados = summary.comunicados if summary else "—"
    contingencias = summary.contingencias if summary else "—"
    operadoras = summary.operadoras if summary else "—"
    planos = summary.planos if summary else "—"

    st.html(
        f"""
        <div class="portal-home-status-strip">
            <div class="portal-home-status-item">
                <div class="portal-home-status-value">{_safe(operadoras)}</div>
                <div class="portal-home-status-label">Operadoras ativas</div>
            </div>
            <div class="portal-home-status-item">
                <div class="portal-home-status-value">{_safe(planos)}</div>
                <div class="portal-home-status-label">Planos cadastrados</div>
            </div>
            <div class="portal-home-status-item">
                <div class="portal-home-status-value">{_safe(comunicados)}</div>
                <div class="portal-home-status-label">Comunicados ativos</div>
            </div>
            <div class="portal-home-status-item">
                <div class="portal-home-status-value">{_safe(contingencias)}</div>
                <div class="portal-home-status-label">Contingências ativas</div>
            </div>
        </div>
        """
    )


def _render_notice_card(notice) -> None:
    period = notice.start_date or ""
    if notice.end_date:
        period = (
            f"{period} até {notice.end_date}"
            if period
            else f"Até {notice.end_date}"
        )

    body = (
        f'<div class="portal-home-notice-body">{_safe(notice.summary)}</div>'
        if notice.summary
        else ""
    )

    st.html(
        f"""
        <article class="portal-home-notice">
            <div class="portal-home-notice-title">
                {_priority_icon(notice.priority)} {_safe(notice.title)}
            </div>
            <div class="portal-home-notice-meta">
                {_safe(notice.category)} · {_safe(notice.operator_name)}
            </div>
            {body}
            <div class="portal-home-notice-footer">
                <span><strong>Prioridade:</strong> {_safe(notice.priority)}</span>
                <span><strong>Vigência:</strong> {_safe(period or "Não informada")}</span>
            </div>
        </article>
        """
    )


def _render_contingency_card(item) -> None:
    guidance = (
        f'<div class="portal-home-notice-body"><strong>Orientação:</strong> {_safe(item.guidance)}</div>'
        if item.guidance
        else ""
    )
    st.html(
        f"""
        <article class="portal-home-notice">
            <div class="portal-home-notice-title">
                {_priority_icon(item.priority)} {_safe(item.event)}
            </div>
            <div class="portal-home-notice-meta">
                {_safe(item.operator_name)} · {_safe(item.unit)}
            </div>
            {guidance}
            <div class="portal-home-notice-footer">
                <span><strong>Prioridade:</strong> {_safe(item.priority)}</span>
                <span><strong>Status:</strong> {_safe(item.status)}</span>
            </div>
        </article>
        """
    )


def _render_quick_access() -> None:
    _section_header(
        "Navegue pelo portal",
        "Acessos rápidos",
        "Entre diretamente nas informações mais consultadas pela operação.",
    )

    row_1 = st.columns(3)
    modules = [
        (
            row_1[0],
            "Operadoras",
            "Planos, coberturas, regras, documentos e informações por convênio.",
            "🏥",
            "home_operadoras",
            "Operadoras",
        ),
        (
            row_1[1],
            "Portais",
            "Acessos utilizados para elegibilidade, autorização e operação.",
            "🌐",
            "home_portais",
            "Portais",
        ),
        (
            row_1[2],
            "Documentos",
            "Documentos obrigatórios, validade e orientações de atendimento.",
            "📄",
            "home_documentos",
            "Documentos",
        ),
    ]

    for column, title, description, icon, key, page in modules:
        with column:
            if render_module_card(
                title=title,
                description=description,
                icon=icon,
                button_key=key,
            ):
                navigate_to(page)
                st.rerun()

    row_2 = st.columns(3)
    modules_2 = [
        (
            row_2[0],
            "Contatos",
            "Telefones, e-mails, centrais e responsáveis das operadoras.",
            "📞",
            "home_contatos",
            "Contatos",
        ),
        (
            row_2[1],
            "Contingências",
            "Indisponibilidades atuais e fluxos alternativos para a operação.",
            "⚠️",
            "home_contingencias",
            "Contingências",
        ),
        (
            row_2[2],
            "Comunicados",
            "Mudanças, avisos e orientações relevantes para as equipes.",
            "📢",
            "home_comunicados",
            "Comunicados",
        ),
    ]

    for column, title, description, icon, key, page in modules_2:
        with column:
            if render_module_card(
                title=title,
                description=description,
                icon=icon,
                button_key=key,
            ):
                navigate_to(page)
                st.rerun()


def render_home() -> None:
    """Renderiza a Home como hall de entrada do Portal Comercial."""

    try:
        summary = get_dashboard_summary()
        data_error = False
    except RuntimeError:
        summary = None
        data_error = True

    st.html(
        """
        <section class="portal-home-hero">
            <div class="portal-home-kicker">Hospital Moinhos de Vento · Comercial</div>
            <h1 class="portal-home-title">Informação certa para cada atendimento.</h1>
            <p class="portal-home-description">
                Um único ponto de consulta para operadoras, planos, portais,
                documentos, contatos, regras e orientações da operação comercial.
            </p>
            <div class="portal-home-badge">● Base institucional de consulta</div>
        </section>
        """
    )

    st.html(
        """
        <div class="portal-home-search-intro">
            <div class="portal-home-search-title">O que você precisa consultar?</div>
            <div class="portal-home-search-subtitle">
                Pesquise agora na base comercial. No futuro, este será também o ponto de conversa com o agente do Portal.
            </div>
        </div>
        """
    )

    search_query = st.text_input(
        label="Pesquisa global",
        placeholder="Pergunte ou pesquise por operadora, plano, documento, portal, contato ou orientação...",
        label_visibility="collapsed",
        key="home_search",
    )

    if data_error:
        st.warning(
            "Não foi possível carregar todos os indicadores da página inicial. "
            "As demais áreas do portal continuam disponíveis."
        )

    if search_query:
        with st.spinner("Consultando a base comercial..."):
            search_results = search_global(
                query=search_query,
                limit=12,
            )

        render_search_results(
            results=search_results,
            key_prefix="home_search",
        )
        st.divider()

    _render_status_strip(summary)

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        _section_header(
            "Atualizações",
            "Comunicados importantes",
            "Mudanças e orientações que merecem atenção da equipe.",
        )

        if summary and summary.notices:
            for notice in summary.notices[:3]:
                _render_notice_card(notice)
        else:
            st.info("Nenhum comunicado ativo neste momento.")

        if st.button(
            "Ver todos os comunicados →",
            key="home_all_notices",
        ):
            navigate_to("Comunicados")
            st.rerun()

    with right:
        _section_header(
            "Operação",
            "Contingências",
            "Situações ativas e caminhos alternativos para manter o atendimento.",
        )

        if summary and summary.contingency_items:
            for item in summary.contingency_items[:3]:
                _render_contingency_card(item)
        else:
            st.success("Nenhuma contingência ativa neste momento.")

        if st.button(
            "Ver todas as contingências →",
            key="home_all_contingencies",
        ):
            navigate_to("Contingências")
            st.rerun()

    _render_quick_access()

import html

import streamlit as st

from components.sidebar import navigate_to
from components.search_results import render_search_results
from core.dashboard_service import get_dashboard_summary
from core.search_service import search_global


def _safe(value) -> str:
    return html.escape(str(value or ""))


def _priority_icon(priority: str) -> str:
    normalized = (priority or "").strip().casefold()
    return {
        "alta": "●",
        "média": "●",
        "media": "●",
        "baixa": "●",
        "crítica": "●",
        "critica": "●",
    }.get(normalized, "●")


def _section_header(kicker: str, title: str, description: str = "") -> None:
    description_html = (
        f'<div class="portal-home-section-description">{_safe(description)}</div>'
        if description
        else ""
    )

    st.html(
        f"""
        <div class="portal-home-section-head">
            <div class="portal-home-section-eyebrow">{_safe(kicker)}</div>
            <div class="portal-home-section-title">{_safe(title)}</div>
            {description_html}
        </div>
        """
    )


def _go(page: str) -> None:
    navigate_to(page)


def _render_hero(summary) -> None:
    operators = summary.operadoras if summary else "—"
    plans = summary.planos if summary else "—"
    notices = summary.comunicados if summary else "—"
    contingencies = summary.contingencias if summary else "—"

    st.html(
        f"""
        <section class="portal-home-hero portal-home-hero-v3">
            <div class="portal-home-hero-copy">
                <div class="portal-home-kicker">HOSPITAL MOINHOS DE VENTO · COMERCIAL</div>
                <h1 class="portal-home-title">
                    Tudo que a operação precisa,
                    <span>em um único lugar.</span>
                </h1>
                <p class="portal-home-description">
                    Consulte convênios com rapidez, encontre o caminho correto
                    para cada atendimento e reduza dúvidas no dia a dia.
                </p>
                <div class="portal-home-hero-tags">
                    <span>Planos</span>
                    <span>Portais</span>
                    <span>Autorizações</span>
                    <span>Documentos</span>
                    <span>Contatos</span>
                </div>
            </div>

            <div class="portal-home-pulse">
                <div class="portal-home-pulse-label">VISÃO DA BASE</div>
                <div class="portal-home-pulse-main">
                    <div>
                        <strong>{_safe(operators)}</strong>
                        <span>operadoras</span>
                    </div>
                    <div>
                        <strong>{_safe(plans)}</strong>
                        <span>planos</span>
                    </div>
                </div>
                <div class="portal-home-pulse-row">
                    <span><b>{_safe(notices)}</b> comunicados ativos</span>
                    <span><b>{_safe(contingencies)}</b> contingências</span>
                </div>
                <div class="portal-home-pulse-foot">
                    Base institucional de consulta comercial
                </div>
            </div>
        </section>
        """
    )


def _render_search() -> str:
    st.html(
        """
        <div class="portal-command-heading">
            <div class="portal-command-eyebrow">CENTRAL DE CONSULTA</div>
            <div class="portal-command-title">Como podemos ajudar?</div>
            <div class="portal-command-subtitle">
                Pesquise na base agora. Este espaço será a interface principal
                do agente do Portal Comercial.
            </div>
        </div>
        """
    )

    return st.text_input(
        label="Pesquisa global",
        placeholder="Ex.: Como faço a autorização do plano? Qual o telefone da operadora? Onde acesso o portal?",
        label_visibility="collapsed",
        key="home_search",
    )


def _render_quick_dock() -> None:
    with st.container(key="home_quick_actions"):
        st.html('<div class="portal-home-dock-label">ATALHOS RÁPIDOS</div>')

        columns = st.columns(5, gap="small")
        actions = [
            ("🏥", "Operadoras", "Operadoras"),
            ("🌐", "Portais", "Portais"),
            ("📄", "Documentos", "Documentos"),
            ("☎️", "Contatos", "Contatos"),
            ("⚠️", "Contingências", "Contingências"),
        ]

        for column, (icon, label, page) in zip(columns, actions):
            with column:
                if st.button(
                    f"{icon}  {label}",
                    key=f"home_dock_{page}",
                    use_container_width=True,
                ):
                    _go(page)
                    st.rerun()


def _notice_html(notice, compact: bool = False) -> str:
    period = notice.start_date or ""
    if notice.end_date:
        period = f"{period} até {notice.end_date}" if period else f"Até {notice.end_date}"

    compact_class = " portal-feed-card-compact" if compact else ""

    return f"""
    <article class="portal-feed-card{compact_class}">
        <div class="portal-feed-topline">
            <span class="portal-feed-dot portal-feed-dot-notice"></span>
            <span>COMUNICADO</span>
            <span class="portal-feed-priority">{_safe(notice.priority)}</span>
        </div>
        <div class="portal-feed-title">{_safe(notice.title)}</div>
        <div class="portal-feed-meta">
            {_safe(notice.operator_name)} · {_safe(notice.category)}
        </div>
        <div class="portal-feed-body">{_safe(notice.summary)}</div>
        <div class="portal-feed-footer">
            <span>{_safe(period or "Vigência não informada")}</span>
        </div>
    </article>
    """


def _contingency_html(item, featured: bool = False) -> str:
    feature_class = " portal-feed-card-featured" if featured else ""

    return f"""
    <article class="portal-feed-card portal-feed-card-alert{feature_class}">
        <div class="portal-feed-topline">
            <span class="portal-feed-dot portal-feed-dot-alert"></span>
            <span>CONTINGÊNCIA</span>
            <span class="portal-feed-priority">{_safe(item.priority)}</span>
        </div>
        <div class="portal-feed-title">{_safe(item.event)}</div>
        <div class="portal-feed-meta">
            {_safe(item.operator_name)} · {_safe(item.unit)}
        </div>
        <div class="portal-feed-body">{_safe(item.guidance)}</div>
        <div class="portal-feed-footer">
            <span>Status: {_safe(item.status)}</span>
        </div>
    </article>
    """


def _render_radar(summary) -> None:
    _section_header(
        "AGORA NO PORTAL",
        "Radar operacional",
        "O que merece atenção antes de iniciar um atendimento.",
    )

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        if summary and summary.contingency_items:
            st.html(
                _contingency_html(
                    summary.contingency_items[0],
                    featured=True,
                )
            )

            for item in summary.contingency_items[1:3]:
                st.html(_contingency_html(item))
        else:
            st.html(
                """
                <div class="portal-empty-state">
                    <div class="portal-empty-icon">✓</div>
                    <div>
                        <strong>Operação sem contingências ativas</strong>
                        <span>Nenhum fluxo alternativo precisa de atenção agora.</span>
                    </div>
                </div>
                """
            )

        if st.button(
            "Ver todas as contingências  →",
            key="home_all_contingencies",
        ):
            _go("Contingências")
            st.rerun()

    with right:
        if summary and summary.notices:
            for notice in summary.notices[:3]:
                st.html(_notice_html(notice, compact=True))
        else:
            st.html(
                """
                <div class="portal-empty-state">
                    <div class="portal-empty-icon">✓</div>
                    <div>
                        <strong>Sem novos comunicados</strong>
                        <span>Não há atualizações publicadas para este momento.</span>
                    </div>
                </div>
                """
            )

        if st.button(
            "Ver todos os comunicados  →",
            key="home_all_notices",
        ):
            _go("Comunicados")
            st.rerun()


def _render_explore() -> None:
    _section_header(
        "EXPLORE",
        "Encontre pelo assunto",
        "Entre pelo caminho que melhor representa a sua necessidade.",
    )

    rows = [
        [
            ("🏥", "Operadoras e planos", "Consulte o panorama completo de cada convênio.", "Operadoras"),
            ("🌐", "Portais e acessos", "Encontre os sistemas utilizados na operação.", "Portais"),
            ("📄", "Documentação", "Confira documentos, validade e orientações.", "Documentos"),
        ],
        [
            ("☎", "Contatos", "Localize centrais, e-mails e responsáveis.", "Contatos"),
            ("👥", "Relacionamento", "Consulte consultores e carteiras.", "Consultores"),
            ("📢", "Atualizações", "Veja comunicados e mudanças recentes.", "Comunicados"),
        ],
    ]

    for row_index, items in enumerate(rows):
        columns = st.columns(3, gap="medium")
        for column, (icon, title, description, page) in zip(columns, items):
            with column:
                st.html(
                    f"""
                    <div class="portal-explore-card">
                        <div class="portal-explore-icon">{_safe(icon)}</div>
                        <div class="portal-explore-title">{_safe(title)}</div>
                        <div class="portal-explore-description">{_safe(description)}</div>
                    </div>
                    """
                )
                if st.button(
                    f"Acessar {title}  →",
                    key=f"home_explore_{row_index}_{page}",
                    use_container_width=True,
                ):
                    _go(page)
                    st.rerun()


def render_home() -> None:
    """Renderiza a Home como hall institucional e operacional."""

    try:
        summary = get_dashboard_summary()
        data_error = False
    except RuntimeError:
        summary = None
        data_error = True

    _render_hero(summary)

    search_query = _render_search()
    _render_quick_dock()

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

    _render_radar(summary)
    _render_explore()

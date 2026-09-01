from html import escape as html_escape

import streamlit as st

from components.search_results import render_search_results
from core.dashboard_service import get_dashboard_summary
from core.search_service import analyze_search_query, search_global
from ui.icons import icon


def _safe(value) -> str:
    return html_escape(str(value or ""))


def _nav_href(page: str) -> str:
    slugs = {
        "Início": "inicio",
        "Pesquisa": "pesquisa",
        "Operadoras": "operadoras",
        "Portais": "portais",
        "Documentos": "documentos",
        "Contatos": "contatos",
        "Consultores": "consultores",
        "Comunicados": "comunicados",
        "Contingências": "contingencias",
        "Administração": "administracao",
    }
    return f"?page={slugs.get(page, 'inicio')}"


def _render_hero(summary) -> None:
    operators = summary.operadoras if summary else "—"
    plans = summary.planos if summary else "—"
    notices = summary.comunicados if summary else "—"
    contingencies = summary.contingencias if summary else "—"

    st.html(
        f"""
        <section class="home-hero">
            <div class="home-hero-grid">
                <div class="home-hero-copy">
                    <div class="home-kicker">
                        HOSPITAL MOINHOS DE VENTO · COMERCIAL
                    </div>

                    <h1 class="home-title">
                        O ponto de partida
                        <span>da operação comercial.</span>
                    </h1>

                    <p class="home-description">
                        Encontre rapidamente a informação certa sobre convênios,
                        planos, acessos, regras, documentos e contatos para cada atendimento.
                    </p>

                    <div class="home-hero-context">
                        <span>Base institucional</span>
                        <span>Consulta rápida</span>
                        <span>Informação centralizada</span>
                    </div>
                </div>

                <div class="home-hero-status">
                    <div class="home-status-header">
                        <div>
                            <span class="home-status-eyebrow">BASE COMERCIAL</span>
                            <strong>Visão rápida</strong>
                        </div>
                        <span class="home-status-live">
                            <i></i> Atualizada
                        </span>
                    </div>

                    <div class="home-status-grid">
                        <div class="home-status-metric">
                            <strong>{_safe(operators)}</strong>
                            <span>Operadoras</span>
                        </div>
                        <div class="home-status-metric">
                            <strong>{_safe(plans)}</strong>
                            <span>Planos</span>
                        </div>
                        <div class="home-status-metric">
                            <strong>{_safe(notices)}</strong>
                            <span>Comunicados</span>
                        </div>
                        <div class="home-status-metric">
                            <strong>{_safe(contingencies)}</strong>
                            <span>Contingências</span>
                        </div>
                    </div>

                    <div class="home-status-foot">
                        Um único lugar para consultar a operação.
                    </div>
                </div>
            </div>
        </section>
        """
    )


def _render_search() -> str:
    st.html(
        f"""
        <div class="home-command-card">
            <div class="home-command-icon">
                {icon("search")}
            </div>
            <div class="home-command-copy">
                <span>ENCONTRE O QUE PRECISA</span>
                <strong>Como podemos ajudar?</strong>
                <small>
                    Digite uma dúvida, operadora, plano, documento, portal ou contato.
                </small>
            </div>
        </div>
        """
    )

    with st.container(key="home_search_shell"):
        return st.text_input(
            label="Pesquisa global",
            placeholder="Ex.: Como faço uma autorização? Onde acesso o portal da operadora?",
            label_visibility="collapsed",
            key="home_search",
        )


def _render_primary_actions() -> None:
    actions = [
        (
            "Operadoras",
            "building",
            "Convênios e planos",
            "Consulte regras, coberturas, documentos e informações por operadora.",
        ),
        (
            "Portais",
            "globe",
            "Portais e acessos",
            "Acesse rapidamente os sistemas usados na rotina operacional.",
        ),
        (
            "Documentos",
            "file",
            "Documentação",
            "Confira exigências, validade e orientações documentais.",
        ),
        (
            "Contatos",
            "phone",
            "Centrais e responsáveis",
            "Encontre telefones, e-mails e canais corretos de atendimento.",
        ),
    ]

    cards = []

    for page, icon_name, title, description in actions:
        cards.append(
            f"""
            <a class="home-action-card"
               href="{_nav_href(page)}"
               target="_self">
                <div class="home-action-icon">
                    {icon(icon_name)}
                </div>
                <div class="home-action-copy">
                    <span>{_safe(page).upper()}</span>
                    <strong>{_safe(title)}</strong>
                    <p>{_safe(description)}</p>
                </div>
                <div class="home-action-go">→</div>
            </a>
            """
        )

    st.html(
        f"""
        <section class="home-actions-section">
            <div class="home-section-heading">
                <div>
                    <span>ACESSO DIRETO</span>
                    <h2>O que você precisa fazer agora?</h2>
                </div>
                <p>
                    Entre pelos caminhos mais usados no dia a dia.
                </p>
            </div>

            <div class="home-action-grid">
                {''.join(cards)}
            </div>
        </section>
        """
    )


def _notice_card(notice) -> str:
    period = notice.start_date or ""
    if notice.end_date:
        period = (
            f"{period} até {notice.end_date}"
            if period
            else f"Até {notice.end_date}"
        )

    return f"""
        <article class="home-radar-card home-radar-card-notice">
            <div class="home-radar-top">
                <span class="home-radar-type">
                    {icon("megaphone")} COMUNICADO
                </span>
                <span class="home-radar-badge">{_safe(notice.priority)}</span>
            </div>

            <h3>{_safe(notice.title)}</h3>

            <div class="home-radar-meta">
                {_safe(notice.operator_name)} · {_safe(notice.category)}
            </div>

            <p>{_safe(notice.summary)}</p>

            <div class="home-radar-footer">
                {_safe(period or "Vigência não informada")}
            </div>
        </article>
    """


def _contingency_card(item, featured: bool = False) -> str:
    featured_class = " is-featured" if featured else ""

    return f"""
        <article class="home-radar-card home-radar-card-alert{featured_class}">
            <div class="home-radar-top">
                <span class="home-radar-type">
                    {icon("warning")} CONTINGÊNCIA
                </span>
                <span class="home-radar-badge">{_safe(item.priority)}</span>
            </div>

            <h3>{_safe(item.event)}</h3>

            <div class="home-radar-meta">
                {_safe(item.operator_name)} · {_safe(item.unit)}
            </div>

            <p>{_safe(item.guidance)}</p>

            <div class="home-radar-footer">
                Status: {_safe(item.status)}
            </div>
        </article>
    """


def _render_radar(summary) -> None:
    contingency_cards = ""
    notice_cards = ""

    if summary and summary.contingency_items:
        contingency_cards = "".join(
            _contingency_card(
                item,
                featured=index == 0,
            )
            for index, item in enumerate(summary.contingency_items[:3])
        )
    else:
        contingency_cards = f"""
            <div class="home-radar-empty">
                <div class="home-radar-empty-icon">{icon("check")}</div>
                <div>
                    <strong>Operação sem contingências ativas</strong>
                    <span>Nenhum fluxo alternativo exige atenção neste momento.</span>
                </div>
            </div>
        """

    if summary and summary.notices:
        notice_cards = "".join(
            _notice_card(notice)
            for notice in summary.notices[:3]
        )
    else:
        notice_cards = f"""
            <div class="home-radar-empty">
                <div class="home-radar-empty-icon">{icon("check")}</div>
                <div>
                    <strong>Sem novos comunicados</strong>
                    <span>Não há atualizações publicadas neste momento.</span>
                </div>
            </div>
        """

    st.html(
        f"""
        <section class="home-radar-section">
            <div class="home-section-heading">
                <div>
                    <span>RADAR OPERACIONAL</span>
                    <h2>O que merece atenção agora</h2>
                </div>
                <p>
                    Informações relevantes antes de iniciar ou continuar um atendimento.
                </p>
            </div>

            <div class="home-radar-grid">
                <div class="home-radar-column">
                    <div class="home-radar-column-head">
                        <div>
                            <span>OPERAÇÃO</span>
                            <strong>Contingências</strong>
                        </div>
                        <a href="{_nav_href('Contingências')}" target="_self">
                            Ver todas →
                        </a>
                    </div>
                    {contingency_cards}
                </div>

                <div class="home-radar-column">
                    <div class="home-radar-column-head">
                        <div>
                            <span>ATUALIZAÇÕES</span>
                            <strong>Comunicados</strong>
                        </div>
                        <a href="{_nav_href('Comunicados')}" target="_self">
                            Ver todos →
                        </a>
                    </div>
                    {notice_cards}
                </div>
            </div>
        </section>
        """
    )


def _render_secondary_paths() -> None:
    items = [
        (
            "Consultores",
            "users",
            "Relacionamento comercial",
            "Consulte consultores e carteiras de atendimento.",
        ),
        (
            "Comunicados",
            "megaphone",
            "Atualizações",
            "Veja mudanças e orientações publicadas recentemente.",
        ),
        (
            "Contingências",
            "warning",
            "Fluxos alternativos",
            "Confira indisponibilidades e orientações de contingência.",
        ),
    ]

    cards = "".join(
        f"""
        <a class="home-secondary-card"
           href="{_nav_href(page)}"
           target="_self">
            <span class="home-secondary-icon">{icon(icon_name)}</span>
            <span class="home-secondary-copy">
                <small>{_safe(page).upper()}</small>
                <strong>{_safe(title)}</strong>
                <p>{_safe(description)}</p>
            </span>
            <span class="home-secondary-arrow">→</span>
        </a>
        """
        for page, icon_name, title, description in items
    )

    st.html(
        f"""
        <section class="home-secondary-section">
            <div class="home-section-heading home-section-heading-compact">
                <div>
                    <span>OUTROS CAMINHOS</span>
                    <h2>Continue explorando</h2>
                </div>
            </div>

            <div class="home-secondary-grid">
                {cards}
            </div>
        </section>
        """
    )


def render_home() -> None:
    """Renderiza a Home como hall institucional do Portal Comercial."""

    try:
        summary = get_dashboard_summary()
        data_error = False
    except RuntimeError:
        summary = None
        data_error = True

    _render_hero(summary)

    search_query = _render_search()

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

        query_analysis = analyze_search_query(search_query)

        render_search_results(
            results=search_results,
            key_prefix="home_search",
            query=search_query,
            query_analysis=query_analysis,
        )

    _render_primary_actions()
    _render_radar(summary)
    _render_secondary_paths()

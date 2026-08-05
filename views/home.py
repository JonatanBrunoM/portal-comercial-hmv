import streamlit as st

from components.cards import (
    render_metric_card,
    render_module_card,
)
from components.hero import render_hero
from core.dashboard_service import get_dashboard_summary
from components.search_results import render_search_results
from core.search_service import search_global
from components.sidebar import navigate_to


def render_home() -> None:
    """Renderiza a página inicial do Portal Comercial."""

    try:
        summary = get_dashboard_summary()
        data_error = None

    except RuntimeError as error:
        summary = None
        data_error = str(error)

    render_hero(
        eyebrow="Hospital Moinhos de Vento",
        title="Comercial - Hospital Moinhos de Vento",
        description=(
            "Consulte operadoras, planos, documentos, portais, "
            "contatos e orientações em um único ambiente."
        ),
    )

    search_query = st.text_input(
        label="Pesquisa global",
        placeholder=(
            "Pesquise por operadora, plano, documento, "
            "procedimento ou orientação..."
        ),
        label_visibility="collapsed",
        key="home_search",
    )

    if search_query:
        with st.spinner(
            "Pesquisando na base comercial..."
        ):
            search_results = search_global(
                query=search_query,
                limit=12,
            )
    
        render_search_results(
            results=search_results,
            key_prefix="home_search",
        )
    
        st.divider()

        if data_error:
            st.warning(
                "A base comercial atingiu temporariamente o limite "
                "de consultas. Aguarde alguns instantes e tente novamente."
            )
    
        st.code(data_error)

    st.markdown("## Hoje")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        render_metric_card(
            title="Comunicados",
            value=summary.comunicados if summary else "—",
            description=(
                "Comunicados ativos."
                if summary and summary.comunicados
                else "Nenhum comunicado publicado."
            ),
            icon="📢",
        )

    with col_2:
        render_metric_card(
            title="Contingências",
            value=summary.contingencias if summary else "—",
            description=(
                "Contingências ativas."
                if summary and summary.contingencias
                else "Nenhuma contingência publicada."
            ),
            icon="⚠️",
        )

    with col_3:
        render_metric_card(
            title="Operadoras",
            value=summary.operadoras if summary else "—",
            description="Operadoras ativas na base comercial.",
            icon="🏥",
        )

    with col_4:
        render_metric_card(
            title="Planos",
            value=summary.planos if summary else "—",
            description="Planos ativos cadastrados.",
            icon="📋",
        )

    st.markdown("## Acessos rápidos")

    row_1 = st.columns(3)

    with row_1[0]:
        if render_module_card(
            title="Operadoras",
            description=(
                "Consulte planos, coberturas, documentos "
                "e informações relacionadas."
            ),
            icon="🏥",
            button_key="home_operadoras",
        ):
            navigate_to("Operadoras")
            st.rerun()

    with row_1[1]:
        if render_module_card(
            title="Portais",
            description=(
                "Encontre os portais utilizados para "
                "elegibilidade e autorizações."
            ),
            icon="🌐",
            button_key="home_portais",
        ):
            st.session_state.current_page = "Portais"
            st.rerun()

    with row_1[2]:
        if render_module_card(
            title="Documentos",
            description=(
                "Consulte documentos obrigatórios, "
                "validade e orientações."
            ),
            icon="📄",
            button_key="home_documentos",
        ):
            st.session_state.current_page = "Documentos"
            st.rerun()

    row_2 = st.columns(3)

    with row_2[0]:
        if render_module_card(
            title="Contatos",
            description=(
                "Localize telefones, e-mails, centrais "
                "e responsáveis."
            ),
            icon="📞",
            button_key="home_contatos",
        ):
            st.session_state.current_page = "Contatos"
            st.rerun()

    with row_2[1]:
        if render_module_card(
            title="Contingências",
            description=(
                "Consulte indisponibilidades e fluxos "
                "alternativos."
            ),
            icon="⚠️",
            button_key="home_contingencias",
        ):
            st.session_state.current_page = "Contingências"
            st.rerun()

    with row_2[2]:
        if render_module_card(
            title="Assistente Comercial",
            description=(
                "Faça perguntas utilizando a futura "
                "base de conhecimento oficial."
            ),
            icon="✨",
            button_key="home_assistente",
        ):
            st.session_state.current_page = "Assistente"
            st.rerun()

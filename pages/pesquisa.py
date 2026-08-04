import streamlit as st

from components.hero import render_hero
from components.search_results import render_search_results
from core.search_service import search_global


def render_pesquisa() -> None:
    """Renderiza a página completa de pesquisa."""

    render_hero(
        eyebrow="Base de conhecimento",
        title="Pesquisa inteligente",
        description=(
            "Pesquise operadoras, planos, documentos, "
            "portais, contatos, autorizações e coberturas."
        ),
    )

    initial_query = st.session_state.get(
        "last_search_query",
        "",
    )

    query = st.text_input(
        label="Pesquisar",
        value=initial_query,
        placeholder=(
            "Exemplo: autorização CASSI, "
            "documentos CABERGS ou OPME..."
        ),
        key="full_search_query",
    )

    st.session_state.last_search_query = query

    if len(query.strip()) < 2:
        st.info(
            "Digite pelo menos dois caracteres para pesquisar."
        )

        return

    with st.spinner(
        "Consultando a base comercial..."
    ):
        results = search_global(
            query=query,
            limit=50,
        )

    render_search_results(
        results=results,
        key_prefix="full_search",
    )

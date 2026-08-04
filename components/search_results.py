from __future__ import annotations

import html

import streamlit as st

from core.search_service import SearchResult


CATEGORY_ICONS = {
    "Operadoras": "🏥",
    "Planos": "📋",
    "Portais": "🌐",
    "Elegibilidade": "✅",
    "Documentos": "📄",
    "Autorizações": "🔑",
    "Coberturas": "🩺",
    "Contatos": "📞",
    "Contingências": "⚠️",
    "Dicas operacionais": "💡",
}


def render_search_result(
    result: SearchResult,
    key_prefix: str,
) -> bool:
    """Renderiza um resultado individual."""

    icon = CATEGORY_ICONS.get(
        result.category,
        "🔎",
    )

    safe_category = html.escape(
        result.category,
    )

    safe_title = html.escape(
        result.title,
    )

    safe_subtitle = html.escape(
        result.subtitle,
    )

    safe_description = html.escape(
        result.description,
    )

    result_html = f"""
    <article class="portal-search-result">
        <div class="portal-search-result-top">
            <span class="portal-search-result-icon">
                {icon}
            </span>

            <span class="portal-search-result-category">
                {safe_category}
            </span>
        </div>

        <div class="portal-search-result-title">
            {safe_title}
        </div>

        <div class="portal-search-result-subtitle">
            {safe_subtitle}
        </div>

        <div class="portal-search-result-description">
            {safe_description}
        </div>
    </article>
    """

    with st.container(border=True):
        st.html(
            result_html,
        )

        return st.button(
            "Ver detalhes",
            key=(
                f"{key_prefix}_"
                f"{result.category}_"
                f"{result.result_id}"
            ),
            use_container_width=True,
        )


def render_search_results(
    results: list[SearchResult],
    key_prefix: str,
) -> None:
    """Renderiza a lista completa de resultados."""

    if not results:
        st.info(
            "Não encontramos informações para essa pesquisa. "
            "Tente o nome da operadora, plano, documento, "
            "procedimento ou tipo de atendimento."
        )

        return

    st.caption(
        f"{len(results)} resultado(s) encontrado(s)."
    )

    for result in results:
        if render_search_result(
            result=result,
            key_prefix=key_prefix,
        ):
            if result.operator_id:
                st.session_state[
                    "selected_operator_id"
                ] = result.operator_id
        
                st.session_state.current_page = (
                    "Operadoras"
                )
        
            else:
                st.session_state[
                    "selected_search_result"
                ] = result
        
                st.session_state.current_page = (
                    "Pesquisa"
                )
        
            st.rerun()

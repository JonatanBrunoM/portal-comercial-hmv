from __future__ import annotations

import html

import streamlit as st

from core.search_service import SearchResult
from components.sidebar import navigate_to


CATEGORY_ICONS = {
    "Operadoras": "🏥",
    "Planos": "📋",
    "Portais": "🌐",
    "Elegibilidade": "✅",
    "Documentos": "📄",
    "Autorizações": "🔑",
    "Coberturas": "🩺",
    "Contatos": "📞",
    "Consultores": "👤",
    "Comunicados": "📢",
    "Contingências": "⚠️",
    "Dicas operacionais": "💡",
}


def _open_result(result: SearchResult) -> None:
    """Agenda a navegação sem disputar estado com widgets já renderizados."""
    if result.operator_id:
        st.session_state["selected_operator_id"] = result.operator_id

        # Não alteramos diretamente o estado do selectbox da ficha.
        # A ficha da operadora consome este destino antes de criar o widget.
        st.session_state["pending_operator_destination"] = {
            "operator_id": result.operator_id,
            "module": result.target_module or "Visão geral",
        }

        navigate_to("Operadoras")
    else:
        st.session_state["selected_search_result"] = result
        navigate_to("Pesquisa")

    st.rerun()


def render_search_result(
    result: SearchResult,
    key_prefix: str,
) -> bool:
    icon = CATEGORY_ICONS.get(result.category, "🔎")

    safe_category = html.escape(result.category)
    safe_title = html.escape(result.title)
    safe_subtitle = html.escape(result.subtitle)
    safe_description = html.escape(result.description)
    safe_operator = html.escape(result.operator_name)

    operator_badge = (
        f'<span class="portal-search-result-operator">{safe_operator}</span>'
        if safe_operator
        else ""
    )

    description_html = (
        f'<div class="portal-search-result-description">{safe_description}</div>'
        if safe_description
        else ""
    )

    result_html = f"""
    <article class="portal-search-result">
        <div class="portal-search-result-top">
            <span class="portal-search-result-icon">{icon}</span>
            <span class="portal-search-result-category">{safe_category}</span>
            {operator_badge}
        </div>
        <div class="portal-search-result-title">{safe_title}</div>
        <div class="portal-search-result-subtitle">{safe_subtitle}</div>
        {description_html}
    </article>
    """

    with st.container(border=True):
        st.html(result_html)

        button_label = (
            f"Abrir em {result.target_module}"
            if result.target_module and result.target_module != "Visão geral"
            else "Abrir operadora"
        )

        return st.button(
            button_label,
            key=f"{key_prefix}_{result.category}_{result.result_id}_{result.operator_id}",
            use_container_width=True,
        )


def render_search_results(
    results: list[SearchResult],
    key_prefix: str,
) -> None:
    if not results:
        st.info(
            "Não encontramos informações para essa pesquisa. "
            "Tente combinar a operadora com o que você precisa, "
            "por exemplo: “Bradesco autorização”, “CASSI telefone” "
            "ou “Unimed portal”."
        )
        return

    st.caption(f"{len(results)} resultado(s) relevante(s) encontrado(s).")

    for result in results:
        if render_search_result(result=result, key_prefix=key_prefix):
            _open_result(result)

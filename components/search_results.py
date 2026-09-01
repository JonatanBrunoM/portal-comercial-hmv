from __future__ import annotations

import html

import streamlit as st

from components.sidebar import navigate_to
from core.search_service import SearchResult, group_search_results
from ui.icons import category_icon


CATEGORY_ORDER = [
    "Contingências",
    "Portais",
    "Autorizações",
    "Elegibilidade",
    "Contatos",
    "Documentos",
    "Coberturas",
    "Comunicados",
    "Planos",
    "Consultores",
    "Dicas operacionais",
    "Operadoras",
]


def _open_result(result: SearchResult) -> None:
    if result.operator_id:
        st.session_state["selected_operator_id"] = result.operator_id
        st.session_state["pending_operator_destination"] = {
            "operator_id": result.operator_id,
            "module": result.target_module or "Visão geral",
        }
        navigate_to("Operadoras")
    else:
        st.session_state["selected_search_result"] = result
        navigate_to("Pesquisa")

    st.rerun()


def _result_button_label(result: SearchResult) -> str:
    if result.target_module and result.target_module != "Visão geral":
        return f"Abrir em {result.target_module}"
    return "Abrir operadora"


def _render_result_content(result: SearchResult, featured: bool = False) -> None:
    icon_html = category_icon(result.category)
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
    featured_badge = (
        '<span class="portal-search-result-category">MELHOR RESULTADO</span>'
        if featured
        else ""
    )

    st.html(
        f"""
        <article class="portal-search-result">
            <div class="portal-search-result-top">
                <span class="portal-search-result-icon">{icon_html}</span>
                <span class="portal-search-result-category">{safe_category}</span>
                {operator_badge}
                {featured_badge}
            </div>
            <div class="portal-search-result-title">{safe_title}</div>
            <div class="portal-search-result-subtitle">{safe_subtitle}</div>
            {description_html}
        </article>
        """
    )


def render_search_result(
    result: SearchResult,
    key_prefix: str,
    featured: bool = False,
) -> None:
    with st.container(border=True):
        _render_result_content(result, featured=featured)
        if st.button(
            _result_button_label(result),
            key=f"{key_prefix}_{result.category}_{result.result_id}_{result.operator_id}",
            use_container_width=True,
            type="primary" if featured else "secondary",
        ):
            _open_result(result)


def render_search_results(
    results: list[SearchResult],
    key_prefix: str,
    query: str,
    query_analysis: dict[str, object] | None = None,
) -> None:
    if not results:
        st.info(
            "Não encontramos informações para essa pesquisa. "
            "Tente combinar a operadora com o que você precisa, "
            "por exemplo: “Bradesco autorização”, “CASSI telefone” "
            "ou “Unimed portal”."
        )
        return

    analysis = query_analysis or {}
    groups = group_search_results(results)
    best = results[0]

    st.caption(f"{len(results)} resultado(s) relevante(s) para “{query}”.")

    # Quando a pesquisa é apenas o nome da operadora, o melhor caminho é a
    # visão geral dela, mesmo que uma regra específica tenha pontuação parecida.
    if analysis.get("is_operator_only"):
        operator_result = next(
            (item for item in results if item.category == "Operadoras"),
            None,
        )
        if operator_result is not None:
            best = operator_result

    st.markdown("### Melhor resultado")
    render_search_result(
        best,
        key_prefix=f"{key_prefix}_best",
        featured=True,
    )

    remaining = [item for item in results if item is not best]
    if not remaining:
        return

    st.markdown("### Outros resultados")

    remaining_groups = group_search_results(remaining)
    ordered_categories = [
        category
        for category in CATEGORY_ORDER
        if category in remaining_groups
    ]
    ordered_categories.extend(
        category
        for category in remaining_groups
        if category not in ordered_categories
    )

    for category in ordered_categories:
        category_results = remaining_groups[category]
        with st.expander(
            f"{category} · {len(category_results)}",
            expanded=len(ordered_categories) <= 2,
        ):
            for result in category_results:
                render_search_result(
                    result,
                    key_prefix=f"{key_prefix}_{category}",
                    featured=False,
                )

from collections.abc import Callable
from textwrap import dedent

import streamlit as st

from config.constants import APP_CONFIG


NAVIGATION_ITEMS = {
    "Início": "🏠",
    "Pesquisa": "🔎",
    "Operadoras": "🏥",
    "Portais": "🌐",
    "Documentos": "📄",
    "Contatos": "📞",
    "Consultores": "👥",
    "Comunicados": "📢",
    "Contingências": "⚠️",
    "Fórum": "💬",
    "Assistente": "✨",
}


def render_sidebar(on_change: Callable[[], None] | None = None) -> str:
    """
    Renderiza a navegação lateral.

    Retorna:
        Nome da página selecionada.
    """

    with st.sidebar:
        sidebar_header = dedent(
            f"""
            <div style="
                padding: 0.25rem 0 1.4rem 0;
                border-bottom: 1px solid #DCE3E8;
                margin-bottom: 1.2rem;
            ">
                <div style="
                    color: #005691;
                    font-size: 0.78rem;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                ">
                    {APP_CONFIG.ORGANIZATION_NAME}
                </div>
        
                <div style="
                    color: #17212B;
                    font-size: 1.25rem;
                    font-weight: 750;
                    margin-top: 0.3rem;
                ">
                    {APP_CONFIG.APP_NAME}
                </div>
            </div>
            """
        )
        
        st.markdown(
            sidebar_header,
            unsafe_allow_html=True,
        )

        labels = [
            f"{icon}  {page}"
            for page, icon in NAVIGATION_ITEMS.items()
        ]

        selected_label = st.radio(
            label="Navegação",
            options=labels,
            index=list(NAVIGATION_ITEMS).index(
                st.session_state.get(
                    "current_page",
                    APP_CONFIG.DEFAULT_PAGE,
                )
            ),
            label_visibility="collapsed",
            key="main_navigation",
            on_change=on_change,
        )

        selected_page = selected_label.split("  ", maxsplit=1)[1]
        st.session_state.current_page = selected_page

        st.markdown("---")

        st.caption(
            "Base de conhecimento da área Comercial."
        )

    return selected_page

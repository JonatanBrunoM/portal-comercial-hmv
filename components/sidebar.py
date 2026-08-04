from collections.abc import Callable

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


def render_sidebar(
    on_change: Callable[[], None] | None = None,
) -> str:
    """Renderiza a navegação lateral."""

    with st.sidebar:
        sidebar_header = f"""
        <div class="portal-sidebar-header">
            <div class="portal-sidebar-organization">
                {APP_CONFIG.ORGANIZATION_NAME}
            </div>

            <div class="portal-sidebar-title">
                {APP_CONFIG.APP_NAME}
            </div>
        </div>
        """

        st.html(sidebar_header)

        current_page = st.session_state.get(
            "current_page",
            APP_CONFIG.DEFAULT_PAGE,
        )

        page_names = list(NAVIGATION_ITEMS.keys())

        if current_page not in page_names:
            current_page = APP_CONFIG.DEFAULT_PAGE

        labels = [
            f"{icon}  {page}"
            for page, icon in NAVIGATION_ITEMS.items()
        ]

        selected_label = st.radio(
            label="Navegação",
            options=labels,
            index=page_names.index(current_page),
            label_visibility="collapsed",
            key="main_navigation",
            on_change=on_change,
        )

        selected_page = selected_label.split("  ", maxsplit=1)[1]
        st.session_state.current_page = selected_page

        st.divider()

        st.caption(
            "Base de conhecimento da área Comercial."
        )

    return selected_page

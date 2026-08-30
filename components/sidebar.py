from collections.abc import Callable

import streamlit as st

from config.constants import APP_CONFIG
from core.auth_service import (
    get_current_profile,
    get_google_user,
    logout,
)


NAVIGATION_ITEMS = {
    "Início": "🏠",
    "Pesquisa": "🔎",
    "Operadoras": "🏥",
    "Portais": "🌐",
    "Documentos": "📄",
    "Contatos": "📞",
    "Consultores": "👥",
    "Particular": "💳",
    "Comunicados": "📢",
    "Contingências": "⚠️",
    "Fórum": "💬",
    "Assistente": "✨",
    "Administração": "⚙️",
}


def get_available_navigation_items() -> dict[str, str]:
    """
    Retorna apenas as opções de navegação permitidas
    para o usuário autenticado.
    """

    navigation_items = NAVIGATION_ITEMS.copy()

    profile = get_current_profile()

    if not profile or profile.get("role") != "admin":
        navigation_items.pop("Administração", None)

    return navigation_items


def navigate_to(page: str) -> None:
    """
    Agenda a navegação para a próxima execução do Streamlit.

    Não altera diretamente a chave do widget da sidebar,
    pois isso gera StreamlitAPIException após o st.radio()
    já ter sido criado.
    """

    navigation_items = get_available_navigation_items()

    if page not in navigation_items:
        page = APP_CONFIG.DEFAULT_PAGE

    st.session_state.pending_page = page


def render_user_area() -> None:
    """
    Renderiza os dados do usuário autenticado
    na parte inferior da sidebar.
    """

    profile = get_current_profile()
    google_user = get_google_user()

    if not google_user:
        return

    nome = (
        (profile or {}).get("nome")
        or google_user.get("name")
        or "Usuário"
    )

    email = (
        (profile or {}).get("email")
        or google_user.get("email")
        or ""
    )

    role = (profile or {}).get("role", "usuario")

    foto_url = (
        (profile or {}).get("foto_url")
        or google_user.get("picture")
    )

    st.markdown(
        """
        <div class="portal-sidebar-user-label">
            Usuário conectado
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_avatar, col_user = st.columns(
        [0.22, 0.78],
        vertical_alignment="center",
    )

    with col_avatar:
        if foto_url:
            st.image(
                foto_url,
                width=42,
            )
        else:
            inicial = nome[:1].upper() if nome else "U"

            st.markdown(
                f"""
                <div style="
                    width:42px;
                    height:42px;
                    border-radius:50%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    background:#EEF4F8;
                    font-weight:700;
                    font-size:1rem;
                ">
                    {inicial}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_user:
        st.markdown(
            f"""
            <div style="
                line-height:1.2;
                overflow:hidden;
            ">
                <div style="
                    font-size:0.88rem;
                    font-weight:700;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                    {nome}
                </div>

                <div style="
                    margin-top:3px;
                    font-size:0.72rem;
                    opacity:0.68;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                    {email}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if role == "admin":
        st.caption("⚙️ Administrador")
    else:
        st.caption("👤 Usuário")

    if st.button(
        "Sair da conta",
        key="sidebar_logout",
        use_container_width=True,
    ):
        logout()


def render_sidebar(
    on_change: Callable[[], None] | None = None,
) -> str:
    """
    Renderiza a navegação lateral do Portal Comercial.
    """

    navigation_items = get_available_navigation_items()

    pending_page = st.session_state.pop(
        "pending_page",
        None,
    )

    if pending_page in navigation_items:
        st.session_state.current_page = pending_page

        st.session_state.pop(
            "main_navigation",
            None,
        )

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

        page_names = list(
            navigation_items.keys()
        )

        if current_page not in page_names:
            current_page = APP_CONFIG.DEFAULT_PAGE
            st.session_state.current_page = current_page

            st.session_state.pop(
                "main_navigation",
                None,
            )

        labels = [
            f"{icon}  {page}"
            for page, icon in navigation_items.items()
        ]

        selected_label = st.radio(
            label="Navegação",
            options=labels,
            index=page_names.index(current_page),
            label_visibility="collapsed",
            key="main_navigation",
            on_change=on_change,
        )

        selected_page = selected_label.split(
            "  ",
            maxsplit=1,
        )[1]

        st.session_state.current_page = selected_page

        st.divider()

        render_user_area()

        st.divider()

        st.caption(
            "Base de conhecimento da área Comercial."
        )

    return selected_page

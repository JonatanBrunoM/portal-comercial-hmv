from collections.abc import Callable

import streamlit as st

from config.constants import (
    APP_CONFIG,
)

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
    "Comunicados": "📢",
    "Contingências": "⚠️",
    "Administração": "⚙️",
}


def get_available_navigation_items(
) -> dict[str, str]:
    """
    Retorna apenas os módulos permitidos
    para o usuário atual.
    """

    navigation_items = (
        NAVIGATION_ITEMS.copy()
    )

    profile = (
        get_current_profile()
    )

    if (
        not profile
        or profile.get(
            "role"
        ) != "admin"
    ):
        navigation_items.pop(
            "Administração",
            None,
        )

    return navigation_items


def navigate_to(
    page: str,
) -> None:
    """
    Agenda uma mudança de página
    para a próxima execução.
    """

    navigation_items = (
        get_available_navigation_items()
    )

    if page not in navigation_items:
        page = (
            APP_CONFIG.DEFAULT_PAGE
        )

    st.session_state[
        "pending_page"
    ] = page


def render_user_area() -> None:
    """Renderiza a conta em formato compatível com a sidebar compacta."""

    profile = get_current_profile()
    google_user = get_google_user()

    if not google_user:
        return

    nome = (
        (profile or {}).get("nome")
        or google_user.get("name")
        or "Usuário"
    )
    role = (profile or {}).get("role", "usuario")
    foto_url = (
        (profile or {}).get("foto_url")
        or google_user.get("picture")
    )

    role_label = "Administrador" if role == "admin" else "Usuário"

    st.html(
        '<div class="portal-sidebar-section-label">Sua conta</div>'
    )

    if foto_url:
        col_avatar, col_copy = st.columns(
            [0.20, 0.80],
            vertical_alignment="center",
        )
        with col_avatar:
            st.image(foto_url, width=42)
        with col_copy:
            st.html(
                f"""
                <div class="portal-sidebar-user-copy">
                    <div class="portal-sidebar-user-name">{nome}</div>
                    <div class="portal-sidebar-user-role">{role_label}</div>
                </div>
                """
            )
    else:
        inicial = nome[:1].upper() if nome else "U"
        st.html(
            f"""
            <div class="portal-sidebar-user-compact">
                <div class="portal-sidebar-avatar-fallback">{inicial}</div>
                <div class="portal-sidebar-user-copy">
                    <div class="portal-sidebar-user-name">{nome}</div>
                    <div class="portal-sidebar-user-role">{role_label}</div>
                </div>
            </div>
            """
        )

    if st.button(
        "↪  Sair da conta",
        key="sidebar_logout",
        use_container_width=True,
    ):
        logout()


def render_sidebar(
    on_change: Callable[
        [],
        None,
    ]
    | None = None,
) -> str:
    """
    Renderiza a navegação lateral.
    """

    navigation_items = (
        get_available_navigation_items()
    )

    pending_page = (
        st.session_state.pop(
            "pending_page",
            None,
        )
    )

    if (
        pending_page
        in navigation_items
    ):
        st.session_state[
            "current_page"
        ] = pending_page

        st.session_state.pop(
            "main_navigation",
            None,
        )

    with st.sidebar:
        sidebar_header = f"""
        <div class="portal-sidebar-header">
            <div class="portal-sidebar-brandmark">
                <div class="portal-sidebar-brand-icon">M</div>
                <div class="portal-sidebar-brand-copy">
                    <div class="portal-sidebar-organization">
                        {APP_CONFIG.ORGANIZATION_NAME}
                    </div>
                    <div class="portal-sidebar-title">
                        {APP_CONFIG.APP_NAME}
                    </div>
                </div>
            </div>
        </div>
        """

        st.html(
            sidebar_header
        )

        st.html(
            '<div class="portal-sidebar-section-label">Navegação</div>'
        )

        current_page = (
            st.session_state.get(
                "current_page",
                APP_CONFIG.DEFAULT_PAGE,
            )
        )

        page_names = list(
            navigation_items.keys()
        )

        if (
            current_page
            not in page_names
        ):
            current_page = (
                APP_CONFIG.DEFAULT_PAGE
            )

            st.session_state[
                "current_page"
            ] = current_page

            st.session_state.pop(
                "main_navigation",
                None,
            )

        selected_page = st.radio(
            label="Navegação",
            options=page_names,
            index=page_names.index(
                current_page
            ),
            format_func=lambda page: (
                f"{navigation_items[page]}  {page}"
            ),
            label_visibility="collapsed",
            key="main_navigation",
            on_change=on_change,
        )

        st.session_state[
            "current_page"
        ] = selected_page

        st.divider()

        render_user_area()

        st.divider()

        st.caption(
            "Base de conhecimento "
            "da área Comercial."
        )

    return selected_page

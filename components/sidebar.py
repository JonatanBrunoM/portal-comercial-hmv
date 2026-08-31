from collections.abc import Callable
import html

import streamlit as st

from config.constants import APP_CONFIG
from core.auth_service import (
    get_current_profile,
    get_google_user,
    logout,
)


NAVIGATION_ITEMS = {
    "Início": ":material/home:",
    "Pesquisa": ":material/search:",
    "Operadoras": ":material/apartment:",
    "Portais": ":material/language:",
    "Documentos": ":material/description:",
    "Contatos": ":material/contact_phone:",
    "Consultores": ":material/groups:",
    "Comunicados": ":material/campaign:",
    "Contingências": ":material/warning:",
    "Administração": ":material/settings:",
}


def get_available_navigation_items() -> dict[str, str]:
    """Retorna apenas os módulos permitidos para o usuário atual."""

    navigation_items = NAVIGATION_ITEMS.copy()
    profile = get_current_profile()

    if not profile or profile.get("role") != "admin":
        navigation_items.pop("Administração", None)

    return navigation_items


def navigate_to(page: str) -> None:
    """Altera a rota principal e mantém a sidebar sincronizada."""

    navigation_items = get_available_navigation_items()

    if page not in navigation_items:
        page = APP_CONFIG.DEFAULT_PAGE

    st.session_state["current_page"] = page
    st.session_state.pop("pending_page", None)
    st.session_state.pop("main_navigation", None)


def _safe(value: object) -> str:
    return html.escape(str(value or ""))


def render_user_area() -> None:
    """Renderiza a conta alinhada ao mesmo eixo visual da rail."""

    profile = get_current_profile()
    google_user = get_google_user()

    if not google_user:
        return

    name = (
        (profile or {}).get("nome")
        or google_user.get("name")
        or "Usuário"
    )
    role = (profile or {}).get("role", "usuario")
    picture = (
        (profile or {}).get("foto_url")
        or google_user.get("picture")
        or ""
    )

    role_label = "Administrador" if role == "admin" else "Usuário"
    initial = name[:1].upper() if name else "U"

    avatar_html = (
        f'<img class="portal-sidebar-avatar" src="{_safe(picture)}" alt="">'
        if picture
        else f'<div class="portal-sidebar-avatar-fallback">{_safe(initial)}</div>'
    )

    st.html(
        f"""
        <div class="portal-sidebar-account-label">CONTA</div>
        <div class="portal-sidebar-user-compact">
            {avatar_html}
            <div class="portal-sidebar-user-copy">
                <div class="portal-sidebar-user-name">{_safe(name)}</div>
                <div class="portal-sidebar-user-role">{_safe(role_label)}</div>
            </div>
        </div>
        """
    )

    if st.button(
        "Sair da conta",
        key="sidebar_logout",
        icon=":material/logout:",
        use_container_width=True,
    ):
        logout()


def render_sidebar(
    on_change: Callable[[], None] | None = None,
) -> str:
    """Renderiza navegação lateral compacta com ícones Material."""

    navigation_items = get_available_navigation_items()
    page_names = list(navigation_items.keys())

    pending_page = st.session_state.pop("pending_page", None)
    if pending_page in navigation_items:
        st.session_state["current_page"] = pending_page

    current_page = st.session_state.get(
        "current_page",
        APP_CONFIG.DEFAULT_PAGE,
    )

    if current_page not in page_names:
        current_page = APP_CONFIG.DEFAULT_PAGE
        st.session_state["current_page"] = current_page

    with st.sidebar:
        st.html(
            f"""
            <div class="portal-sidebar-header">
                <div class="portal-sidebar-brandmark">
                    <div class="portal-sidebar-brand-icon">M</div>
                    <div class="portal-sidebar-brand-copy">
                        <div class="portal-sidebar-organization">
                            {_safe(APP_CONFIG.ORGANIZATION_NAME)}
                        </div>
                        <div class="portal-sidebar-title">
                            {_safe(APP_CONFIG.APP_NAME)}
                        </div>
                    </div>
                </div>
            </div>
            <div class="portal-sidebar-section-label">NAVEGAÇÃO</div>
            """
        )

        for page, material_icon in navigation_items.items():
            is_active = page == current_page

            clicked = st.button(
                page,
                key=f"nav_{page}",
                icon=material_icon,
                type="primary" if is_active else "secondary",
                use_container_width=True,
            )

            if clicked:
                st.session_state["current_page"] = page
                st.session_state.pop("pending_page", None)
                st.session_state.pop("main_navigation", None)

                if on_change:
                    on_change()

                st.rerun()

        st.html('<div class="portal-sidebar-separator"></div>')
        render_user_area()

        st.html(
            """
            <div class="portal-sidebar-footer">
                Base Comercial HMV
            </div>
            """
        )

    return st.session_state.get(
        "current_page",
        APP_CONFIG.DEFAULT_PAGE,
    )

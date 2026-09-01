from collections.abc import Callable
import html

import streamlit as st

from config.constants import APP_CONFIG
from ui.icons import icon

from core.auth_service import (
    get_current_profile,
    get_google_user,
    logout,
)


NAVIGATION_ITEMS = {
    "Início": "home",
    "Pesquisa": "search",
    "Operadoras": "building",
    "Portais": "globe",
    "Documentos": "file",
    "Contatos": "phone",
    "Consultores": "users",
    "Comunicados": "megaphone",
    "Contingências": "warning",
    "Administração": "settings",
}

PAGE_SLUGS = {
    "Início": "inicio",
    "Pesquisa": "pesquisa",
    "Operadoras": "operadoras",
    "Portais": "portais",
    "Documentos": "documentos",
    "Contatos": "contatos",
    "Consultores": "consultores",
    "Comunicados": "comunicados",
    "Contingências": "contingencias",
    "Administração": "administracao",
}

SLUG_PAGES = {slug: page for page, slug in PAGE_SLUGS.items()}



def get_available_navigation_items() -> dict[str, str]:
    navigation_items = NAVIGATION_ITEMS.copy()
    profile = get_current_profile()

    if not profile or profile.get("role") != "admin":
        navigation_items.pop("Administração", None)

    return navigation_items


def _safe(value: object) -> str:
    return html.escape(str(value or ""))


def _sync_query_page(page: str) -> None:
    slug = PAGE_SLUGS.get(page, PAGE_SLUGS[APP_CONFIG.DEFAULT_PAGE])
    st.query_params["page"] = slug


def navigate_to(page: str) -> None:
    navigation_items = get_available_navigation_items()

    if page not in navigation_items:
        page = APP_CONFIG.DEFAULT_PAGE

    st.session_state["current_page"] = page
    st.session_state.pop("pending_page", None)
    st.session_state.pop("main_navigation", None)
    _sync_query_page(page)


def _resolve_page_from_query() -> str | None:
    try:
        slug = st.query_params.get("page")
    except Exception:
        return None

    if isinstance(slug, list):
        slug = slug[0] if slug else None

    if not slug:
        return None

    return SLUG_PAGES.get(str(slug))


def _render_user_area_html() -> str:
    profile = get_current_profile()
    google_user = get_google_user()

    if not google_user:
        return ""

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

    if picture:
        avatar = f'<img class="portal-sidebar-avatar" src="{_safe(picture)}" alt="">'
    else:
        avatar = f'<div class="portal-sidebar-avatar-fallback">{_safe(initial)}</div>'

    return f"""
        <div class="portal-sidebar-separator"></div>
        <div class="portal-sidebar-account-label">CONTA</div>
        <div class="portal-sidebar-user-compact">
            {avatar}
            <div class="portal-sidebar-user-copy">
                <div class="portal-sidebar-user-name">{_safe(name)}</div>
                <div class="portal-sidebar-user-role">{_safe(role_label)}</div>
            </div>
        </div>
    """


def render_sidebar(
    on_change: Callable[[], None] | None = None,
) -> str:
    navigation_items = get_available_navigation_items()

    query_page = _resolve_page_from_query()
    if query_page in navigation_items:
        st.session_state["current_page"] = query_page

    pending_page = st.session_state.pop("pending_page", None)
    if pending_page in navigation_items:
        st.session_state["current_page"] = pending_page

    current_page = st.session_state.get(
        "current_page",
        APP_CONFIG.DEFAULT_PAGE,
    )

    if current_page not in navigation_items:
        current_page = APP_CONFIG.DEFAULT_PAGE
        st.session_state["current_page"] = current_page

    navigation_html = []

    for page, icon_name in navigation_items.items():
        slug = PAGE_SLUGS[page]
        active_class = " is-active" if page == current_page else ""
        icon_svg = icon(icon_name)

        navigation_html.append(
            f"""
            <a class="portal-sidebar-nav-item{active_class}"
               href="?page={slug}"
               target="_self"
               aria-label="{_safe(page)}"
               title="{_safe(page)}">
                <span class="portal-sidebar-nav-icon">{icon_svg}</span>
                <span class="portal-sidebar-nav-text">{_safe(page)}</span>
            </a>
            """
        )

    with st.sidebar:
        st.html(
            f"""
            <div class="portal-sidebar-shell">
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

                <nav class="portal-sidebar-nav">
                    {''.join(navigation_html)}
                </nav>

                {_render_user_area_html()}
            </div>
            """
        )

        if st.button(
            "Sair da conta",
            key="sidebar_logout",
            use_container_width=True,
        ):
            logout()

        st.html(
            '<div class="portal-sidebar-footer">Base Comercial HMV</div>'
        )

    return current_page

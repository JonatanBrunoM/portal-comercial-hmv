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
    "Início": "home",
    "Pesquisa": "search",
    "Operadoras": "building",
    "Portais": "globe",
    "Documentos": "file",
    "Contatos": "phone",
    "Consultores": "users",
    "Comunicados": "megaphone",
    "Contingências": "triangle",
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


ICON_SVGS = {
    "home": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 10.8 12 3l9 7.8v9.2a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>
        </svg>
    """,
    "search": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="6.5"/>
            <path d="m16 16 5 5"/>
        </svg>
    """,
    "building": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 21V5l8-3v19M12 8h8v13M8 7v2M8 12v2M8 17v2M16 11v2M16 16v2"/>
        </svg>
    """,
    "globe": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9"/>
            <path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>
        </svg>
    """,
    "file": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 2h8l4 4v16H6zM14 2v5h5M9 12h6M9 16h6"/>
        </svg>
    """,
    "phone": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 3 4 5.5c.5 7 7 13.5 14 14l2.5-3-4-3-2 2c-2.5-1-5-3.5-6-6l2-2z"/>
        </svg>
    """,
    "users": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="9" cy="8" r="3"/>
            <circle cx="17" cy="9" r="2.5"/>
            <path d="M3 20c0-4 2.5-6 6-6s6 2 6 6M14 15c4 0 7 1.5 7 5"/>
        </svg>
    """,
    "megaphone": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 11v4h4l8 4V7l-8 4zM15 10l5-2v10l-5-2M7 15l1 5h3l-1-4"/>
        </svg>
    """,
    "triangle": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3 2.8 20h18.4zM12 9v5M12 17.5h.01"/>
        </svg>
    """,
    "settings": """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.86 2.86-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.1A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.86-2.86.06-.06A1.7 1.7 0 0 0 4.2 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H2.4v-4h.1A1.7 1.7 0 0 0 4.2 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06L6.66 3.8l.06.06A1.7 1.7 0 0 0 8.6 4.2a1.7 1.7 0 0 0 1-.6A1.7 1.7 0 0 0 10 2.5v-.1h4v.1a1.7 1.7 0 0 0 1 1.7 1.7 1.7 0 0 0 1.88-.34l.06-.06 2.86 2.86-.06.06A1.7 1.7 0 0 0 19.4 8.6a1.7 1.7 0 0 0 .6 1 1.7 1.7 0 0 0 1.1.4h.1v4h-.1a1.7 1.7 0 0 0-1.7 1z"/>
        </svg>
    """,
}


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
        icon_svg = ICON_SVGS[icon_name]

        navigation_html.append(
            f"""
            <a class="portal-sidebar-nav-item{active_class}"
               href="?page={slug}"
               target="_self"
               aria-label="{_safe(page)}">
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

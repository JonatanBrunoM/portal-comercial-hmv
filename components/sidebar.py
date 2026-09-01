from __future__ import annotations

from typing import Callable
import html

import streamlit as st

from config.constants import APP_CONFIG
from core.auth_service import (
    get_current_profile,
    get_google_user,
    logout,
)
from ui.icons import icon


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


def _user_data() -> dict[str, str] | None:
    profile = get_current_profile()
    google_user = get_google_user()

    if not google_user:
        return None

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

    return {
        "name": str(name),
        "role": "Administrador" if role == "admin" else "Usuário",
        "picture": str(picture or ""),
        "initial": str(name)[:1].upper() if name else "U",
    }


def _avatar_html(user: dict[str, str], css_class: str) -> str:
    if user["picture"]:
        return (
            f'<img class="{css_class}" '
            f'src="{_safe(user["picture"])}" '
            f'alt="Foto de {_safe(user["name"])}">'
        )

    return (
        f'<div class="{css_class} portal-sidebar-avatar-fallback">'
        f'{_safe(user["initial"])}</div>'
    )


def _navigation_links(
    navigation_items: dict[str, str],
    current_page: str,
    *,
    compact: bool,
) -> str:
    links: list[str] = []

    for page, icon_name in navigation_items.items():
        slug = PAGE_SLUGS[page]
        active_class = " is-active" if page == current_page else ""
        item_class = (
            "portal-sidebar-compact-item"
            if compact
            else "portal-sidebar-expanded-item"
        )

        label = "" if compact else (
            f'<span class="portal-sidebar-expanded-text">{_safe(page)}</span>'
        )

        links.append(
            f"""
            <a class="{item_class}{active_class}"
               href="?page={slug}"
               target="_self"
               aria-label="{_safe(page)}"
               title="{_safe(page)}">
                <span class="portal-sidebar-icon-slot">
                    {icon(icon_name)}
                </span>
                {label}
            </a>
            """
        )

    return "".join(links)


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

    user = _user_data()

    compact_navigation = _navigation_links(
        navigation_items,
        current_page,
        compact=True,
    )
    expanded_navigation = _navigation_links(
        navigation_items,
        current_page,
        compact=False,
    )

    compact_account = ""
    expanded_account = ""

    if user:
        compact_account = f"""
            <div class="portal-sidebar-compact-account">
                {_avatar_html(user, "portal-sidebar-avatar-compact")}
            </div>
        """

        expanded_account = f"""
            <div class="portal-sidebar-expanded-account">
                {_avatar_html(user, "portal-sidebar-avatar-expanded")}
                <div class="portal-sidebar-expanded-user-copy">
                    <div class="portal-sidebar-expanded-user-name">
                        {_safe(user["name"])}
                    </div>
                    <div class="portal-sidebar-expanded-user-role">
                        {_safe(user["role"])}
                    </div>
                </div>
            </div>
        """

    with st.sidebar:
        st.html(
            f"""
            <div class="portal-sidebar-root">

                <aside class="portal-sidebar-compact" aria-label="Navegação compacta">
                    <div class="portal-sidebar-compact-brand" title="{_safe(APP_CONFIG.APP_NAME)}">
                        <div class="portal-sidebar-compact-brandmark">M</div>
                    </div>

                    <nav class="portal-sidebar-compact-nav">
                        {compact_navigation}
                    </nav>

                    {compact_account}
                </aside>

                <aside class="portal-sidebar-expanded" aria-label="Navegação principal">
                    <div class="portal-sidebar-expanded-brand">
                        <div class="portal-sidebar-expanded-brandmark">M</div>
                        <div class="portal-sidebar-expanded-brand-copy">
                            <div class="portal-sidebar-expanded-organization">
                                {_safe(APP_CONFIG.ORGANIZATION_NAME)}
                            </div>
                            <div class="portal-sidebar-expanded-title">
                                {_safe(APP_CONFIG.APP_NAME)}
                            </div>
                        </div>
                    </div>

                    <div class="portal-sidebar-expanded-label">NAVEGAÇÃO</div>

                    <nav class="portal-sidebar-expanded-nav">
                        {expanded_navigation}
                    </nav>

                    <div class="portal-sidebar-expanded-spacer"></div>

                    <div class="portal-sidebar-expanded-separator"></div>
                    <div class="portal-sidebar-expanded-label portal-sidebar-account-label">
                        CONTA
                    </div>

                    {expanded_account}

                    <div class="portal-sidebar-expanded-footer">
                        Base Comercial HMV
                    </div>
                </aside>

            </div>
            """
        )

        if user and st.button(
            "Sair da conta",
            key="sidebar_logout",
            use_container_width=True,
        ):
            logout()

    return current_page

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator

from nicegui import ui


NAV_ITEMS = (
    ("home", "home", "Início", "/"),
    ("search", "search", "Pesquisa", "/pesquisa"),
    ("operators", "domain", "Operadoras", "/operadoras"),
    ("portals", "vpn_key", "Portais", "/portais"),
    ("documents", "description", "Documentos", "/documentos"),
    ("contacts", "contacts", "Contatos", "/contatos"),
    ("consultants", "support_agent", "Consultores", "/consultores"),
    ("communications", "campaign", "Comunicados", "/comunicados"),
    ("contingencies", "warning_amber", "Contingências", "/contingencias"),
)

ADMIN_ITEMS = (
    ("admin", "settings", "Administração", "/administracao"),
)


TOPBAR_CONTEXT = (
    ("/administracao", "Administração"),
    ("/contingencias", "Contingências"),
    ("/comunicados", "Comunicados"),
    ("/consultores", "Consultores"),
    ("/contatos", "Contatos"),
    ("/documentos", "Documentos"),
    ("/portais", "Portais"),
    ("/operadoras", "Operadoras"),
    ("/pesquisa", "Pesquisa"),
    ("/", "Início"),
)


_SPA_CONTENT_MODE: ContextVar[bool] = ContextVar(
    "portal_spa_content_mode",
    default=False,
)


def _soon(label: str) -> None:
    ui.notify(
        f"{label}: módulo será conectado nas próximas etapas.",
        type="info",
        position="top",
    )


def _initials(name: str, email: str) -> str:
    source = (name or email.split("@", 1)[0]).strip()
    parts = [part for part in source.split() if part]
    if not parts:
        return "HM"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _path_matches(target: str, current_path: str) -> bool:
    if target == "/":
        return current_path == "/"
    return current_path == target or current_path.startswith(f"{target}/")


@dataclass(slots=True)
class PortalNavigationState:
    """Mantém menu e contexto da topbar sem reconstruir o shell."""

    items: list[tuple[str, object]] = field(default_factory=list)
    context_label: object | None = None

    def register(self, target: str, button: object) -> None:
        self.items.append((target, button))

    def bind_context_label(self, label: object) -> None:
        self.context_label = label

    def update(self, current_path: str) -> None:
        path = (current_path or "/").split("?", 1)[0].split("#", 1)[0] or "/"

        for target, button in self.items:
            if _path_matches(target, path):
                button.classes(add="is-active")
            else:
                button.classes(remove="is-active")

        if self.context_label is not None:
            current_label = "Portal Comercial"
            for target, label in TOPBAR_CONTEXT:
                if _path_matches(target, path):
                    current_label = label
                    break
            self.context_label.set_text(current_label)


def _nav_button(
    key: str,
    icon: str,
    label: str,
    target: str | None,
    *,
    navigation: PortalNavigationState,
    mobile: bool = False,
) -> None:
    classes = "portal-mobile-nav-item" if mobile else "portal-nav-item"

    def navigate() -> None:
        if target:
            ui.navigate.to(target)
        else:
            _soon(label)

    button = ui.button(on_click=navigate).props("flat no-caps").classes(classes)
    with button:
        ui.icon(icon).classes("portal-nav-icon")
        ui.label(label).classes("portal-nav-label")

    if target:
        navigation.register(target, button)


def _brand() -> None:
    with ui.row().classes("portal-brand"):
        with ui.element("div").classes("portal-brand-mark"):
            ui.icon("local_hospital")
        with ui.column().classes("portal-brand-copy"):
            ui.label("PORTAL COMERCIAL").classes("portal-brand-title")
            ui.label("Hospital Moinhos de Vento").classes("portal-brand-subtitle")


def _desktop_sidebar(user: dict, navigation: PortalNavigationState) -> None:
    name = str(user.get("name") or "").strip() or "Usuário institucional"
    email = str(user.get("email") or "").strip()
    role = "Administrador" if user.get("role") == "admin" else "Usuário"

    with ui.element("aside").classes("portal-sidebar"):
        _brand()

        ui.label("NAVEGAÇÃO").classes("portal-nav-section-label")
        with ui.column().classes("portal-nav-list"):
            for key, icon, label, target in NAV_ITEMS:
                _nav_button(
                    key,
                    icon,
                    label,
                    target,
                    navigation=navigation,
                )

        with ui.element("div").classes("portal-sidebar-spacer"):
            pass

        if user.get("role") == "admin":
            ui.label("GESTÃO").classes("portal-nav-section-label")
            with ui.column().classes("portal-nav-list"):
                for key, icon, label, target in ADMIN_ITEMS:
                    _nav_button(
                        key,
                        icon,
                        label,
                        target,
                        navigation=navigation,
                    )

        with ui.row().classes("portal-profile"):
            ui.avatar(_initials(name, email)).classes("portal-profile-avatar")
            with ui.column().classes("portal-profile-copy"):
                ui.label(name).classes("portal-profile-name")
                ui.label(role).classes("portal-profile-role")
            with ui.link(target="/logout").classes("portal-logout-link"):
                ui.icon("logout").classes("portal-profile-more")


def _topbar(user: dict, navigation: PortalNavigationState) -> None:
    name = str(user.get("name") or "").strip()
    email = str(user.get("email") or "").strip()

    def submit_global_search() -> None:
        query = str(global_search.value or "").strip()
        if len(query) < 2:
            ui.notify(
                "Digite pelo menos 2 caracteres para pesquisar.",
                type="info",
                position="top",
            )
            global_search.run_method("focus")
            return

        ui.context.client.storage["portal_pending_search_query"] = query
        global_search.value = ""
        ui.navigate.to("/pesquisa")

    with ui.element("header").classes("portal-topbar"):
        with ui.row().classes("portal-mobile-brand"):
            with ui.element("div").classes("portal-mobile-brand-mark"):
                ui.icon("local_hospital")
            ui.label("Portal Comercial").classes("portal-mobile-brand-title")

        with ui.row().classes("portal-topbar-context"):
            ui.icon("chevron_right").classes("portal-topbar-context-icon")
            context_label = ui.label("Início").classes("portal-topbar-context-label")
            navigation.bind_context_label(context_label)

        with ui.element("div").classes("portal-topbar-spacer"):
            pass

        with ui.element("div").classes("portal-topbar-search"):
            ui.icon("search").classes("portal-topbar-search-icon")
            global_search = ui.input(
                placeholder="Pesquisar no portal..."
            ).props(
                "borderless dense autocomplete='off'"
            ).classes("portal-topbar-search-input")
            global_search.on("keydown.enter", submit_global_search)
            ui.button(
                icon="arrow_forward",
                on_click=submit_global_search,
            ).props(
                "flat round dense aria-label='Pesquisar'"
            ).classes("portal-topbar-search-button")

        with ui.element("div").classes("portal-topbar-user"):
            ui.avatar(_initials(name, email)).classes("portal-topbar-avatar")


def _mobile_navigation(navigation: PortalNavigationState) -> None:
    visible = NAV_ITEMS[:5]
    with ui.element("nav").classes("portal-mobile-nav"):
        for key, icon, label, target in visible:
            _nav_button(
                key,
                icon,
                label,
                target,
                navigation=navigation,
                mobile=True,
            )


def _page_header(
    *,
    page_title: str,
    page_eyebrow: str,
    page_description: str,
) -> None:
    if not page_title:
        return

    with ui.element("section").classes("portal-page-header"):
        if page_eyebrow:
            ui.label(page_eyebrow).classes("portal-page-eyebrow")
        ui.label(page_title).classes("portal-page-title")
        if page_description:
            ui.label(page_description).classes("portal-page-description")


@contextmanager
def spa_content_mode() -> Iterator[None]:
    """Evita recriar sidebar/topbar quando a rota é trocada via ui.sub_pages."""
    token = _SPA_CONTENT_MODE.set(True)
    try:
        yield
    finally:
        _SPA_CONTENT_MODE.reset(token)


@contextmanager
def portal_shell(*, user: dict) -> Iterator[PortalNavigationState]:
    """Shell persistente da aplicação.

    Sidebar, topbar e navegação móvel são criadas uma única vez por cliente.
    Apenas o conteúdo de ``ui.sub_pages`` é substituído durante a navegação.
    """
    navigation = PortalNavigationState()

    with ui.element("div").classes("portal-app-shell portal-spa-shell"):
        _desktop_sidebar(user, navigation)

        with ui.element("div").classes("portal-main-shell"):
            _topbar(user, navigation)

            with ui.element("main").classes("portal-content portal-spa-content"):
                yield navigation

        _mobile_navigation(navigation)


@contextmanager
def portal_layout(
    *,
    user: dict,
    active: str = "home",
    page_title: str = "",
    page_eyebrow: str = "",
    page_description: str = "",
) -> Iterator[None]:
    """Layout compartilhado.

    No modo SPA, o shell já existe e esta função renderiza somente o cabeçalho
    e o conteúdo da subpágina. Fora do modo SPA mantém compatibilidade com
    qualquer uso isolado existente.
    """
    if _SPA_CONTENT_MODE.get():
        _page_header(
            page_title=page_title,
            page_eyebrow=page_eyebrow,
            page_description=page_description,
        )
        yield
        return

    navigation = PortalNavigationState()

    with ui.element("div").classes("portal-app-shell"):
        _desktop_sidebar(user, navigation)

        with ui.element("div").classes("portal-main-shell"):
            _topbar(user, navigation)

            with ui.element("main").classes("portal-content"):
                _page_header(
                    page_title=page_title,
                    page_eyebrow=page_eyebrow,
                    page_description=page_description,
                )
                yield

        _mobile_navigation(navigation)

    # Compatibilidade visual quando uma página ainda for aberta isoladamente.
    target_by_key = {
        key: target for key, _icon, _label, target in NAV_ITEMS + ADMIN_ITEMS
    }
    navigation.update(target_by_key.get(active, "/"))

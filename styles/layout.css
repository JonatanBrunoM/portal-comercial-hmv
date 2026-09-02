from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from nicegui import ui


NAV_ITEMS = (
    ("home", "home", "Início", "/"),
    ("search", "search", "Pesquisa", None),
    ("operators", "domain", "Operadoras", "/operadoras"),
    ("portals", "vpn_key", "Portais", "/portais"),
    ("documents", "description", "Documentos", None),
    ("contacts", "contacts", "Contatos", None),
    ("consultants", "support_agent", "Consultores", None),
    ("communications", "campaign", "Comunicados", None),
    ("contingencies", "warning_amber", "Contingências", None),
)

ADMIN_ITEMS = (
    ("admin", "settings", "Administração", None),
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


def _nav_button(
    key: str,
    icon: str,
    label: str,
    target: str | None,
    *,
    active: str,
    mobile: bool = False,
) -> None:
    classes = "portal-mobile-nav-item" if mobile else "portal-nav-item"
    if key == active:
        classes += " is-active"

    def navigate() -> None:
        if target:
            ui.navigate.to(target)
        else:
            _soon(label)

    with ui.button(on_click=navigate).props("flat no-caps").classes(classes):
        ui.icon(icon).classes("portal-nav-icon")
        ui.label(label).classes("portal-nav-label")


def _brand() -> None:
    with ui.row().classes("portal-brand"):
        with ui.element("div").classes("portal-brand-mark"):
            ui.icon("local_hospital")
        with ui.column().classes("portal-brand-copy"):
            ui.label("PORTAL COMERCIAL").classes("portal-brand-title")
            ui.label("Hospital Moinhos de Vento").classes("portal-brand-subtitle")


def _desktop_sidebar(active: str, user: dict) -> None:
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
                    active=active,
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
                        active=active,
                    )

        with ui.row().classes("portal-profile"):
            ui.avatar(_initials(name, email)).classes("portal-profile-avatar")
            with ui.column().classes("portal-profile-copy"):
                ui.label(name).classes("portal-profile-name")
                ui.label(role).classes("portal-profile-role")
            with ui.link(target="/logout").classes("portal-logout-link"):
                ui.icon("logout").classes("portal-profile-more")


def _topbar(user: dict) -> None:
    name = str(user.get("name") or "").strip()
    email = str(user.get("email") or "").strip()

    with ui.element("header").classes("portal-topbar"):
        with ui.row().classes("portal-mobile-brand"):
            with ui.element("div").classes("portal-mobile-brand-mark"):
                ui.icon("local_hospital")
            ui.label("Portal Comercial").classes("portal-mobile-brand-title")

        with ui.element("div").classes("portal-topbar-spacer"):
            pass

        with ui.button(on_click=lambda: _soon("Ajuda")).props(
            "flat round aria-label='Ajuda'"
        ).classes("portal-icon-button"):
            ui.icon("help_outline")

        with ui.button(on_click=lambda: _soon("Notificações")).props(
            "flat round aria-label='Notificações'"
        ).classes("portal-icon-button"):
            ui.icon("notifications_none")

        ui.avatar(_initials(name, email)).classes("portal-topbar-avatar")


def _mobile_navigation(active: str) -> None:
    visible = NAV_ITEMS[:5]
    with ui.element("nav").classes("portal-mobile-nav"):
        for key, icon, label, target in visible:
            _nav_button(
                key,
                icon,
                label,
                target,
                active=active,
                mobile=True,
            )


@contextmanager
def portal_layout(
    *,
    user: dict,
    active: str = "home",
    page_title: str = "",
    page_eyebrow: str = "",
    page_description: str = "",
) -> Iterator[None]:
    """Estrutura compartilhada por todas as páginas autenticadas."""
    with ui.element("div").classes("portal-app-shell"):
        _desktop_sidebar(active, user)

        with ui.element("div").classes("portal-main-shell"):
            _topbar(user)

            with ui.element("main").classes("portal-content"):
                if page_title:
                    with ui.element("section").classes("portal-page-header"):
                        if page_eyebrow:
                            ui.label(page_eyebrow).classes("portal-page-eyebrow")
                        ui.label(page_title).classes("portal-page-title")
                        if page_description:
                            ui.label(page_description).classes(
                                "portal-page-description"
                            )

                yield

        _mobile_navigation(active)

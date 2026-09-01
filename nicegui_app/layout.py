from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterator

from nicegui import ui


NAV_ITEMS = (
    ("home", "home", "Início"),
    ("search", "search", "Pesquisa"),
    ("operators", "domain", "Operadoras"),
    ("portals", "vpn_key", "Portais"),
    ("documents", "description", "Documentos"),
    ("contacts", "contacts", "Contatos"),
    ("consultants", "support_agent", "Consultores"),
    ("communications", "campaign", "Comunicados"),
    ("contingencies", "warning_amber", "Contingências"),
)

ADMIN_ITEMS = (
    ("admin", "settings", "Administração"),
)


def _soon(label: str) -> Callable[[], None]:
    def handler() -> None:
        ui.notify(
            f"{label}: módulo será conectado nas próximas etapas.",
            type="info",
            position="top",
        )

    return handler


def _nav_button(
    key: str,
    icon: str,
    label: str,
    *,
    active: str,
    mobile: bool = False,
) -> None:
    classes = "portal-mobile-nav-item" if mobile else "portal-nav-item"
    if key == active:
        classes += " is-active"

    with ui.button(on_click=_soon(label)).props("flat no-caps").classes(classes):
        ui.icon(icon).classes("portal-nav-icon")
        ui.label(label).classes("portal-nav-label")


def _brand() -> None:
    with ui.row().classes("portal-brand"):
        with ui.element("div").classes("portal-brand-mark"):
            ui.icon("local_hospital")
        with ui.column().classes("portal-brand-copy"):
            ui.label("PORTAL COMERCIAL").classes("portal-brand-title")
            ui.label("Hospital Moinhos de Vento").classes("portal-brand-subtitle")


def _desktop_sidebar(active: str) -> None:
    with ui.element("aside").classes("portal-sidebar"):
        _brand()

        ui.label("NAVEGAÇÃO").classes("portal-nav-section-label")
        with ui.column().classes("portal-nav-list"):
            for key, icon, label in NAV_ITEMS:
                _nav_button(key, icon, label, active=active)

        with ui.element("div").classes("portal-sidebar-spacer"):
            pass

        ui.label("GESTÃO").classes("portal-nav-section-label")
        with ui.column().classes("portal-nav-list"):
            for key, icon, label in ADMIN_ITEMS:
                _nav_button(key, icon, label, active=active)

        with ui.row().classes("portal-profile"):
            ui.avatar("JB").classes("portal-profile-avatar")
            with ui.column().classes("portal-profile-copy"):
                ui.label("Usuário institucional").classes("portal-profile-name")
                ui.label("Ambiente de POC").classes("portal-profile-role")
            ui.icon("more_horiz").classes("portal-profile-more")


def _topbar() -> None:
    with ui.element("header").classes("portal-topbar"):
        with ui.row().classes("portal-mobile-brand"):
            with ui.element("div").classes("portal-mobile-brand-mark"):
                ui.icon("local_hospital")
            ui.label("Portal Comercial").classes("portal-mobile-brand-title")

        with ui.element("div").classes("portal-topbar-spacer"):
            pass

        with ui.button(on_click=_soon("Ajuda")).props(
            "flat round aria-label='Ajuda'"
        ).classes("portal-icon-button"):
            ui.icon("help_outline")

        with ui.button(on_click=_soon("Notificações")).props(
            "flat round aria-label='Notificações'"
        ).classes("portal-icon-button"):
            ui.icon("notifications_none")

        ui.avatar("JB").classes("portal-topbar-avatar")


def _mobile_navigation(active: str) -> None:
    visible = NAV_ITEMS[:5]
    with ui.element("nav").classes("portal-mobile-nav"):
        for key, icon, label in visible:
            _nav_button(key, icon, label, active=active, mobile=True)


@contextmanager
def portal_layout(
    *,
    active: str = "home",
    page_title: str = "",
    page_eyebrow: str = "",
    page_description: str = "",
) -> Iterator[None]:
    """Estrutura compartilhada por todas as páginas NiceGUI."""
    with ui.element("div").classes("portal-app-shell"):
        _desktop_sidebar(active)

        with ui.element("div").classes("portal-main-shell"):
            _topbar()

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

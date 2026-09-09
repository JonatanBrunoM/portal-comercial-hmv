from __future__ import annotations

from nicegui import ui


_VARIANTS = {"home", "search", "operators", "portals", "documents", "contacts", "consultants", "communications", "contingencies"}


def render_hero_art(*, variant: str, icon: str) -> None:
    """Renderiza a ilustração decorativa padronizada dos heroes."""
    normalized = variant if variant in _VARIANTS else "home"
    with ui.element("div").classes(f"portal-hero-art portal-hero-art--{normalized}").props("aria-hidden=true"):
        ui.element("span").classes("portal-hero-art-orbit orbit-one")
        ui.element("span").classes("portal-hero-art-orbit orbit-two")
        ui.element("span").classes("portal-hero-art-arc arc-one")
        ui.element("span").classes("portal-hero-art-arc arc-two")
        for index in range(1, 6):
            ui.element("span").classes(f"portal-hero-art-node node-{index}")
        with ui.element("div").classes("portal-hero-art-core"):
            ui.icon(icon)

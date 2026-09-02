from __future__ import annotations

from pathlib import Path

from nicegui import ui


BASE_DIR = Path(__file__).resolve().parents[1]

STYLE_ORDER = (
    "styles/nicegui/tokens.css",
    "styles/nicegui/base.css",
    "styles/nicegui/layout.css",
    "styles/nicegui/components.css",
    "styles/nicegui/auth.css",
    "styles/nicegui/operators.css",
    "styles/nicegui/portals.css",
    "styles/nicegui/documents.css",
    "styles/nicegui/contacts.css",
    "styles/nicegui/consultants.css",
    "styles/nicegui/communications.css",
    "styles/nicegui/contingencies.css",
    "styles/nicegui/search.css",
    "styles/nicegui/admin.css",
)


def apply_theme() -> None:
    """Carrega o design system NiceGUI em ordem determinística."""
    css = "\n\n".join(
        (BASE_DIR / relative_path).read_text(encoding="utf-8")
        for relative_path in STYLE_ORDER
    )
    ui.add_css(css)

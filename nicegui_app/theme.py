from __future__ import annotations

from pathlib import Path

from nicegui import ui


BASE_DIR = Path(__file__).resolve().parents[1]

STYLE_ORDER = (
    "styles/nicegui/tokens.css",
    "styles/nicegui/base.css",
    "styles/nicegui/layout.css",
    "styles/nicegui/components.css",
    "styles/nicegui/data.css",
    "styles/nicegui/auth.css",
    "styles/nicegui/components_auth_patch.css",
)


def apply_theme() -> None:
    """Carrega o design system NiceGUI em ordem determinística."""
    css = "\n\n".join(
        (BASE_DIR / relative_path).read_text(encoding="utf-8")
        for relative_path in STYLE_ORDER
    )
    ui.add_css(css)

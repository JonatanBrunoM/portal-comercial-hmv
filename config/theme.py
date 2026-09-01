from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STYLE_ORDER = (
    "styles/tokens.css",
    "styles/base.css",
    "styles/layout.css",
    "styles/streamlit.css",
    "styles/components/buttons.css",
    "styles/components/forms.css",
    "styles/components/hero.css",
    "styles/components/cards.css",
    "styles/components/search.css",
    "styles/components/tables.css",
    "styles/components/alerts.css",
    "styles/components/sidebar.css",
    "styles/pages/home.css",
    "styles/pages/operadoras.css",
    "styles/pages/admin.css",
    "styles/pages/forum.css",
)


def _read_stylesheet(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path

    if not path.exists():
        raise RuntimeError(f"Arquivo de estilo não encontrado: {relative_path}")

    return path.read_text(encoding="utf-8")


def build_stylesheet() -> str:
    """Monta a folha de estilos na ordem oficial do design system."""

    sections = []

    for relative_path in STYLE_ORDER:
        css = _read_stylesheet(relative_path).strip()
        sections.append(f"/* source: {relative_path} */\n{css}")

    return "\n\n".join(sections)


def apply_theme() -> None:
    """Carrega e injeta o design system uma única vez na aplicação."""

    css = build_stylesheet()
    st.html(f"<style>{css}</style>")

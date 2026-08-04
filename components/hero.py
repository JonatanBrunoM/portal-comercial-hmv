import html

import streamlit as st


def render_hero(
    title: str,
    description: str,
    eyebrow: str | None = None,
) -> None:
    """Renderiza o cabeçalho principal de uma página."""

    safe_title = html.escape(title)
    safe_description = html.escape(description)
    safe_eyebrow = html.escape(eyebrow) if eyebrow else ""

    eyebrow_html = (
        f'<div class="portal-hero-eyebrow">{safe_eyebrow}</div>'
        if safe_eyebrow
        else ""
    )

    hero_html = f"""
    <section class="portal-hero">
        {eyebrow_html}
        <h1 class="portal-hero-title">{safe_title}</h1>
        <p class="portal-hero-description">{safe_description}</p>
    </section>
    """

    st.html(hero_html)

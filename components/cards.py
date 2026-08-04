import html

import streamlit as st


def render_metric_card(
    title: str,
    value: str | int,
    description: str,
    icon: str,
) -> None:
    """Renderiza um card resumido de indicador."""

    safe_title = html.escape(str(title))
    safe_value = html.escape(str(value))
    safe_description = html.escape(str(description))
    safe_icon = html.escape(icon)

    card_html = f"""
    <article class="portal-metric-card">
        <div class="portal-metric-header">
            <div class="portal-metric-label">{safe_title}</div>
            <div class="portal-metric-icon">{safe_icon}</div>
        </div>

        <div class="portal-metric-value">{safe_value}</div>
        <div class="portal-metric-description">{safe_description}</div>
    </article>
    """

    st.html(card_html)


def render_module_card(
    title: str,
    description: str,
    icon: str,
    button_key: str,
) -> bool:
    """Renderiza um card de acesso rápido."""

    safe_title = html.escape(title)
    safe_description = html.escape(description)
    safe_icon = html.escape(icon)

    with st.container(border=True):
        module_html = f"""
        <div class="portal-module-card">
            <div class="portal-module-icon">{safe_icon}</div>

            <div class="portal-module-content">
                <div class="portal-module-title">{safe_title}</div>
                <div class="portal-module-description">
                    {safe_description}
                </div>
            </div>
        </div>
        """

        st.html(module_html)

        return st.button(
            "Acessar",
            key=button_key,
            use_container_width=True,
        )

from __future__ import annotations

import html

import streamlit as st

from core.operadoras_service import OperadoraSummary
from ui.icons import icon


def render_operadora_card(
    operadora: OperadoraSummary,
) -> bool:
    """Renderiza o card resumido de uma operadora."""

    safe_name = html.escape(
        operadora.short_name
    )

    safe_full_name = html.escape(
        operadora.name
    )

    safe_status = html.escape(
        operadora.status or "Sem status"
    )

    card_html = f"""
    <article class="portal-operadora-card">
        <div class="portal-operadora-card-top">
            <div class="portal-operadora-icon">
                {icon("building")}
            </div>

            <div class="portal-operadora-status">
                {safe_status}
            </div>
        </div>

        <div class="portal-operadora-name">
            {safe_name}
        </div>

        <div class="portal-operadora-full-name">
            {safe_full_name}
        </div>

        <div class="portal-operadora-plans">
            <strong>{operadora.plans_count}</strong>
            plano(s) cadastrado(s)
        </div>
    </article>
    """

    with st.container(border=True):
        st.html(card_html)

        return st.button(
            "Abrir operadora",
            key=(
                "open_operator_"
                f"{operadora.operator_id}"
            ),
            use_container_width=True,
        )

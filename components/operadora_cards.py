from __future__ import annotations

import html

import streamlit as st

from core.operadoras_service import OperadoraSummary
from ui.icons import icon


def render_operadora_card(
    operadora: OperadoraSummary,
) -> bool:
    """Renderiza o card resumido de uma operadora."""

    safe_name = html.escape(operadora.short_name)
    safe_full_name = html.escape(operadora.name)
    safe_status = html.escape(operadora.status or "Sem status")
    safe_consultant = html.escape(operadora.consultant or "Consultor não vinculado")

    plan_label = "plano cadastrado" if operadora.plans_count == 1 else "planos cadastrados"

    card_html = f"""
    <article class="portal-operadora-card">
        <div class="portal-operadora-card-top">
            <div class="portal-operadora-icon" aria-hidden="true">
                {icon("building")}
            </div>
            <div class="portal-operadora-status">{safe_status}</div>
        </div>

        <div class="portal-operadora-name">{safe_name}</div>
        <div class="portal-operadora-full-name">{safe_full_name}</div>

        <div class="portal-operadora-card-divider"></div>

        <div class="portal-operadora-card-meta">
            <div class="portal-operadora-meta-item">
                <span class="portal-operadora-meta-icon">{icon("clipboard")}</span>
                <span><strong>{operadora.plans_count}</strong> {plan_label}</span>
            </div>
            <div class="portal-operadora-meta-item portal-operadora-meta-consultant">
                <span class="portal-operadora-meta-icon">{icon("user")}</span>
                <span>{safe_consultant}</span>
            </div>
        </div>
    </article>
    """

    with st.container(border=True):
        st.html(card_html)

        return st.button(
            "Acessar central da operadora",
            key=f"open_operator_{operadora.operator_id}",
            use_container_width=True,
            type="primary",
        )

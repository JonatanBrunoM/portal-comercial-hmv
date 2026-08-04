from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from components.operadora_cards import (
    render_operadora_card,
)
from core.operadoras_service import (
    get_operadora_by_id,
    get_operadora_planos,
    search_operadoras,
)


def _safe_text(
    row: pd.Series,
    column: str,
) -> str:
    if column not in row.index:
        return ""

    value = row[column]

    if pd.isna(value):
        return ""

    return str(value).strip()


def render_operadora_detail(
    operator_id: str,
) -> None:
    """Renderiza a ficha inicial de uma operadora."""

    operadora = get_operadora_by_id(
        operator_id
    )

    if operadora is None:
        st.error(
            "Não foi possível localizar essa operadora."
        )

        if st.button(
            "Voltar para operadoras",
            use_container_width=False,
        ):
            st.session_state.pop(
                "selected_operator_id",
                None,
            )
            st.rerun()

        return

    top_left, top_right = st.columns(
        [5, 1]
    )

    with top_left:
        render_hero(
            eyebrow="Ficha da operadora",
            title=operadora.short_name,
            description=(
                operadora.name
                if operadora.name
                != operadora.short_name
                else (
                    "Consulte os planos e informações "
                    "relacionadas a esta operadora."
                )
            ),
        )

    with top_right:
        if st.button(
            "← Voltar",
            use_container_width=True,
        ):
            st.session_state.pop(
                "selected_operator_id",
                None,
            )
            st.rerun()

    metric_1, metric_2, metric_3 = st.columns(
        3
    )

    metric_1.metric(
        "Planos cadastrados",
        operadora.plans_count,
    )

    metric_2.metric(
        "Status",
        operadora.status or "Não informado",
    )

    metric_3.metric(
        "Consultor",
        operadora.consultant or "Não definido",
    )

    if operadora.observations:
        with st.expander(
            "Observações da operadora",
            expanded=False,
        ):
            st.write(
                operadora.observations
            )

    st.markdown("## Planos vinculados")

    planos = get_operadora_planos(
        operator_id
    )

    if planos.empty:
        st.info(
            "Nenhum plano ativo foi encontrado "
            "para esta operadora."
        )
        return

    for _, plano in planos.iterrows():
        plan_name = (
            _safe_text(
                plano,
                "Nome padronizado",
            )
            or _safe_text(
                plano,
                "Plano",
            )
            or "Plano sem nome"
        )

        unit = (
            _safe_text(
                plano,
                "Unidade",
            )
            or "Unidade não informada"
        )

        plan_type = (
            _safe_text(
                plano,
                "Tipo do plano",
            )
            or "Tipo não informado"
        )

        with st.expander(
            f"📋 {plan_name}",
            expanded=False,
        ):
            col_1, col_2 = st.columns(2)

            col_1.markdown(
                f"**Unidade:** {unit}"
            )

            col_2.markdown(
                f"**Tipo:** {plan_type}"
            )

            observation = _safe_text(
                plano,
                "Observação resumida",
            )

            if observation:
                st.markdown(
                    f"**Observação:** {observation}"
                )


def render_operadoras() -> None:
    """Renderiza a listagem ou ficha de operadoras."""

    selected_operator_id = (
        st.session_state.get(
            "selected_operator_id"
        )
    )

    if selected_operator_id:
        render_operadora_detail(
            selected_operator_id
        )
        return

    render_hero(
        eyebrow="Convênios e planos",
        title="Operadoras",
        description=(
            "Encontre uma operadora e consulte seus "
            "planos e informações relacionadas."
        ),
    )

    query = st.text_input(
        label="Pesquisar operadora",
        placeholder=(
            "Digite o nome da operadora..."
        ),
        key="operator_search_query",
    )

    with st.spinner(
        "Carregando operadoras..."
    ):
        operadoras = search_operadoras(
            query
        )

    st.caption(
        f"{len(operadoras)} operadora(s) encontrada(s)."
    )

    if not operadoras:
        st.info(
            "Nenhuma operadora foi encontrada "
            "para essa pesquisa."
        )
        return

    columns_per_row = 3

    for start in range(
        0,
        len(operadoras),
        columns_per_row,
    ):
        columns = st.columns(
            columns_per_row
        )

        batch = operadoras[
            start : start + columns_per_row
        ]

        for column, operadora in zip(
            columns,
            batch,
        ):
            with column:
                if render_operadora_card(
                    operadora
                ):
                    st.session_state[
                        "selected_operator_id"
                    ] = operadora.operator_id

                    st.rerun()

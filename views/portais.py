from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import (
    get_operadoras,
    get_planos,
    get_portais,
)
from utils.formatting import normalize_text


def _safe_value(
    row: pd.Series,
    column: str,
) -> str:
    """Retorna um valor textual sem gerar erro."""

    if column not in row.index:
        return ""

    value = row[column]

    if pd.isna(value):
        return ""

    return str(value).strip()


def _safe_url(value: object) -> str:
    """Retorna somente URLs HTTP ou HTTPS válidas."""

    url = str(value or "").strip()

    if not url:
        return ""

    if not re.match(
        r"^https?://",
        url,
        flags=re.IGNORECASE,
    ):
        return ""

    return url


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _build_portais_dataset() -> pd.DataFrame:
    """
    Monta a base de portais com os nomes das operadoras
    e dos planos.
    """

    portais = get_portais()
    operadoras = get_operadoras()
    planos = get_planos()

    if portais is None or portais.empty:
        return pd.DataFrame()

    result = portais.copy()

    if (
        not operadoras.empty
        and "ID Operadora" in operadoras.columns
        and "ID Operadora" in result.columns
    ):
        operator_name_column = next(
            (
                column
                for column in [
                    "Nome curto",
                    "Operadora",
                ]
                if column in operadoras.columns
            ),
            None,
        )

        if operator_name_column:
            operator_lookup = (
                operadoras[
                    [
                        "ID Operadora",
                        operator_name_column,
                    ]
                ]
                .drop_duplicates(
                    subset=["ID Operadora"]
                )
                .rename(
                    columns={
                        operator_name_column: (
                            "Nome Operadora"
                        )
                    }
                )
            )

            result = result.merge(
                operator_lookup,
                how="left",
                on="ID Operadora",
            )

    if "Nome Operadora" not in result.columns:
        result["Nome Operadora"] = ""

    if (
        not planos.empty
        and "ID Plano" in planos.columns
        and "ID Plano" in result.columns
    ):
        plan_name_column = next(
            (
                column
                for column in [
                    "Nome padronizado",
                    "Plano",
                ]
                if column in planos.columns
            ),
            None,
        )

        if plan_name_column:
            plan_lookup = (
                planos[
                    [
                        "ID Plano",
                        plan_name_column,
                    ]
                ]
                .drop_duplicates(
                    subset=["ID Plano"]
                )
                .rename(
                    columns={
                        plan_name_column: "Nome Plano"
                    }
                )
            )

            result = result.merge(
                plan_lookup,
                how="left",
                on="ID Plano",
            )

    if "Nome Plano" not in result.columns:
        result["Nome Plano"] = ""

    # Não exibe registros marcados explicitamente como inativos.
    if "Status" in result.columns:
        normalized_status = (
            result["Status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        result = result[
            ~normalized_status.eq("inativo")
        ]

    result["Nome Operadora"] = (
        result["Nome Operadora"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    result["Nome Plano"] = (
        result["Nome Plano"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    sort_columns = [
        column
        for column in [
            "Nome Operadora",
            "Nome do portal",
            "Nome Plano",
        ]
        if column in result.columns
    ]

    if sort_columns:
        result = result.sort_values(
            by=sort_columns,
            na_position="last",
        )

    return result.reset_index(drop=True)


def _filter_portais(
    dataframe: pd.DataFrame,
    query: str,
    operator_name: str,
    plan_name: str,
    unit: str,
) -> pd.DataFrame:
    """Aplica os filtros selecionados pelo usuário."""

    filtered = dataframe.copy()

    if operator_name != "Todas":
        filtered = filtered[
            filtered["Nome Operadora"]
            .fillna("")
            .astype(str)
            .eq(operator_name)
        ]

    if plan_name != "Todos":
        filtered = filtered[
            filtered["Nome Plano"]
            .fillna("")
            .astype(str)
            .eq(plan_name)
        ]

    if unit != "Todas":
        filtered = filtered[
            filtered["Unidade"]
            .fillna("")
            .astype(str)
            .eq(unit)
        ]

    normalized_query = normalize_text(query)

    if normalized_query:
        searchable_columns = [
            column
            for column in [
                "Nome do portal",
                "Tipo",
                "URL",
                "Unidade",
                "Instrução de acesso",
                "Observações",
                "Nome Operadora",
                "Nome Plano",
            ]
            if column in filtered.columns
        ]

        if searchable_columns:
            searchable_text = (
                filtered[searchable_columns]
                .fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
                .map(normalize_text)
            )

            filtered = filtered[
                searchable_text.str.contains(
                    normalized_query,
                    regex=False,
                    na=False,
                )
            ]

    return filtered.reset_index(drop=True)


def _render_portal(
    portal: pd.Series,
    position: int,
) -> None:
    """Renderiza um registro de portal."""

    portal_name = (
        _safe_value(
            portal,
            "Nome do portal",
        )
        or "Portal sem nome"
    )

    operator_name = (
        _safe_value(
            portal,
            "Nome Operadora",
        )
        or "Operadora não identificada"
    )

    plan_name = _safe_value(
        portal,
        "Nome Plano",
    )

    portal_type = _safe_value(
        portal,
        "Tipo",
    )

    unit = _safe_value(
        portal,
        "Unidade",
    )

    requires_login = _safe_value(
        portal,
        "Exige login",
    )

    instructions = _safe_value(
        portal,
        "Instrução de acesso",
    )

    observations = _safe_value(
        portal,
        "Observações",
    )

    url = _safe_url(
        _safe_value(
            portal,
            "URL",
        )
    )

    portal_id = (
        _safe_value(
            portal,
            "ID Portal",
        )
        or str(position)
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### 🌐 {portal_name}"
        )

        st.caption(
            operator_name
        )

        detail_1, detail_2 = st.columns(2)

        detail_1.markdown(
            "**Plano:** "
            f"{plan_name or 'Não informado'}"
        )

        detail_2.markdown(
            "**Unidade:** "
            f"{unit or 'Não informada'}"
        )

        if portal_type:
            st.markdown(
                f"**Tipo:** {portal_type}"
            )

        if requires_login:
            st.markdown(
                f"**Exige login:** {requires_login}"
            )

        if instructions:
            with st.expander(
                "Orientação de acesso",
                expanded=False,
            ):
                st.write(instructions)

        if observations:
            st.caption(
                observations
            )

        if url:
            st.link_button(
                "Abrir portal",
                url,
                use_container_width=True,
            )

        else:
            st.button(
                "Link indisponível",
                key=f"portal_unavailable_{portal_id}",
                disabled=True,
                use_container_width=True,
            )


def render_portais() -> None:
    """Renderiza a página geral de portais."""

    render_hero(
        eyebrow="Acessos e sistemas externos",
        title="Portais",
        description=(
            "Encontre os portais utilizados para "
            "elegibilidade, autorizações e demais "
            "processos das operadoras."
        ),
    )

    try:
        with st.spinner(
            "Carregando portais..."
        ):
            dataframe = _build_portais_dataset()

    except RuntimeError:
        st.error(
            "Não foi possível carregar os portais "
            "neste momento."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhum portal foi encontrado na base."
        )
        return

    query = st.text_input(
        label="Pesquisar portais",
        placeholder=(
            "Pesquise pelo portal, operadora, plano "
            "ou finalidade..."
        ),
        key="portais_search_query",
    )

    operator_options = sorted(
        value
        for value in dataframe[
            "Nome Operadora"
        ].dropna().astype(str).unique()
        if value.strip()
    )

    selected_operator = st.selectbox(
        label="Operadora",
        options=[
            "Todas",
            *operator_options,
        ],
        key="portais_operator_filter",
    )

    operator_filtered = dataframe

    if selected_operator != "Todas":
        operator_filtered = dataframe[
            dataframe["Nome Operadora"].eq(
                selected_operator
            )
        ]

    plan_options = sorted(
        value
        for value in operator_filtered[
            "Nome Plano"
        ].dropna().astype(str).unique()
        if value.strip()
    )

    unit_options = []

    if "Unidade" in operator_filtered.columns:
        unit_options = sorted(
            value
            for value in operator_filtered[
                "Unidade"
            ].dropna().astype(str).unique()
            if value.strip()
        )

    filter_1, filter_2 = st.columns(2)

    with filter_1:
        selected_plan = st.selectbox(
            label="Plano",
            options=[
                "Todos",
                *plan_options,
            ],
            key="portais_plan_filter",
        )

    with filter_2:
        selected_unit = st.selectbox(
            label="Unidade",
            options=[
                "Todas",
                *unit_options,
            ],
            key="portais_unit_filter",
        )

    filtered = _filter_portais(
        dataframe=dataframe,
        query=query,
        operator_name=selected_operator,
        plan_name=selected_plan,
        unit=selected_unit,
    )

    st.caption(
        f"{len(filtered)} portal(is) encontrado(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhum portal corresponde aos filtros "
            "selecionados."
        )
        return

    columns_per_row = 2

    for start in range(
        0,
        len(filtered),
        columns_per_row,
    ):
        columns = st.columns(
            columns_per_row
        )

        batch = filtered.iloc[
            start : start + columns_per_row
        ]

        for column, (
            index,
            portal,
        ) in zip(
            columns,
            batch.iterrows(),
        ):
            with column:
                _render_portal(
                    portal=portal,
                    position=index,
                )

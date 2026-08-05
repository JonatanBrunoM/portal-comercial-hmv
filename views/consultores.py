from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.sheets_service import (
    read_worksheet,
)
from utils.formatting import normalize_text


CONSULTORES_SHEET = "12_CONSULTORES"
CARTEIRAS_SHEET = "13_CARTEIRAS"


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


def _is_email(value: str) -> bool:
    """Valida um endereço de e-mail em formato básico."""

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value.strip(),
        )
    )


def _clean_phone(value: str) -> str:
    """Mantém somente os caracteres necessários para telefone."""

    return re.sub(
        r"[^\d+]",
        "",
        value,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _build_consultores_dataset() -> pd.DataFrame:
    """
    Une consultores e carteiras em uma única base.
    """

    consultores = read_worksheet(
        worksheet=CONSULTORES_SHEET,
        ttl=1800,
    )

    carteiras = read_worksheet(
        worksheet=CARTEIRAS_SHEET,
        ttl=1800,
    )

    if consultores is None or consultores.empty:
        return pd.DataFrame()

    result = consultores.copy()

    required_consultor_columns = [
        "ID Consultor",
        "Nome",
        "Cargo",
        "E-mail",
        "Telefone",
        "Status",
        "Observações",
    ]

    for column in required_consultor_columns:
        if column not in result.columns:
            result[column] = ""

        result[column] = (
            result[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    if (
        carteiras is not None
        and not carteiras.empty
        and "ID Consultor" in carteiras.columns
    ):
        carteira_columns = [
            "ID Consultor",
            "Operadora",
            "Plano",
            "Segmento",
            "Observações",
        ]

        for column in carteira_columns:
            if column not in carteiras.columns:
                carteiras[column] = ""

            carteiras[column] = (
                carteiras[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        grouped_carteiras = (
            carteiras.groupby(
                "ID Consultor",
                dropna=False,
            )
            .agg(
                {
                    "Operadora": lambda values: " • ".join(
                        sorted(
                            {
                                value
                                for value in values
                                if value
                            }
                        )
                    ),
                    "Plano": lambda values: " • ".join(
                        sorted(
                            {
                                value
                                for value in values
                                if value
                            }
                        )
                    ),
                    "Segmento": lambda values: " • ".join(
                        sorted(
                            {
                                value
                                for value in values
                                if value
                            }
                        )
                    ),
                    "Observações": lambda values: " | ".join(
                        value
                        for value in values
                        if value
                    ),
                }
            )
            .reset_index()
            .rename(
                columns={
                    "Operadora": "Operadoras",
                    "Plano": "Planos",
                    "Segmento": "Segmentos",
                    "Observações": (
                        "Observações carteira"
                    ),
                }
            )
        )

        result = result.merge(
            grouped_carteiras,
            how="left",
            on="ID Consultor",
        )

    for column in [
        "Operadoras",
        "Planos",
        "Segmentos",
        "Observações carteira",
    ]:
        if column not in result.columns:
            result[column] = ""

        result[column] = (
            result[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

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

    result = result.sort_values(
        by=[
            "Nome",
            "Cargo",
        ],
        na_position="last",
    )

    return result.reset_index(drop=True)


def _filter_consultores(
    dataframe: pd.DataFrame,
    query: str,
    operator_name: str,
    segment: str,
) -> pd.DataFrame:
    """Aplica os filtros da página."""

    filtered = dataframe.copy()

    if operator_name != "Todas":
        normalized_operator = normalize_text(
            operator_name
        )

        filtered = filtered[
            filtered["Operadoras"]
            .fillna("")
            .astype(str)
            .map(normalize_text)
            .str.contains(
                normalized_operator,
                regex=False,
                na=False,
            )
        ]

    if segment != "Todos":
        normalized_segment = normalize_text(
            segment
        )

        filtered = filtered[
            filtered["Segmentos"]
            .fillna("")
            .astype(str)
            .map(normalize_text)
            .str.contains(
                normalized_segment,
                regex=False,
                na=False,
            )
        ]

    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        searchable_columns = [
            "Nome",
            "Cargo",
            "E-mail",
            "Telefone",
            "Operadoras",
            "Planos",
            "Segmentos",
            "Observações",
            "Observações carteira",
        ]

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


def _render_contact_actions(
    email: str,
    phone: str,
    consultant_id: str,
) -> None:
    """Renderiza ações de contato."""

    action_columns = st.columns(2)

    with action_columns[0]:
        if _is_email(email):
            st.link_button(
                "Enviar e-mail",
                f"mailto:{email}",
                use_container_width=True,
            )

        else:
            st.button(
                "E-mail indisponível",
                key=(
                    "consultant_email_unavailable_"
                    f"{consultant_id}"
                ),
                disabled=True,
                use_container_width=True,
            )

    with action_columns[1]:
        cleaned_phone = _clean_phone(
            phone
        )

        if cleaned_phone:
            st.link_button(
                "Ligar",
                f"tel:{cleaned_phone}",
                use_container_width=True,
            )

        else:
            st.button(
                "Telefone indisponível",
                key=(
                    "consultant_phone_unavailable_"
                    f"{consultant_id}"
                ),
                disabled=True,
                use_container_width=True,
            )


def _render_consultor(
    row: pd.Series,
    position: int,
) -> None:
    """Renderiza um consultor individual."""

    name = (
        _safe_value(
            row,
            "Nome",
        )
        or "Consultor sem identificação"
    )

    role = (
        _safe_value(
            row,
            "Cargo",
        )
        or "Cargo não informado"
    )

    email = _safe_value(
        row,
        "E-mail",
    )

    phone = _safe_value(
        row,
        "Telefone",
    )

    operators = (
        _safe_value(
            row,
            "Operadoras",
        )
        or "Nenhuma operadora vinculada"
    )

    plans = (
        _safe_value(
            row,
            "Planos",
        )
        or "Nenhum plano específico"
    )

    segments = (
        _safe_value(
            row,
            "Segmentos",
        )
        or "Segmento não informado"
    )

    observations = _safe_value(
        row,
        "Observações",
    )

    portfolio_observations = _safe_value(
        row,
        "Observações carteira",
    )

    consultant_id = (
        _safe_value(
            row,
            "ID Consultor",
        )
        or str(position)
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### 👤 {name}"
        )

        st.caption(
            role
        )

        st.markdown(
            f"**Operadoras atendidas:** {operators}"
        )

        st.markdown(
            f"**Planos:** {plans}"
        )

        st.markdown(
            f"**Segmentos:** {segments}"
        )

        detail_1, detail_2 = st.columns(2)

        detail_1.markdown(
            f"**E-mail:** "
            f"{email or 'Não informado'}"
        )

        detail_2.markdown(
            f"**Telefone:** "
            f"{phone or 'Não informado'}"
        )

        combined_observations = [
            value
            for value in [
                observations,
                portfolio_observations,
            ]
            if value
        ]

        if combined_observations:
            with st.expander(
                "Observações",
                expanded=False,
            ):
                for observation in combined_observations:
                    st.write(
                        observation
                    )

        _render_contact_actions(
            email=email,
            phone=phone,
            consultant_id=consultant_id,
        )


def render_consultores() -> None:
    """Renderiza a página de consultores."""

    render_hero(
        eyebrow="Carteiras comerciais",
        title="Consultores",
        description=(
            "Consulte os responsáveis por cada "
            "operadora, plano e carteira de clientes."
        ),
    )

    try:
        with st.spinner(
            "Carregando consultores..."
        ):
            dataframe = (
                _build_consultores_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar os consultores "
            "neste momento."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhum consultor foi encontrado na base."
        )
        return

    query = st.text_input(
        label="Pesquisar consultores",
        placeholder=(
            "Pesquise pelo nome, operadora, "
            "plano, segmento ou contato..."
        ),
        key="consultores_search_query",
    )

    operator_values: set[str] = set()

    for value in dataframe[
        "Operadoras"
    ].dropna().astype(str):
        operator_values.update(
            item.strip()
            for item in value.split("•")
            if item.strip()
        )

    operator_options = sorted(
        operator_values
    )

    segment_values: set[str] = set()

    for value in dataframe[
        "Segmentos"
    ].dropna().astype(str):
        segment_values.update(
            item.strip()
            for item in value.split("•")
            if item.strip()
        )

    segment_options = sorted(
        segment_values
    )

    filter_1, filter_2 = st.columns(2)

    with filter_1:
        selected_operator = st.selectbox(
            label="Operadora",
            options=[
                "Todas",
                *operator_options,
            ],
            key="consultores_operator_filter",
        )

    with filter_2:
        selected_segment = st.selectbox(
            label="Segmento",
            options=[
                "Todos",
                *segment_options,
            ],
            key="consultores_segment_filter",
        )

    filtered = _filter_consultores(
        dataframe=dataframe,
        query=query,
        operator_name=selected_operator,
        segment=selected_segment,
    )

    st.caption(
        f"{len(filtered)} consultor(es) encontrado(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhum consultor corresponde aos "
            "filtros selecionados."
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
            consultant,
        ) in zip(
            columns,
            batch.iterrows(),
        ):
            with column:
                _render_consultor(
                    row=consultant,
                    position=index,
                )

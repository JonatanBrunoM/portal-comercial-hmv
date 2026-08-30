from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import (
    get_documentos,
    get_operadoras,
    get_planos,
)
from utils.formatting import normalize_text


def _safe_value(
    row: pd.Series,
    column: str,
) -> str:
    """Retorna um campo textual sem gerar erro."""

    if column not in row.index:
        return ""

    value = row[column]

    if pd.isna(value):
        return ""

    return str(value).strip()


def _normalize_option(value: object) -> str:
    """Padroniza valores usados nos filtros."""

    text = str(value or "").strip()

    if not text or text.casefold() == "nan":
        return ""

    return text


def _format_validity(value: object) -> str:
    """Formata a validade do documento."""

    text = _normalize_option(value)

    if not text:
        return "Não informada"

    try:
        number = float(text.replace(",", "."))

        if number.is_integer():
            return f"{int(number)} dias"

        return f"{number:g} dias"

    except ValueError:
        return text


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _build_documentos_dataset() -> pd.DataFrame:
    """
    Une documentos, operadoras e planos em uma única base.
    """

    documentos = get_documentos()
    operadoras = get_operadoras()
    planos = get_planos()

    if documentos is None or documentos.empty:
        return pd.DataFrame()

    result = documentos.copy()

    # Adiciona o nome da operadora.
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

    # Adiciona o nome do plano.
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

    # Remove somente registros explicitamente inativos.
    status_column = next(
        (
            column
            for column in [
                "Status",
                "Status revisão",
            ]
            if column in result.columns
        ),
        None,
    )

    if status_column:
        normalized_status = (
            result[status_column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        result = result[
            ~normalized_status.eq("inativo")
        ]

    text_columns = [
        "Nome Operadora",
        "Nome Plano",
        "Documento",
        "Unidade",
        "Tipo atendimento",
        "Obrigatório",
        "Original/Cópia",
    ]

    for column in text_columns:
        if column not in result.columns:
            result[column] = ""

        result[column] = (
            result[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    sort_columns = [
        column
        for column in [
            "Nome Operadora",
            "Nome Plano",
            "Documento",
        ]
        if column in result.columns
    ]

    if sort_columns:
        result = result.sort_values(
            by=sort_columns,
            na_position="last",
        )

    return result.reset_index(drop=True)


def _filter_documentos(
    dataframe: pd.DataFrame,
    query: str,
    operator_name: str,
    plan_name: str,
    attendance_type: str,
    required_status: str,
    only_with_validity: bool,
) -> pd.DataFrame:
    """Aplica os filtros da página."""

    filtered = dataframe.copy()

    if operator_name != "Todas":
        filtered = filtered[
            filtered["Nome Operadora"].eq(
                operator_name
            )
        ]

    if plan_name != "Todos":
        filtered = filtered[
            filtered["Nome Plano"].eq(
                plan_name
            )
        ]

    if attendance_type != "Todos":
        filtered = filtered[
            filtered["Tipo atendimento"].eq(
                attendance_type
            )
        ]

    if required_status != "Todos":
        normalized_required = (
            filtered["Obrigatório"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        filtered = filtered[
            normalized_required.eq(
                required_status.casefold()
            )
        ]

    if only_with_validity:
        validity = (
            filtered["Validade em dias"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        filtered = filtered[
            validity.ne("")
            & ~validity.str.casefold().eq("nan")
        ]

    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        searchable_columns = [
            column
            for column in [
                "Documento",
                "Nome Operadora",
                "Nome Plano",
                "Unidade",
                "Tipo atendimento",
                "Original/Cópia",
                "Observações",
            ]
            if column in filtered.columns
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


def _render_documento(
    document: pd.Series,
    position: int,
) -> None:
    """Renderiza um documento individual."""

    document_name = (
        _safe_value(
            document,
            "Documento",
        )
        or "Documento sem identificação"
    )

    operator_name = (
        _safe_value(
            document,
            "Nome Operadora",
        )
        or "Operadora não identificada"
    )

    plan_name = (
        _safe_value(
            document,
            "Nome Plano",
        )
        or "Plano não informado"
    )

    unit = (
        _safe_value(
            document,
            "Unidade",
        )
        or "Não informada"
    )

    attendance_type = (
        _safe_value(
            document,
            "Tipo atendimento",
        )
        or "Geral"
    )

    required = (
        _safe_value(
            document,
            "Obrigatório",
        )
        or "Não identificado"
    )

    original_copy = (
        _safe_value(
            document,
            "Original/Cópia",
        )
        or "Não identificado"
    )

    validity = _format_validity(
        _safe_value(
            document,
            "Validade em dias",
        )
    )

    accepts_other = (
        _safe_value(
            document,
            "Aceita outro convênio",
        )
        or "Não identificado"
    )

    accepts_email = (
        _safe_value(
            document,
            "Aceita e-mail",
        )
        or "Não identificado"
    )

    accepts_fax = (
        _safe_value(
            document,
            "Aceita fax",
        )
        or "Não identificado"
    )

    document_link = _safe_value(
        document,
        "Link Documento",
    )

    observations = _safe_value(
        document,
        "Observações",
    )

    document_id = (
        _safe_value(
            document,
            "ID Documento",
        )
        or str(position)
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### 📄 {document_name}"
        )

        st.caption(
            f"{operator_name} • {plan_name}"
        )

        detail_1, detail_2, detail_3 = (
            st.columns(3)
        )

        detail_1.markdown(
            f"**Obrigatório:** {required}"
        )

        detail_2.markdown(
            f"**Validade:** {validity}"
        )

        detail_3.markdown(
            f"**Formato:** {original_copy}"
        )

        st.markdown(
            f"**Tipo de atendimento:** "
            f"{attendance_type}"
        )

        st.markdown(
            f"**Unidade:** {unit}"
        )

        with st.expander(
            "Regras de recebimento",
            expanded=False,
        ):
            col_1, col_2, col_3 = (
                st.columns(3)
            )

            col_1.markdown(
                "**Outro convênio:** "
                f"{accepts_other}"
            )

            col_2.markdown(
                f"**E-mail:** {accepts_email}"
            )

            col_3.markdown(
                f"**Fax:** {accepts_fax}"
            )

        if observations:
            with st.expander(
                "Observações",
                expanded=False,
            ):
                st.write(
                    observations
                )

        if (
            document_link.startswith("https://")
            or document_link.startswith("http://")
        ):
            st.link_button(
                "Abrir documento",
                document_link,
                use_container_width=True,
            )

        else:
            st.button(
                "Arquivo não vinculado",
                key=(
                    "document_unavailable_"
                    f"{document_id}"
                ),
                disabled=True,
                use_container_width=True,
            )


def render_documentos() -> None:
    """Renderiza a página geral de documentos."""

    render_hero(
        eyebrow="Atendimento e faturamento",
        title="Documentos",
        description=(
            "Consulte os documentos necessários, "
            "regras de recebimento, validade e formato."
        ),
    )

    try:
        with st.spinner(
            "Carregando documentos..."
        ):
            dataframe = (
                _build_documentos_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar os documentos "
            "neste momento."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhum documento foi encontrado na base."
        )
        return

    query = st.text_input(
        label="Pesquisar documentos",
        placeholder=(
            "Pesquise pelo documento, operadora, "
            "plano ou atendimento..."
        ),
        key="documentos_search_query",
    )

    operator_options = sorted(
        value
        for value in dataframe[
            "Nome Operadora"
        ].unique()
        if value
    )

    selected_operator = st.selectbox(
        label="Operadora",
        options=[
            "Todas",
            *operator_options,
        ],
        key="documentos_operator_filter",
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
        ].unique()
        if value
    )

    attendance_options = sorted(
        value
        for value in operator_filtered[
            "Tipo atendimento"
        ].unique()
        if value
    )

    filter_1, filter_2, filter_3 = (
        st.columns(3)
    )

    with filter_1:
        selected_plan = st.selectbox(
            label="Plano",
            options=[
                "Todos",
                *plan_options,
            ],
            key="documentos_plan_filter",
        )

    with filter_2:
        selected_attendance = st.selectbox(
            label="Tipo de atendimento",
            options=[
                "Todos",
                *attendance_options,
            ],
            key=(
                "documentos_attendance_filter"
            ),
        )

    with filter_3:
        selected_required = st.selectbox(
            label="Obrigatoriedade",
            options=[
                "Todos",
                "Sim",
                "Não",
                "Não identificado",
            ],
            key=(
                "documentos_required_filter"
            ),
        )

    only_with_validity = st.checkbox(
        label=(
            "Mostrar somente documentos "
            "com validade informada"
        ),
        key="documentos_validity_filter",
    )

    filtered = _filter_documentos(
        dataframe=dataframe,
        query=query,
        operator_name=selected_operator,
        plan_name=selected_plan,
        attendance_type=(
            selected_attendance
        ),
        required_status=(
            selected_required
        ),
        only_with_validity=(
            only_with_validity
        ),
    )

    st.caption(
        f"{len(filtered)} documento(s) "
        "encontrado(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhum documento corresponde aos "
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
            document,
        ) in zip(
            columns,
            batch.iterrows(),
        ):
            with column:
                _render_documento(
                    document=document,
                    position=index,
                )

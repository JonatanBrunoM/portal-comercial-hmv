from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import (
    get_contatos,
    get_operadoras,
    get_planos,
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


def _clean_phone(value: str) -> str:
    """Mantém somente os números necessários para o link telefônico."""

    return re.sub(
        r"[^\d+]",
        "",
        value,
    )


def _is_email(value: str) -> bool:
    """Verifica se o conteúdo possui formato básico de e-mail."""

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value.strip(),
        )
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _build_contatos_dataset() -> pd.DataFrame:
    """
    Une os contatos aos nomes das operadoras e dos planos.
    """

    contatos = get_contatos()
    operadoras = get_operadoras()
    planos = get_planos()

    if contatos is None or contatos.empty:
        return pd.DataFrame()

    result = contatos.copy()

    # Nome da operadora
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

    # Nome do plano
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

    # Remove apenas contatos explicitamente inativos
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

    required_columns = [
        "Nome Operadora",
        "Nome Plano",
        "Nome/Setor",
        "Finalidade",
        "Tipo",
        "Contato",
        "Horário atendimento",
        "Responsável",
        "Observações",
    ]

    for column in required_columns:
        if column not in result.columns:
            result[column] = ""

        result[column] = (
            result[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    sort_columns = [
        "Nome Operadora",
        "Finalidade",
        "Nome/Setor",
        "Contato",
    ]

    result = result.sort_values(
        by=sort_columns,
        na_position="last",
    )

    return result.reset_index(drop=True)


def _filter_contatos(
    dataframe: pd.DataFrame,
    query: str,
    operator_name: str,
    plan_name: str,
    purpose: str,
    contact_type: str,
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

    if purpose != "Todas":
        filtered = filtered[
            filtered["Finalidade"].eq(
                purpose
            )
        ]

    if contact_type != "Todos":
        filtered = filtered[
            filtered["Tipo"].eq(
                contact_type
            )
        ]

    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        searchable_columns = [
            "Nome Operadora",
            "Nome Plano",
            "Nome/Setor",
            "Finalidade",
            "Tipo",
            "Contato",
            "Horário atendimento",
            "Responsável",
            "Observações",
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


def _render_contact_action(
    contact_type: str,
    contact: str,
    contact_id: str,
) -> None:
    """Renderiza a ação apropriada para o contato."""

    normalized_type = normalize_text(
        contact_type
    )

    if (
        normalized_type == "email"
        or _is_email(contact)
    ):
        st.link_button(
            "Enviar e-mail",
            f"mailto:{contact}",
            use_container_width=True,
        )

        return

    phone = _clean_phone(
        contact
    )

    if (
        phone
        and normalized_type in {
            "telefone",
            "celular",
            "whatsapp",
        }
    ):
        st.link_button(
            "Ligar",
            f"tel:{phone}",
            use_container_width=True,
        )

        return

    st.button(
        "Contato somente para consulta",
        key=f"contact_read_only_{contact_id}",
        disabled=True,
        use_container_width=True,
    )


def _render_contato(
    contact_row: pd.Series,
    position: int,
) -> None:
    """Renderiza um contato individual."""

    purpose = (
        _safe_value(
            contact_row,
            "Finalidade",
        )
        or "Contato geral"
    )

    operator_name = (
        _safe_value(
            contact_row,
            "Nome Operadora",
        )
        or "Operadora não identificada"
    )

    plan_name = (
        _safe_value(
            contact_row,
            "Nome Plano",
        )
        or "Todos os planos"
    )

    department = (
        _safe_value(
            contact_row,
            "Nome/Setor",
        )
        or "Setor não informado"
    )

    contact_type = (
        _safe_value(
            contact_row,
            "Tipo",
        )
        or "Não informado"
    )

    contact = (
        _safe_value(
            contact_row,
            "Contato",
        )
        or "Não informado"
    )

    responsible = (
        _safe_value(
            contact_row,
            "Responsável",
        )
        or "Não informado"
    )

    schedule = (
        _safe_value(
            contact_row,
            "Horário atendimento",
        )
        or "Não informado"
    )

    observations = _safe_value(
        contact_row,
        "Observações",
    )

    contact_id = (
        _safe_value(
            contact_row,
            "ID Contato",
        )
        or str(position)
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### 📞 {purpose}"
        )

        st.caption(
            f"{operator_name} • {plan_name}"
        )

        st.markdown(
            f"**Setor:** {department}"
        )

        detail_1, detail_2 = st.columns(
            2
        )

        detail_1.markdown(
            f"**Tipo:** {contact_type}"
        )

        detail_2.markdown(
            f"**Contato:** {contact}"
        )

        st.markdown(
            f"**Responsável:** {responsible}"
        )

        st.markdown(
            f"**Horário:** {schedule}"
        )

        if observations:
            with st.expander(
                "Observações",
                expanded=False,
            ):
                st.write(
                    observations
                )

        if contact != "Não informado":
            _render_contact_action(
                contact_type=contact_type,
                contact=contact,
                contact_id=contact_id,
            )


def render_contatos() -> None:
    """Renderiza a página geral de contatos."""

    render_hero(
        eyebrow="Centrais e responsáveis",
        title="Contatos",
        description=(
            "Encontre telefones, e-mails, fax, "
            "centrais de atendimento e responsáveis "
            "das operadoras."
        ),
    )

    try:
        with st.spinner(
            "Carregando contatos..."
        ):
            dataframe = (
                _build_contatos_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar os contatos "
            "neste momento."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhum contato foi encontrado na base."
        )
        return

    query = st.text_input(
        label="Pesquisar contatos",
        placeholder=(
            "Pesquise por operadora, setor, telefone, "
            "e-mail ou finalidade..."
        ),
        key="contatos_search_query",
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
        key="contatos_operator_filter",
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

    purpose_options = sorted(
        value
        for value in operator_filtered[
            "Finalidade"
        ].unique()
        if value
    )

    type_options = sorted(
        value
        for value in operator_filtered[
            "Tipo"
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
            key="contatos_plan_filter",
        )

    with filter_2:
        selected_purpose = st.selectbox(
            label="Finalidade",
            options=[
                "Todas",
                *purpose_options,
            ],
            key="contatos_purpose_filter",
        )

    with filter_3:
        selected_type = st.selectbox(
            label="Tipo de contato",
            options=[
                "Todos",
                *type_options,
            ],
            key="contatos_type_filter",
        )

    filtered = _filter_contatos(
        dataframe=dataframe,
        query=query,
        operator_name=selected_operator,
        plan_name=selected_plan,
        purpose=selected_purpose,
        contact_type=selected_type,
    )

    st.caption(
        f"{len(filtered)} contato(s) encontrado(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhum contato corresponde aos "
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
            contact_row,
        ) in zip(
            columns,
            batch.iterrows(),
        ):
            with column:
                _render_contato(
                    contact_row=contact_row,
                    position=index,
                )

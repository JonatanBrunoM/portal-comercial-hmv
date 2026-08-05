from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from core.sheets_service import (
    get_autorizacoes,
    get_coberturas,
    get_contatos,
    get_contingencias,
    get_documentos,
    get_elegibilidade,
    get_operadoras,
    get_planos,
    get_portais,
)
from utils.formatting import normalize_text


@dataclass(frozen=True)
class OperadoraSummary:
    operator_id: str
    name: str
    short_name: str
    status: str
    consultant: str
    plans_count: int
    observations: str


def _safe_value(
    row: pd.Series,
    column: str,
) -> str:
    if column not in row.index:
        return ""

    value = row[column]

    if pd.isna(value):
        return ""

    return str(value).strip()


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def get_operadoras_summary() -> list[OperadoraSummary]:
    """Retorna as operadoras com a quantidade de planos."""

    try:
        operadoras = get_operadoras()
    
    except RuntimeError:
        return []
    
    try:
        planos = get_planos()
    
    except RuntimeError:
        planos = pd.DataFrame()

    if operadoras.empty:
        return []

    plans_count: dict[str, int] = {}

    if not planos.empty and "ID Operadora" in planos.columns:
        plans_count = (
            planos["ID Operadora"]
            .fillna("")
            .astype(str)
            .str.strip()
            .value_counts()
            .to_dict()
        )

    summaries: list[OperadoraSummary] = []

    for _, row in operadoras.iterrows():
        operator_id = _safe_value(
            row,
            "ID Operadora",
        )

        name = (
            _safe_value(row, "Operadora")
            or _safe_value(row, "Nome curto")
            or "Operadora sem nome"
        )

        short_name = (
            _safe_value(row, "Nome curto")
            or name
        )

        summaries.append(
            OperadoraSummary(
                operator_id=operator_id,
                name=name,
                short_name=short_name,
                status=_safe_value(row, "Status"),
                consultant=_safe_value(
                    row,
                    "Consultor responsável",
                ),
                plans_count=int(
                    plans_count.get(
                        operator_id,
                        0,
                    )
                ),
                observations=_safe_value(
                    row,
                    "Observações",
                ),
            )
        )

    return sorted(
        summaries,
        key=lambda item: normalize_text(
            item.short_name
        ),
    )


def search_operadoras(
    query: str,
) -> list[OperadoraSummary]:
    """Filtra as operadoras pelo nome ou identificador."""

    operadoras = get_operadoras_summary()
    normalized_query = normalize_text(query)

    if not normalized_query:
        return operadoras

    return [
        operadora
        for operadora in operadoras
        if (
            normalized_query
            in normalize_text(operadora.name)
            or normalized_query
            in normalize_text(operadora.short_name)
            or normalized_query
            in normalize_text(operadora.operator_id)
        )
    ]


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def get_operadora_planos(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna os planos vinculados a uma operadora."""

    planos = get_planos()

    if (
        planos.empty
        or "ID Operadora" not in planos.columns
    ):
        return pd.DataFrame()

    filtered = planos[
        planos["ID Operadora"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(str(operator_id).strip())
    ].copy()

    sort_column = next(
        (
            column
            for column in [
                "Nome padronizado",
                "Plano",
            ]
            if column in filtered.columns
        ),
        None,
    )

    if sort_column:
        filtered = filtered.sort_values(
            by=sort_column,
            na_position="last",
        )

    return filtered.reset_index(drop=True)


def get_operadora_by_id(
    operator_id: str,
) -> OperadoraSummary | None:
    """Localiza uma operadora pelo seu identificador."""

    return next(
        (
            operadora
            for operadora in get_operadoras_summary()
            if operadora.operator_id == operator_id
        ),
        None,
    )

def _filter_by_operator(
    dataframe: pd.DataFrame,
    operator_id: str,
) -> pd.DataFrame:
    """
    Filtra qualquer módulo pelo ID da operadora.
    """

    if (
        dataframe is None
        or dataframe.empty
        or "ID Operadora" not in dataframe.columns
    ):
        return pd.DataFrame()

    filtered = dataframe[
        dataframe["ID Operadora"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(str(operator_id).strip())
    ].copy()

    return filtered.reset_index(drop=True)


def _safe_module_load(
    loader,
    operator_id: str,
) -> pd.DataFrame:
    """
    Carrega um módulo sem impedir a abertura da ficha
    caso uma aba apresente falha temporária.
    """

    try:
        dataframe = loader()

    except RuntimeError:
        return pd.DataFrame()

    return _filter_by_operator(
        dataframe=dataframe,
        operator_id=operator_id,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def get_operadora_portais(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna os portais da operadora."""

    return _safe_module_load(
        get_portais,
        operator_id,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def get_operadora_elegibilidade(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna as regras de elegibilidade da operadora."""

    return _safe_module_load(
        get_elegibilidade,
        operator_id,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def get_operadora_documentos(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna os documentos da operadora."""

    return _safe_module_load(
        get_documentos,
        operator_id,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def get_operadora_autorizacoes(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna as autorizações da operadora."""

    return _safe_module_load(
        get_autorizacoes,
        operator_id,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def get_operadora_coberturas(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna as coberturas da operadora."""

    return _safe_module_load(
        get_coberturas,
        operator_id,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def get_operadora_contatos(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna os contatos da operadora."""

    return _safe_module_load(
        get_contatos,
        operator_id,
    )


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def get_operadora_contingencias(
    operator_id: str,
) -> pd.DataFrame:
    """Retorna as contingências da operadora."""

    return _safe_module_load(
        get_contingencias,
        operator_id,
    )

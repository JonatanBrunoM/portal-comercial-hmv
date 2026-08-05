from __future__ import annotations

import logging

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

from config.settings import CACHE_SETTINGS, SHEETS


logger = logging.getLogger(__name__)


@st.cache_resource
def get_sheets_connection() -> GSheetsConnection:
    """Retorna a conexão compartilhada com o Google Sheets."""

    return st.connection(
        "gsheets",
        type=GSheetsConnection,
    )


def _clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame recebido do Google Sheets.
    """

    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    cleaned = dataframe.copy()

    cleaned.columns = [
        str(column).strip()
        for column in cleaned.columns
    ]

    cleaned = cleaned.dropna(
        axis=0,
        how="all",
    )

    cleaned = cleaned.dropna(
        axis=1,
        how="all",
    )

    return cleaned.reset_index(drop=True)


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def read_worksheet(
    worksheet: str,
    ttl: int = 600,
) -> pd.DataFrame:
    """Lê uma aba da base comercial."""

    try:
        connection = get_sheets_connection()

        dataframe = connection.read(
            worksheet=worksheet,
            ttl=ttl,
        )

        return _clean_dataframe(dataframe)

    except Exception as error:
        logger.exception(
            "Erro ao ler a aba %s.",
            worksheet,
        )
    
        raise RuntimeError(
            f"Erro ao carregar a aba '{worksheet}': "
            f"{type(error).__name__}: {error}"
        ) from error


def get_operadoras() -> pd.DataFrame:
    """Retorna somente as operadoras ativas."""

    dataframe = read_worksheet(
        worksheet=SHEETS["operadoras"],
        ttl=CACHE_SETTINGS.OPERADORAS,
    )

    if dataframe.empty:
        return dataframe

    if "Status" in dataframe.columns:
        dataframe = dataframe[
            dataframe["Status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq("ativo")
        ]

    return dataframe.reset_index(drop=True)


def get_planos() -> pd.DataFrame:
    """Retorna somente os planos ativos."""

    dataframe = read_worksheet(
        worksheet=SHEETS["planos"],
        ttl=CACHE_SETTINGS.PLANOS,
    )

    if dataframe.empty:
        return dataframe

    if "Status" in dataframe.columns:
        dataframe = dataframe[
            dataframe["Status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq("ativo")
        ]

    return dataframe.reset_index(drop=True)


def get_portais() -> pd.DataFrame:
    """Retorna os portais cadastrados."""

    return read_worksheet(
        worksheet=SHEETS["portais"],
        ttl=CACHE_SETTINGS.PORTAIS,
    )


def get_documentos() -> pd.DataFrame:
    """Retorna os documentos cadastrados."""

    return read_worksheet(
        worksheet=SHEETS["documentos"],
        ttl=CACHE_SETTINGS.DOCUMENTOS,
    )


def get_contatos() -> pd.DataFrame:
    """Retorna os contatos cadastrados."""

    return read_worksheet(
        worksheet=SHEETS["contatos"],
        ttl=CACHE_SETTINGS.CONTATOS,
    )


def get_contingencias() -> pd.DataFrame:
    """Retorna as contingências cadastradas."""

    return read_worksheet(
        worksheet=SHEETS["contingencias"],
        ttl=CACHE_SETTINGS.CONTINGENCIAS,
    )


def get_comunicados() -> pd.DataFrame:
    """Retorna os comunicados cadastrados."""

    return read_worksheet(
        worksheet=SHEETS["comunicados"],
        ttl=CACHE_SETTINGS.COMUNICADOS,
    )


def get_elegibilidade() -> pd.DataFrame:
    """Retorna as regras de elegibilidade."""

    return read_worksheet(
        worksheet=SHEETS["elegibilidade"],
        ttl=CACHE_SETTINGS.ELEGIBILIDADE,
    )


def get_autorizacoes() -> pd.DataFrame:
    """Retorna as regras de autorização."""

    return read_worksheet(
        worksheet=SHEETS["autorizacoes"],
        ttl=CACHE_SETTINGS.AUTORIZACOES,
    )


def get_coberturas() -> pd.DataFrame:
    """Retorna as regras de cobertura."""

    return read_worksheet(
        worksheet=SHEETS["coberturas"],
        ttl=CACHE_SETTINGS.COBERTURAS,
    )


def get_dicas_operacionais() -> pd.DataFrame:
    """Retorna as dicas operacionais."""

    return read_worksheet(
        worksheet=SHEETS["dicas"],
        ttl=CACHE_SETTINGS.DICAS,
    )

def clear_sheets_cache() -> None:
    """
    Limpa o cache das leituras e da conexão.

    Usaremos essa função futuramente após alterações
    feitas pela área administrativa.
    """

    st.cache_data.clear()
    st.cache_resource.clear()

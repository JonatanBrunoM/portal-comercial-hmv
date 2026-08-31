from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from config.settings import CACHE_SETTINGS, DATASETS
from core.supabase_repository import fetch_table

logger = logging.getLogger(__name__)


def _resolve_dataset(dataset: str) -> str:
    if dataset in DATASETS:
        return DATASETS[dataset]
    if dataset in DATASETS.values():
        return dataset
    raise KeyError(f"Conjunto de dados não configurado: {dataset}")


def _clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()
    cleaned = dataframe.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    return cleaned.dropna(axis=0, how="all").reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner=False)
def read_dataset(dataset: str, ttl: int = 600) -> pd.DataFrame:
    """Lê uma tabela do Supabase preservando os nomes nativos das colunas."""
    del ttl
    table_name = _resolve_dataset(dataset)
    try:
        return _clean_dataframe(fetch_table(table_name))
    except Exception as error:
        logger.exception("Erro ao ler a tabela %s no Supabase.", table_name)
        raise RuntimeError(
            f"Não foi possível carregar '{table_name}' no Supabase."
        ) from error


def _active_only(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "status" not in dataframe.columns:
        return dataframe.reset_index(drop=True)
    mask = (
        dataframe["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("ativo")
    )
    return dataframe[mask].reset_index(drop=True)


def get_operadoras() -> pd.DataFrame:
    return _active_only(read_dataset("operadoras", CACHE_SETTINGS.OPERADORAS))


def get_planos() -> pd.DataFrame:
    return _active_only(read_dataset("planos", CACHE_SETTINGS.PLANOS))


def get_locais_atendimento() -> pd.DataFrame:
    return _active_only(read_dataset("locais_atendimento", CACHE_SETTINGS.LOCAIS))


def get_tipos_atendimento() -> pd.DataFrame:
    return _active_only(read_dataset("tipos_atendimento", CACHE_SETTINGS.TIPOS_ATENDIMENTO))


def get_plano_locais() -> pd.DataFrame:
    return read_dataset("plano_locais", CACHE_SETTINGS.PLANO_LOCAIS)


def get_portais() -> pd.DataFrame:
    return _active_only(read_dataset("portais", CACHE_SETTINGS.PORTAIS))


def get_documentos() -> pd.DataFrame:
    return _active_only(read_dataset("documentos", CACHE_SETTINGS.DOCUMENTOS))


def get_contatos() -> pd.DataFrame:
    return _active_only(read_dataset("contatos", CACHE_SETTINGS.CONTATOS))


def get_contingencias() -> pd.DataFrame:
    return read_dataset("contingencias", CACHE_SETTINGS.CONTINGENCIAS)


def get_comunicados() -> pd.DataFrame:
    return read_dataset("comunicados", CACHE_SETTINGS.COMUNICADOS)


def get_elegibilidade() -> pd.DataFrame:
    return _active_only(read_dataset("elegibilidade", CACHE_SETTINGS.ELEGIBILIDADE))


def get_autorizacoes() -> pd.DataFrame:
    return _active_only(read_dataset("autorizacoes", CACHE_SETTINGS.AUTORIZACOES))


def get_coberturas() -> pd.DataFrame:
    return _active_only(read_dataset("coberturas", CACHE_SETTINGS.COBERTURAS))


def get_dicas_operacionais() -> pd.DataFrame:
    return _active_only(read_dataset("dicas_operacionais", CACHE_SETTINGS.DICAS))


def get_consultores() -> pd.DataFrame:
    return _active_only(read_dataset("consultores", CACHE_SETTINGS.CONSULTORES))


def get_carteiras() -> pd.DataFrame:
    return _active_only(read_dataset("carteiras", CACHE_SETTINGS.CARTEIRAS))


def clear_data_cache() -> None:
    st.cache_data.clear()

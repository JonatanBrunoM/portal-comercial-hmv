from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.data_service import (
    get_autorizacoes,
    get_coberturas,
    get_contatos,
    get_contingencias,
    get_documentos,
    get_elegibilidade,
    get_operadoras,
    get_planos,
    get_portais,
    get_consultores,
)


@dataclass(frozen=True)
class OperadoraSummary:
    operator_id: str
    code: str
    name: str
    short_name: str
    status: str
    observations: str
    logo_url: str
    site_url: str
    plans_count: int
    consultant: str


def _safe(row: pd.Series, column: str) -> str:
    if column not in row.index or pd.isna(row[column]):
        return ""
    return str(row[column]).strip()


def _filter_by_operator(dataframe: pd.DataFrame, operator_id: str) -> pd.DataFrame:
    if dataframe.empty or "ID Operadora" not in dataframe.columns:
        return dataframe.iloc[0:0].copy()
    return dataframe[
        dataframe["ID Operadora"].fillna("").astype(str).str.strip().eq(str(operator_id).strip())
    ].reset_index(drop=True)


def _consultant_name(operator_id: str) -> str:
    try:
        dataframe = _filter_by_operator(get_consultores(), operator_id)
        if dataframe.empty:
            return ""
        return _safe(dataframe.iloc[0], "Nome")
    except Exception:
        return ""


def _to_summary(row: pd.Series, planos: pd.DataFrame) -> OperadoraSummary:
    operator_id = _safe(row, "ID Operadora")
    linked_plans = _filter_by_operator(planos, operator_id)
    return OperadoraSummary(
        operator_id=operator_id,
        code=_safe(row, "Código"),
        name=_safe(row, "Operadora"),
        short_name=_safe(row, "Nome curto") or _safe(row, "Operadora"),
        status=_safe(row, "Status"),
        observations=_safe(row, "Observações"),
        logo_url=_safe(row, "Logo URL"),
        site_url=_safe(row, "Site URL"),
        plans_count=len(linked_plans),
        consultant=_consultant_name(operator_id),
    )


def search_operadoras(query: str = "") -> list[OperadoraSummary]:
    operadoras = get_operadoras()
    planos = get_planos()
    term = (query or "").strip().casefold()
    results: list[OperadoraSummary] = []
    for _, row in operadoras.iterrows():
        searchable = " ".join([
            _safe(row, "Código"),
            _safe(row, "Operadora"),
            _safe(row, "Nome curto"),
        ]).casefold()
        if term and term not in searchable:
            continue
        results.append(_to_summary(row, planos))
    return results


def get_operadora_by_id(operator_id: str) -> OperadoraSummary | None:
    operadoras = get_operadoras()
    if operadoras.empty or "ID Operadora" not in operadoras.columns:
        return None
    match = operadoras[
        operadoras["ID Operadora"].fillna("").astype(str).str.strip().eq(str(operator_id).strip())
    ]
    if match.empty:
        return None
    return _to_summary(match.iloc[0], get_planos())


def get_operadora_planos(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_planos(), operator_id)


def get_operadora_portais(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_portais(), operator_id)


def get_operadora_elegibilidade(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_elegibilidade(), operator_id)


def get_operadora_documentos(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_documentos(), operator_id)


def get_operadora_autorizacoes(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_autorizacoes(), operator_id)


def get_operadora_coberturas(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_coberturas(), operator_id)


def get_operadora_contatos(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_contatos(), operator_id)


def get_operadora_contingencias(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_contingencias(), operator_id)

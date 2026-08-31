from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.data_service import (
    get_autorizacoes,
    get_carteiras,
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
    if dataframe.empty or "operadora_id" not in dataframe.columns:
        return dataframe.iloc[0:0].copy()
    mask = (
        dataframe["operadora_id"].fillna("").astype(str).str.strip()
        .eq(str(operator_id).strip())
    )
    return dataframe[mask].reset_index(drop=True)


def _consultant_name(operator_id: str) -> str:
    carteiras = _filter_by_operator(get_carteiras(), operator_id)
    consultores = get_consultores()
    if carteiras.empty or consultores.empty or "id" not in consultores.columns:
        return ""
    ids = set(carteiras.get("consultor_id", pd.Series(dtype=str)).dropna().astype(str))
    names = [
        _safe(row, "nome")
        for _, row in consultores.iterrows()
        if str(row.get("id", "")) in ids and _safe(row, "nome")
    ]
    return " • ".join(dict.fromkeys(names))


def _to_summary(row: pd.Series, planos: pd.DataFrame) -> OperadoraSummary:
    operator_id = _safe(row, "id")
    return OperadoraSummary(
        operator_id=operator_id,
        code=_safe(row, "codigo"),
        name=_safe(row, "nome"),
        short_name=_safe(row, "nome_curto") or _safe(row, "nome"),
        status=_safe(row, "status"),
        observations=_safe(row, "observacoes"),
        logo_url=_safe(row, "logo_url"),
        site_url=_safe(row, "site_url"),
        plans_count=len(_filter_by_operator(planos, operator_id)),
        consultant=_consultant_name(operator_id),
    )


def search_operadoras(query: str = "") -> list[OperadoraSummary]:
    operadoras = get_operadoras()
    planos = get_planos()
    term = (query or "").strip().casefold()
    results: list[OperadoraSummary] = []
    for _, row in operadoras.iterrows():
        searchable = " ".join([
            _safe(row, "codigo"), _safe(row, "nome"), _safe(row, "nome_curto")
        ]).casefold()
        if term and term not in searchable:
            continue
        results.append(_to_summary(row, planos))
    return results


def get_operadora_by_id(operator_id: str) -> OperadoraSummary | None:
    operadoras = get_operadoras()
    if operadoras.empty or "id" not in operadoras.columns:
        return None
    match = operadoras[
        operadoras["id"].fillna("").astype(str).str.strip().eq(str(operator_id).strip())
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

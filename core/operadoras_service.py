from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.data_service import (
    get_autorizacoes_native,
    get_coberturas_native,
    get_contatos_native,
    get_contingencias_native,
    get_documentos_native,
    get_elegibilidade_native,
    get_locais_atendimento_native,
    get_operadoras_native,
    get_planos_native,
    get_portais_native,
    get_tipos_atendimento_native,
    get_carteiras_native,
    get_consultores_native,
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
    return dataframe[
        dataframe["operadora_id"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(str(operator_id).strip())
    ].reset_index(drop=True)


def _merge_reference_name(
    dataframe: pd.DataFrame,
    reference: pd.DataFrame,
    foreign_key: str,
    output_column: str,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    result = dataframe.copy()
    if foreign_key not in result.columns:
        result[output_column] = ""
        return result

    if reference.empty or not {"id", "nome"}.issubset(reference.columns):
        result[output_column] = ""
        return result

    lookup = (
        reference[["id", "nome"]]
        .drop_duplicates(subset=["id"])
        .rename(columns={"id": foreign_key, "nome": output_column})
    )
    return result.merge(lookup, on=foreign_key, how="left")


def _enrich_context(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    if result.empty:
        return result

    if "plano_id" in result.columns:
        result = _merge_reference_name(
            result,
            get_planos_native(),
            "plano_id",
            "plano_nome",
        )

    if "local_id" in result.columns:
        result = _merge_reference_name(
            result,
            get_locais_atendimento_native(),
            "local_id",
            "local_nome",
        )

    if "tipo_atendimento_id" in result.columns:
        result = _merge_reference_name(
            result,
            get_tipos_atendimento_native(),
            "tipo_atendimento_id",
            "tipo_atendimento_nome",
        )

    return result


def _consultant_name(operator_id: str) -> str:
    try:
        carteiras = _filter_by_operator(get_carteiras_native(), operator_id)
        if carteiras.empty or "consultor_id" not in carteiras.columns:
            return ""

        consultants = get_consultores_native()
        if consultants.empty or "id" not in consultants.columns:
            return ""

        consultant_id = _safe(carteiras.iloc[0], "consultor_id")
        match = consultants[
            consultants["id"].fillna("").astype(str).str.strip().eq(consultant_id)
        ]
        if match.empty:
            return ""
        return _safe(match.iloc[0], "nome")
    except Exception:
        return ""


def _to_summary(row: pd.Series, planos: pd.DataFrame) -> OperadoraSummary:
    operator_id = _safe(row, "id")
    linked_plans = _filter_by_operator(planos, operator_id)
    return OperadoraSummary(
        operator_id=operator_id,
        code=_safe(row, "codigo"),
        name=_safe(row, "nome"),
        short_name=_safe(row, "nome_curto") or _safe(row, "nome"),
        status=_safe(row, "status"),
        observations=_safe(row, "observacoes"),
        logo_url=_safe(row, "logo_url"),
        site_url=_safe(row, "site_url"),
        plans_count=len(linked_plans),
        consultant=_consultant_name(operator_id),
    )


def search_operadoras(query: str = "") -> list[OperadoraSummary]:
    operadoras = get_operadoras_native()
    planos = get_planos_native()
    term = (query or "").strip().casefold()
    results: list[OperadoraSummary] = []

    for _, row in operadoras.iterrows():
        searchable = " ".join(
            [_safe(row, "codigo"), _safe(row, "nome"), _safe(row, "nome_curto")]
        ).casefold()
        if term and term not in searchable:
            continue
        results.append(_to_summary(row, planos))

    return results


def get_operadora_by_id(operator_id: str) -> OperadoraSummary | None:
    operadoras = get_operadoras_native()
    if operadoras.empty or "id" not in operadoras.columns:
        return None

    match = operadoras[
        operadoras["id"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(str(operator_id).strip())
    ]
    if match.empty:
        return None
    return _to_summary(match.iloc[0], get_planos_native())


def get_operadora_planos(operator_id: str) -> pd.DataFrame:
    return _filter_by_operator(get_planos_native(), operator_id)


def get_operadora_portais(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_portais_native(), operator_id))


def get_operadora_elegibilidade(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_elegibilidade_native(), operator_id))


def get_operadora_documentos(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_documentos_native(), operator_id))


def get_operadora_autorizacoes(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_autorizacoes_native(), operator_id))


def get_operadora_coberturas(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_coberturas_native(), operator_id))


def get_operadora_contatos(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_contatos_native(), operator_id))


def get_operadora_contingencias(operator_id: str) -> pd.DataFrame:
    return _enrich_context(_filter_by_operator(get_contingencias_native(), operator_id))

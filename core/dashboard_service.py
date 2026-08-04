from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.sheets_service import (
    get_comunicados,
    get_contingencias,
    get_operadoras,
    get_planos,
)


@dataclass(frozen=True)
class DashboardSummary:
    """Indicadores exibidos na página inicial."""

    operadoras: int
    planos: int
    comunicados: int
    contingencias: int


def _count_rows(dataframe: pd.DataFrame) -> int:
    """Conta registros de forma segura."""

    if dataframe is None or dataframe.empty:
        return 0

    return len(dataframe.index)


def _count_published(dataframe: pd.DataFrame) -> int:
    """
    Conta apenas registros publicáveis ou ativos.

    Caso a aba ainda não possua uma coluna de status
    preenchida, retorna zero para evitar publicar dados
    pendentes por engano.
    """

    if dataframe is None or dataframe.empty:
        return 0

    status_columns = [
        "Status",
        "Status revisão",
        "Status contingência",
    ]

    available_column = next(
        (
            column
            for column in status_columns
            if column in dataframe.columns
        ),
        None,
    )

    if available_column is None:
        return 0

    valid_statuses = {
        "ativo",
        "ativa",
        "publicável",
        "publicavel",
        "revisado",
    }

    normalized_status = (
        dataframe[available_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    return int(
        normalized_status.isin(valid_statuses).sum()
    )


def get_dashboard_summary() -> DashboardSummary:
    """Carrega os indicadores reais da Home."""

    operadoras = get_operadoras()
    planos = get_planos()
    comunicados = get_comunicados()
    contingencias = get_contingencias()

    return DashboardSummary(
        operadoras=_count_rows(operadoras),
        planos=_count_rows(planos),
        comunicados=_count_published(comunicados),
        contingencias=_count_published(contingencias),
    )

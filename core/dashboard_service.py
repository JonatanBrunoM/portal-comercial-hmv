from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd
import streamlit as st

from core.data_service import (
    get_comunicados_native,
    get_contingencias_native,
    get_operadoras_native,
    get_planos_native,
)
from utils.formatting import normalize_text


@dataclass(frozen=True)
class DashboardNotice:
    """Representa um comunicado resumido da Home."""

    notice_id: str
    title: str
    summary: str
    priority: str
    category: str
    operator_name: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class DashboardContingency:
    """Representa uma contingência resumida da Home."""

    contingency_id: str
    event: str
    operator_name: str
    priority: str
    status: str
    guidance: str
    unit: str


@dataclass(frozen=True)
class DashboardSummary:
    """Indicadores e destaques exibidos na Home."""

    operadoras: int
    planos: int
    comunicados: int
    contingencias: int
    notices: tuple[DashboardNotice, ...]
    contingency_items: tuple[DashboardContingency, ...]


def _safe_value(
    row: pd.Series,
    column: str,
) -> str:
    """Retorna o conteúdo de uma coluna sem gerar erro."""

    if column not in row.index:
        return ""

    value = row[column]

    if pd.isna(value):
        return ""

    return str(value).strip()


def _first_available(
    row: pd.Series,
    columns: list[str],
) -> str:
    """Retorna o primeiro campo preenchido da lista."""

    for column in columns:
        value = _safe_value(
            row,
            column,
        )

        if value:
            return value

    return ""


def _parse_date(
    value: object,
) -> pd.Timestamp | None:
    """Converte um valor para data."""

    if value is None or pd.isna(value):
        return None

    if isinstance(value, (date, datetime)):
        return pd.Timestamp(value).normalize()

    text = str(value).strip()

    if not text or text.casefold() == "nan":
        return None

    parsed = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=True,
    )

    if pd.isna(parsed):
        return None

    return pd.Timestamp(parsed).normalize()


def _format_date(
    value: object,
) -> str:
    """Formata uma data para exibição."""

    parsed = _parse_date(value)

    if parsed is None:
        return ""

    return parsed.strftime("%d/%m/%Y")


def _is_published_status(
    value: object,
) -> bool:
    """Identifica registros disponíveis para publicação."""

    status = normalize_text(value)

    return status in {
        "ativo",
        "ativa",
        "publicado",
        "publicada",
        "publicavel",
        "revisado",
        "validado",
        "validada",
    }


def _is_notice_active(
    row: pd.Series,
) -> bool:
    """Verifica status e vigência de um comunicado."""

    status = _first_available(
        row,
        [
            "status",
            "status",
            "status",
        ],
    )

    if not _is_published_status(status):
        return False

    today = pd.Timestamp.today().normalize()

    start_date = _parse_date(
        _first_available(
            row,
            [
                "inicio_em",
                "inicio_em",
            ],
        )
    )

    end_date = _parse_date(
        _first_available(
            row,
            [
                "fim_em",
                "fim_em",
            ],
        )
    )

    if start_date is not None and today < start_date:
        return False

    if end_date is not None and today > end_date:
        return False

    return True


def _is_contingency_active(
    row: pd.Series,
) -> bool:
    """Verifica se uma contingência pode aparecer na Home."""

    status = _first_available(
        row,
        [
            "status",
            "status",
            "status",
        ],
    )

    return _is_published_status(
        status
    )


def _priority_order(
    value: object,
) -> int:
    """Define a ordem de exibição por prioridade."""

    priority = normalize_text(value)

    order = {
        "alta": 0,
        "media": 1,
        "baixa": 2,
    }

    return order.get(
        priority,
        3,
    )


def _count_rows(
    dataframe: pd.DataFrame,
) -> int:
    """Conta registros com segurança."""

    if dataframe is None or dataframe.empty:
        return 0

    return len(dataframe.index)


def _build_notices(
    dataframe: pd.DataFrame,
) -> tuple[DashboardNotice, ...]:
    """Seleciona os comunicados ativos da Home."""

    if dataframe is None or dataframe.empty:
        return ()

    filtered = dataframe[
        dataframe.apply(
            _is_notice_active,
            axis=1,
        )
    ].copy()

    if filtered.empty:
        return ()

    filtered["_priority_order"] = filtered.apply(
        lambda row: _priority_order(
            _safe_value(
                row,
                "prioridade",
            )
        ),
        axis=1,
    )

    filtered["_date_sort"] = pd.to_datetime(
        filtered.get(
            "inicio_em",
            pd.Series(
                index=filtered.index,
                dtype="object",
            ),
        ),
        errors="coerce",
        dayfirst=True,
    )

    filtered = filtered.sort_values(
        by=[
            "_priority_order",
            "_date_sort",
        ],
        ascending=[
            True,
            False,
        ],
        na_position="last",
    )

    notices: list[DashboardNotice] = []

    for index, row in filtered.head(
        3
    ).iterrows():
        notices.append(
            DashboardNotice(
                notice_id=(
                    _first_available(
                        row,
                        [
                            "id",
                            "id",
                        ],
                    )
                    or str(index)
                ),
                title=(
                    _safe_value(
                        row,
                        "titulo",
                    )
                    or "Comunicado sem título"
                ),
                summary=_first_available(
                    row,
                    [
                        "resumo",
                        "conteudo",
                    ],
                ),
                priority=(
                    _safe_value(
                        row,
                        "prioridade",
                    )
                    or "Não informada"
                ),
                category=(
                    _safe_value(
                        row,
                        "categoria",
                    )
                    or "Geral"
                ),
                operator_name=(
                    _first_available(
                        row,
                        [
                            "operadora_nome",
                        ],
                    )
                    or "Comunicado geral"
                ),
                start_date=_format_date(
                    _first_available(
                        row,
                        [
                            "inicio_em",
                            "inicio_em",
                        ],
                    )
                ),
                end_date=_format_date(
                    _first_available(
                        row,
                        [
                            "fim_em",
                            "fim_em",
                        ],
                    )
                ),
            )
        )

    return tuple(notices)


def _build_contingencies(
    dataframe: pd.DataFrame,
) -> tuple[DashboardContingency, ...]:
    """Seleciona as contingências prioritárias da Home."""

    if dataframe is None or dataframe.empty:
        return ()

    filtered = dataframe[
        dataframe.apply(
            _is_contingency_active,
            axis=1,
        )
    ].copy()

    if filtered.empty:
        return ()

    filtered["_priority_order"] = filtered.apply(
        lambda row: _priority_order(
            _safe_value(
                row,
                "prioridade",
            )
        ),
        axis=1,
    )

    filtered = filtered.sort_values(
        by="_priority_order",
        ascending=True,
        na_position="last",
    )

    contingency_items: list[
        DashboardContingency
    ] = []

    for index, row in filtered.head(
        3
    ).iterrows():
        contingency_items.append(
            DashboardContingency(
                contingency_id=(
                    _first_available(
                        row,
                        [
                            "id",
                            "id",
                        ],
                    )
                    or str(index)
                ),
                event=(
                    _safe_value(
                        row,
                        "titulo",
                    )
                    or "Contingência sem identificação"
                ),
                operator_name=(
                    _first_available(
                        row,
                        [
                            "operadora_nome",
                        ],
                    )
                    or "Operadora não identificada"
                ),
                priority=(
                    _safe_value(
                        row,
                        "prioridade",
                    )
                    or "Não informada"
                ),
                status=(
                    _first_available(
                        row,
                        [
                            "status",
                            "status",
                            "status",
                        ],
                    )
                    or "Não informado"
                ),
                guidance=_safe_value(
                    row,
                    "orientacao_alternativa",
                ),
                unit=(
                    _safe_value(
                        row,
                        "local_nome",
                    )
                    or "Todas as unidades"
                ),
            )
        )

    return tuple(
        contingency_items
    )


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def get_dashboard_summary() -> DashboardSummary:
    """Carrega os indicadores e destaques da Home."""

    operadoras = get_operadoras_native()
    planos = get_planos_native()
    comunicados = get_comunicados_native()
    contingencias = get_contingencias_native()

    operator_names = {}
    if not operadoras.empty and {"id", "nome"}.issubset(operadoras.columns):
        operator_names = dict(zip(operadoras["id"].astype(str), operadoras["nome"].fillna("").astype(str)))

    if not comunicados.empty and "operadora_id" in comunicados.columns:
        comunicados = comunicados.copy()
        comunicados["operadora_nome"] = comunicados["operadora_id"].astype(str).map(operator_names).fillna("")

    if not contingencias.empty and "operadora_id" in contingencias.columns:
        contingencias = contingencias.copy()
        contingencias["operadora_nome"] = contingencias["operadora_id"].astype(str).map(operator_names).fillna("")

    notices = _build_notices(
        comunicados
    )

    contingency_items = (
        _build_contingencies(
            contingencias
        )
    )

    return DashboardSummary(
        operadoras=_count_rows(
            operadoras
        ),
        planos=_count_rows(
            planos
        ),
        comunicados=len(
            notices
        ),
        contingencias=len(
            contingency_items
        ),
        notices=notices,
        contingency_items=(
            contingency_items
        ),
    )

from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd
import streamlit as st

from config.settings import DATASETS
from core.data_service import (
    get_operadoras,
    get_planos,
    read_dataset,
)
from utils.formatting import normalize_text


@dataclass(frozen=True)
class QualityIssue:
    """Representa um problema encontrado na base."""

    issue_type: str
    severity: str
    column: str
    message: str
    affected_rows: int
    examples: tuple[str, ...]


@dataclass(frozen=True)
class QualityReport:
    """Resultado da análise de qualidade de uma conjunto de dados."""

    dataset_key: str
    dataset_name: str
    total_rows: int
    total_columns: int
    score: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    issues: tuple[QualityIssue, ...]


REQUIRED_COLUMNS = {
    "operadoras": [
        "ID Operadora",
        "Operadora",
        "Status",
    ],
    "planos": [
        "ID Plano",
        "ID Operadora",
        "Plano",
        "Status",
    ],
    "portais": [
        "ID Portal",
        "ID Operadora",
        "Nome do portal",
        "URL",
    ],
    "elegibilidade": [
        "ID Elegibilidade",
        "ID Operadora",
        "Tipo atendimento",
    ],
    "documentos": [
        "ID Documento",
        "ID Operadora",
        "Documento",
    ],
    "autorizacoes": [
        "ID Autorização",
        "ID Operadora",
        "Tipo atendimento",
    ],
    "coberturas": [
        "ID Cobertura",
        "ID Operadora",
        "Tipo atendimento",
    ],
    "contatos": [
        "ID Contato",
        "ID Operadora",
        "Finalidade",
        "Contato",
    ],
    "contingencias": [
        "ID Contingência",
        "ID Operadora",
        "Evento",
        "Prioridade",
    ],
    "dicas": [
        "ID Dica",
        "Título",
    ],
    "consultores": [
        "ID Consultor",
        "Nome",
    ],
    "carteiras": [
        "ID Consultor",
        "Operadora",
    ],
    "comunicados": [
        "ID Comunicado",
        "Título",
        "Prioridade",
    ],
    "forum_posts": [
        "ID Post",
        "Título",
        "Conteúdo",
    ],
    "forum_comentarios": [
        "ID Comentário",
        "ID Post",
        "Comentário",
    ],
    "conhecimento": [
        "ID Conhecimento",
        "Pergunta",
        "Resposta",
        "Fonte",
    ],
    "particular": [
        "ID Particular",
        "Categoria",
        "Título",
        "Status",
    ],
}


ID_COLUMNS = {
    "operadoras": "ID Operadora",
    "planos": "ID Plano",
    "portais": "ID Portal",
    "elegibilidade": "ID Elegibilidade",
    "documentos": "ID Documento",
    "autorizacoes": "ID Autorização",
    "coberturas": "ID Cobertura",
    "contatos": "ID Contato",
    "contingencias": "ID Contingência",
    "dicas": "ID Dica",
    "consultores": "ID Consultor",
    "comunicados": "ID Comunicado",
    "forum_posts": "ID Post",
    "forum_comentarios": "ID Comentário",
    "conhecimento": "ID Conhecimento",
    "particular": "ID Particular",
}


URL_COLUMNS = {
    "portais": [
        "URL",
    ],
    "documentos": [
        "Link Documento",
    ],
    "comunicados": [
        "Link",
    ],
    "particular": [
        "Link",
    ],
}


def _empty_mask(
    series: pd.Series,
) -> pd.Series:
    """Identifica valores vazios ou equivalentes a vazio."""

    normalized = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return (
        normalized.eq("")
        | normalized.str.casefold().eq("nan")
        | normalized.str.casefold().eq("none")
    )


def _examples(
    dataframe: pd.DataFrame,
    mask: pd.Series,
    identification_column: str | None,
    limit: int = 5,
) -> tuple[str, ...]:
    """Retorna exemplos dos registros afetados."""

    affected = dataframe.loc[
        mask
    ]

    if affected.empty:
        return ()

    if (
        identification_column
        and identification_column
        in affected.columns
    ):
        values = (
            affected[identification_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        examples = [
            value
            for value in values
            if value
        ]

        if examples:
            return tuple(
                examples[:limit]
            )

    return tuple(
        f"Linha {index + 2}"
        for index in affected.index[:limit]
    )


def _is_valid_url(
    value: object,
) -> bool:
    """Valida URLs HTTP e HTTPS."""

    text = str(value or "").strip()

    if not text:
        return True

    return bool(
        re.match(
            r"^https?://[^\s]+$",
            text,
            flags=re.IGNORECASE,
        )
    )


def _add_missing_required_issues(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
    dataset_key: str,
    id_column: str | None,
) -> None:
    """Analisa campos obrigatórios ausentes ou vazios."""

    for column in REQUIRED_COLUMNS.get(
        dataset_key,
        [],
    ):
        if column not in dataframe.columns:
            issues.append(
                QualityIssue(
                    issue_type="Coluna ausente",
                    severity="Crítico",
                    column=column,
                    message=(
                        f"A coluna obrigatória "
                        f"'{column}' não existe na conjunto de dados."
                    ),
                    affected_rows=len(dataframe),
                    examples=(),
                )
            )
            continue

        mask = _empty_mask(
            dataframe[column]
        )

        count = int(
            mask.sum()
        )

        if count:
            issues.append(
                QualityIssue(
                    issue_type="Campo obrigatório vazio",
                    severity="Crítico",
                    column=column,
                    message=(
                        f"{count} registro(s) possuem "
                        f"o campo '{column}' vazio."
                    ),
                    affected_rows=count,
                    examples=_examples(
                        dataframe=dataframe,
                        mask=mask,
                        identification_column=id_column,
                    ),
                )
            )


def _add_duplicate_id_issue(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
    id_column: str | None,
) -> None:
    """Identifica IDs duplicados."""

    if (
        not id_column
        or id_column not in dataframe.columns
    ):
        return

    values = (
        dataframe[id_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    valid_values = values.ne("")

    duplicated = (
        values.duplicated(
            keep=False
        )
        & valid_values
    )

    count = int(
        duplicated.sum()
    )

    if not count:
        return

    duplicated_ids = tuple(
        values[
            duplicated
        ]
        .drop_duplicates()
        .head(5)
        .tolist()
    )

    issues.append(
        QualityIssue(
            issue_type="ID duplicado",
            severity="Crítico",
            column=id_column,
            message=(
                f"{count} linha(s) possuem "
                f"identificadores duplicados."
            ),
            affected_rows=count,
            examples=duplicated_ids,
        )
    )


def _add_duplicate_rows_issue(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
) -> None:
    """Identifica linhas completamente duplicadas."""

    duplicated = dataframe.duplicated(
        keep=False
    )

    count = int(
        duplicated.sum()
    )

    if count:
        issues.append(
            QualityIssue(
                issue_type="Linha duplicada",
                severity="Alerta",
                column="Todas",
                message=(
                    f"{count} linha(s) estão "
                    f"completamente duplicadas."
                ),
                affected_rows=count,
                examples=tuple(
                    f"Linha {index + 2}"
                    for index in dataframe[
                        duplicated
                    ].index[:5]
                ),
            )
        )


def _add_url_issues(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
    dataset_key: str,
    id_column: str | None,
) -> None:
    """Identifica links preenchidos em formato inválido."""

    for column in URL_COLUMNS.get(
        dataset_key,
        [],
    ):
        if column not in dataframe.columns:
            continue

        invalid_mask = ~dataframe[
            column
        ].map(
            _is_valid_url
        )

        count = int(
            invalid_mask.sum()
        )

        if count:
            issues.append(
                QualityIssue(
                    issue_type="Link inválido",
                    severity="Alerta",
                    column=column,
                    message=(
                        f"{count} registro(s) possuem "
                        f"link inválido em '{column}'."
                    ),
                    affected_rows=count,
                    examples=_examples(
                        dataframe=dataframe,
                        mask=invalid_mask,
                        identification_column=id_column,
                    ),
                )
            )


def _add_status_issues(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
    id_column: str | None,
) -> None:
    """Analisa status de publicação e revisão."""

    status_column = next(
        (
            column
            for column in [
                "Status revisão",
                "Status publicação",
                "Status contingência",
                "Status",
            ]
            if column in dataframe.columns
        ),
        None,
    )

    if not status_column:
        return

    normalized = (
        dataframe[status_column]
        .fillna("")
        .astype(str)
        .map(normalize_text)
    )

    pending_mask = normalized.isin(
        {
            "",
            "pendente",
            "em revisao",
            "em validacao",
        }
    )

    pending_count = int(
        pending_mask.sum()
    )

    if pending_count:
        issues.append(
            QualityIssue(
                issue_type="Revisão pendente",
                severity="Alerta",
                column=status_column,
                message=(
                    f"{pending_count} registro(s) ainda "
                    f"não foram revisados ou validados."
                ),
                affected_rows=pending_count,
                examples=_examples(
                    dataframe=dataframe,
                    mask=pending_mask,
                    identification_column=id_column,
                ),
            )
        )

    inactive_mask = normalized.isin(
        {
            "inativo",
            "inativa",
            "excluido",
            "excluida",
            "reprovado",
            "reprovada",
        }
    )

    inactive_count = int(
        inactive_mask.sum()
    )

    if inactive_count:
        issues.append(
            QualityIssue(
                issue_type="Registro inativo",
                severity="Informativo",
                column=status_column,
                message=(
                    f"{inactive_count} registro(s) estão "
                    f"inativos ou indisponíveis."
                ),
                affected_rows=inactive_count,
                examples=_examples(
                    dataframe=dataframe,
                    mask=inactive_mask,
                    identification_column=id_column,
                ),
            )
        )


def _add_operator_link_issues(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
    id_column: str | None,
) -> None:
    """Identifica IDs de operadoras inexistentes."""

    if "ID Operadora" not in dataframe.columns:
        return

    operadoras = get_operadoras()

    if (
        operadoras.empty
        or "ID Operadora" not in operadoras.columns
    ):
        return

    valid_ids = set(
        operadoras["ID Operadora"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    values = (
        dataframe["ID Operadora"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    invalid_mask = (
        values.ne("")
        & ~values.isin(valid_ids)
    )

    count = int(
        invalid_mask.sum()
    )

    if count:
        issues.append(
            QualityIssue(
                issue_type="Operadora inexistente",
                severity="Crítico",
                column="ID Operadora",
                message=(
                    f"{count} registro(s) estão vinculados "
                    f"a uma operadora inexistente."
                ),
                affected_rows=count,
                examples=_examples(
                    dataframe=dataframe,
                    mask=invalid_mask,
                    identification_column=id_column,
                ),
            )
        )


def _add_plan_link_issues(
    issues: list[QualityIssue],
    dataframe: pd.DataFrame,
    id_column: str | None,
) -> None:
    """Identifica IDs de planos inexistentes."""

    if "ID Plano" not in dataframe.columns:
        return

    planos = get_planos()

    if (
        planos.empty
        or "ID Plano" not in planos.columns
    ):
        return

    valid_ids = set(
        planos["ID Plano"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    values = (
        dataframe["ID Plano"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    invalid_mask = (
        values.ne("")
        & ~values.isin(valid_ids)
    )

    count = int(
        invalid_mask.sum()
    )

    if count:
        issues.append(
            QualityIssue(
                issue_type="Plano inexistente",
                severity="Crítico",
                column="ID Plano",
                message=(
                    f"{count} registro(s) estão vinculados "
                    f"a um plano inexistente."
                ),
                affected_rows=count,
                examples=_examples(
                    dataframe=dataframe,
                    mask=invalid_mask,
                    identification_column=id_column,
                ),
            )
        )


def _calculate_score(
    issues: list[QualityIssue],
    total_rows: int,
) -> int:
    """Calcula uma nota simples de qualidade entre 0 e 100."""

    if total_rows == 0:
        return 0

    penalty = 0

    for issue in issues:
        severity_penalty = {
            "Crítico": 15,
            "Alerta": 7,
            "Informativo": 2,
        }.get(
            issue.severity,
            0,
        )

        affected_ratio = min(
            1.0,
            issue.affected_rows
            / max(
                total_rows,
                1,
            ),
        )

        penalty += int(
            severity_penalty
            * max(
                affected_ratio,
                0.25,
            )
        )

    return max(
        0,
        100 - penalty,
    )


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def analyze_dataset_quality(
    dataset_key: str,
) -> QualityReport:
    """Executa o diagnóstico de qualidade de uma conjunto de dados."""

    if dataset_key not in DATASETS:
        raise ValueError(
            f"Módulo desconhecido: {dataset_key}"
        )

    dataset_name = DATASETS[
        dataset_key
    ]

    dataframe = read_dataset(
        dataset=dataset_name,
        ttl=600,
    )

    id_column = ID_COLUMNS.get(
        dataset_key
    )

    issues: list[QualityIssue] = []

    _add_missing_required_issues(
        issues=issues,
        dataframe=dataframe,
        dataset_key=dataset_key,
        id_column=id_column,
    )

    _add_duplicate_id_issue(
        issues=issues,
        dataframe=dataframe,
        id_column=id_column,
    )

    _add_duplicate_rows_issue(
        issues=issues,
        dataframe=dataframe,
    )

    _add_url_issues(
        issues=issues,
        dataframe=dataframe,
        dataset_key=dataset_key,
        id_column=id_column,
    )

    _add_status_issues(
        issues=issues,
        dataframe=dataframe,
        id_column=id_column,
    )

    if dataset_key not in {
        "operadoras",
        "consultores",
        "comunicados",
        "forum_posts",
        "forum_comentarios",
        "conhecimento",
        "particular",
    }:
        _add_operator_link_issues(
            issues=issues,
            dataframe=dataframe,
            id_column=id_column,
        )

    if dataset_key not in {
        "operadoras",
        "planos",
        "consultores",
        "carteiras",
        "comunicados",
        "forum_posts",
        "forum_comentarios",
        "conhecimento",
        "particular",
    }:
        _add_plan_link_issues(
            issues=issues,
            dataframe=dataframe,
            id_column=id_column,
        )

    critical_issues = sum(
        issue.severity == "Crítico"
        for issue in issues
    )

    warning_issues = sum(
        issue.severity == "Alerta"
        for issue in issues
    )

    info_issues = sum(
        issue.severity == "Informativo"
        for issue in issues
    )

    score = _calculate_score(
        issues=issues,
        total_rows=len(dataframe),
    )

    return QualityReport(
        dataset_key=dataset_key,
        dataset=dataset_name,
        total_rows=len(dataframe),
        total_columns=len(dataframe.columns),
        score=score,
        critical_issues=critical_issues,
        warning_issues=warning_issues,
        info_issues=info_issues,
        issues=tuple(issues),
    )

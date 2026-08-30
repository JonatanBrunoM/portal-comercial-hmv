from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st
import logging

from config.settings import CACHE_SETTINGS
from core.data_service import (
    get_autorizacoes,
    get_coberturas,
    get_contatos,
    get_contingencias,
    get_dicas_operacionais,
    get_documentos,
    get_elegibilidade,
    get_operadoras,
    get_planos,
    get_portais,
)
from utils.formatting import normalize_text, shorten_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    """Representa um resultado da pesquisa global."""

    result_id: str
    category: str
    title: str
    subtitle: str
    description: str
    operator_id: str
    plan_id: str
    relevance: int
    source_dataset: str


SEARCH_SYNONYMS = {
    "rm": [
        "ressonancia",
        "ressonancia magnetica",
    ],
    "pet": [
        "pet scan",
        "pet ct",
        "petscan",
    ],
    "senha": [
        "autorizacao",
        "autorizacao previa",
    ],
    "convenio": [
        "operadora",
    ],
    "telefone": [
        "contato",
        "fone",
    ],
    "guia": [
        "documento",
        "guia tiss",
    ],
    "material especial": [
        "opme",
        "ortese",
        "protese",
    ],
}


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
        value = _safe_value(row, column)

        if value:
            return value

    return ""


def _expand_query(query: str) -> list[str]:
    """Expande a consulta usando sinônimos conhecidos."""

    normalized_query = normalize_text(query)

    terms = {
        normalized_query,
    }

    words = normalized_query.split()

    terms.update(words)

    for key, synonyms in SEARCH_SYNONYMS.items():
        normalized_key = normalize_text(key)

        if (
            normalized_key in normalized_query
            or normalized_query in normalized_key
        ):
            terms.update(
                normalize_text(synonym)
                for synonym in synonyms
            )

        for synonym in synonyms:
            normalized_synonym = normalize_text(synonym)

            if (
                normalized_synonym in normalized_query
                or normalized_query in normalized_synonym
            ):
                terms.add(normalized_key)
                terms.update(
                    normalize_text(item)
                    for item in synonyms
                )

    return [
        term
        for term in terms
        if term
    ]


def _calculate_relevance(
    query: str,
    terms: list[str],
    title: str,
    subtitle: str,
    description: str,
) -> int:
    """Calcula a relevância básica do resultado."""

    normalized_query = normalize_text(query)
    normalized_title = normalize_text(title)
    normalized_subtitle = normalize_text(subtitle)
    normalized_description = normalize_text(description)

    score = 0

    if normalized_query == normalized_title:
        score += 100

    elif normalized_query in normalized_title:
        score += 70

    if normalized_query in normalized_subtitle:
        score += 40

    if normalized_query in normalized_description:
        score += 25

    for term in terms:
        if term in normalized_title:
            score += 15

        if term in normalized_subtitle:
            score += 8

        if term in normalized_description:
            score += 4

    return score


def _create_result(
    *,
    query: str,
    terms: list[str],
    result_id: str,
    category: str,
    title: str,
    subtitle: str,
    description: str,
    operator_id: str,
    plan_id: str,
    source_dataset: str,
) -> SearchResult | None:
    """Cria um resultado apenas quando houver correspondência."""

    relevance = _calculate_relevance(
        query=query,
        terms=terms,
        title=title,
        subtitle=subtitle,
        description=description,
    )

    if relevance <= 0:
        return None

    return SearchResult(
        result_id=result_id,
        category=category,
        title=title or "Informação sem título",
        subtitle=subtitle,
        description=shorten_text(description),
        operator_id=operator_id,
        plan_id=plan_id,
        relevance=relevance,
        source_dataset=source_dataset,
    )


def _safe_load_dataset(
    loader,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Carrega uma conjunto sem derrubar toda a pesquisa.

    Se uma conjunto falhar, registra o erro e retorna
    um DataFrame vazio.
    """

    try:
        return loader()

    except Exception as error:
        logger.exception(
            "Não foi possível carregar o conjunto %s.",
            dataset_name,
        )

        return pd.DataFrame()

@st.cache_data(
    ttl=CACHE_SETTINGS.SEARCH_INDEX,
    show_spinner=False,
)

def build_search_index() -> list[dict]:
    """
    Monta um índice único com as informações pesquisáveis.

    O retorno utiliza dicionários para permitir cache seguro.
    """

    items: list[dict] = []

    datasets = [
        (
            "Operadoras",
            "02_OPERADORAS",
            _safe_load_dataset(
                get_operadoras,
                "Operadoras",
            ),
            "ID Operadora",
            ["Nome curto", "Operadora"],
            ["Operadora"],
            ["Observações"],
            "ID Operadora",
            "",
        ),
        (
            "Planos",
            "03_PLANOS",
            _safe_load_dataset(
                get_planos,
                "Planos",
            ),
            "ID Plano",
            ["Nome padronizado", "Plano"],
            ["Unidade", "Tipo do plano"],
            ["Observação resumida"],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Portais",
            "04_PORTAIS",
            _safe_load_dataset(
                get_portais,
                "Portais",
            ),
            "ID Portal",
            ["Nome do portal"],
            ["Tipo", "Unidade"],
            ["Instrução de acesso", "Observações", "URL"],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Elegibilidade",
            "05_ELEGIBILIDADE",
            _safe_load_dataset(
                get_elegibilidade,
                "Elegibilidade",
            ),
            "ID Elegibilidade",
            ["Tipo atendimento"],
            ["Unidade"],
            [
                "Como verificar",
                "Documento necessário",
                "Observações",
            ],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Documentos",
            "06_DOCUMENTOS",
            _safe_load_dataset(
                get_documentos,
                "Documentos",
            ),
            "ID Documento",
            ["Documento"],
            ["Tipo atendimento", "Unidade"],
            [
                "Observações",
                "Original/Cópia",
                "Validade em dias",
            ],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Autorizações",
            "07_AUTORIZACOES",
            _safe_load_dataset(
                get_autorizacoes,
                "Autorizações",
            ),
            "ID Autorização",
            ["Tipo atendimento"],
            ["Meio de solicitação", "Unidade"],
            [
                "Quem solicita",
                "Observações",
                "Pré/Pós",
            ],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Coberturas",
            "08_COBERTURAS",
            _safe_load_dataset(
                get_coberturas,
                "Coberturas",
            ),
            "ID Cobertura",
            ["Tipo atendimento"],
            ["Coberto", "Unidade"],
            [
                "Restrição",
                "Observações",
                "Acomodação",
            ],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Contatos",
            "09_CONTATOS",
            _safe_load_dataset(
                get_contatos,
                "Contatos",
            ),
            "ID Contato",
            ["Nome/Setor", "Finalidade"],
            ["Tipo", "Contato"],
            [
                "Responsável",
                "Horário atendimento",
                "Observações",
            ],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Contingências",
            "10_CONTINGENCIAS",
            _safe_load_dataset(
                get_contingencias,
                "Contingências",
            ),
            "ID Contingência",
            ["Evento"],
            ["Prioridade", "Unidade"],
            [
                "Orientação alternativa",
                "Observações",
            ],
            "ID Operadora",
            "ID Plano",
        ),
        (
            "Dicas operacionais",
            "11_DICAS_OPERACIONAIS",
            _safe_load_dataset(
                get_dicas_operacionais,
                "Dicas operacionais",
            ),
            "ID Dica",
            ["Título", "Categoria"],
            ["Unidade", "Palavras-chave"],
            ["Dica operacional"],
            "ID Operadora",
            "ID Plano",
        ),
    ]

    for (
        category,
        source_dataset,
        dataframe,
        id_column,
        title_columns,
        subtitle_columns,
        description_columns,
        operator_column,
        plan_column,
    ) in datasets:
        if dataframe is None or dataframe.empty:
            continue

        for _, row in dataframe.iterrows():
            title = _first_available(
                row,
                title_columns,
            )

            subtitle_values = [
                _safe_value(row, column)
                for column in subtitle_columns
            ]

            description_values = [
                _safe_value(row, column)
                for column in description_columns
            ]

            subtitle = " • ".join(
                value
                for value in subtitle_values
                if value
            )

            description = " | ".join(
                value
                for value in description_values
                if value
            )

            items.append(
                {
                    "result_id": _safe_value(
                        row,
                        id_column,
                    ),
                    "category": category,
                    "title": title,
                    "subtitle": subtitle,
                    "description": description,
                    "operator_id": _safe_value(
                        row,
                        operator_column,
                    ),
                    "plan_id": (
                        _safe_value(
                            row,
                            plan_column,
                        )
                        if plan_column
                        else ""
                    ),
                    "source_dataset": source_dataset,
                }
            )

    return items


def search_global(
    query: str,
    limit: int = 30,
) -> list[SearchResult]:
    """Pesquisa em todos os módulos indexados."""

    normalized_query = normalize_text(query)

    if len(normalized_query) < 2:
        return []

    terms = _expand_query(
        query,
    )

    results: list[SearchResult] = []

    for item in build_search_index():
        result = _create_result(
            query=query,
            terms=terms,
            result_id=item["result_id"],
            category=item["category"],
            title=item["title"],
            subtitle=item["subtitle"],
            description=item["description"],
            operator_id=item["operator_id"],
            plan_id=item["plan_id"],
            source_dataset=item["source_dataset"],
        )

        if result is not None:
            results.append(result)

    results.sort(
        key=lambda item: (
            -item.relevance,
            item.category,
            item.title,
        )
    )

    return results[:limit]

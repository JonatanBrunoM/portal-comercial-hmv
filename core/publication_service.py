from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from config.settings import SHEETS
from core.sheets_service import read_worksheet
from utils.formatting import normalize_text


@dataclass(frozen=True)
class PublicationSummary:
    """Resumo da situação de publicação de uma aba."""

    sheet_key: str
    worksheet: str
    total: int
    ready: int
    pending: int
    inactive: int
    unidentified: int
    dataframe: pd.DataFrame


PUBLICATION_RULES = {
    "operadoras": {
        "id_column": "ID Operadora",
        "title_columns": [
            "Nome curto",
            "Operadora",
        ],
        "required_columns": [
            "ID Operadora",
            "Operadora",
            "Status",
        ],
    },
    "planos": {
        "id_column": "ID Plano",
        "title_columns": [
            "Nome padronizado",
            "Plano",
        ],
        "required_columns": [
            "ID Plano",
            "ID Operadora",
            "Plano",
            "Status",
        ],
    },
    "portais": {
        "id_column": "ID Portal",
        "title_columns": [
            "Nome do portal",
        ],
        "required_columns": [
            "ID Portal",
            "ID Operadora",
            "Nome do portal",
            "URL",
        ],
    },
    "elegibilidade": {
        "id_column": "ID Elegibilidade",
        "title_columns": [
            "Tipo atendimento",
        ],
        "required_columns": [
            "ID Elegibilidade",
            "ID Operadora",
            "Tipo atendimento",
            "Como verificar",
        ],
    },
    "documentos": {
        "id_column": "ID Documento",
        "title_columns": [
            "Documento",
        ],
        "required_columns": [
            "ID Documento",
            "ID Operadora",
            "Documento",
        ],
    },
    "autorizacoes": {
        "id_column": "ID Autorização",
        "title_columns": [
            "Tipo atendimento",
        ],
        "required_columns": [
            "ID Autorização",
            "ID Operadora",
            "Tipo atendimento",
        ],
    },
    "coberturas": {
        "id_column": "ID Cobertura",
        "title_columns": [
            "Tipo atendimento",
        ],
        "required_columns": [
            "ID Cobertura",
            "ID Operadora",
            "Tipo atendimento",
        ],
    },
    "contatos": {
        "id_column": "ID Contato",
        "title_columns": [
            "Finalidade",
            "Nome/Setor",
        ],
        "required_columns": [
            "ID Contato",
            "ID Operadora",
            "Finalidade",
            "Contato",
        ],
    },
    "contingencias": {
        "id_column": "ID Contingência",
        "title_columns": [
            "Evento",
        ],
        "required_columns": [
            "ID Contingência",
            "Evento",
            "Prioridade",
            "Orientação alternativa",
        ],
    },
    "dicas": {
        "id_column": "ID Dica",
        "title_columns": [
            "Título",
            "Categoria",
        ],
        "required_columns": [
            "ID Dica",
            "Título",
            "Dica operacional",
        ],
    },
    "consultores": {
        "id_column": "ID Consultor",
        "title_columns": [
            "Nome",
        ],
        "required_columns": [
            "ID Consultor",
            "Nome",
            "Status",
        ],
    },
    "comunicados": {
        "id_column": "ID Comunicado",
        "title_columns": [
            "Título",
        ],
        "required_columns": [
            "ID Comunicado",
            "Título",
            "Conteúdo",
            "Prioridade",
        ],
    },
    "forum_posts": {
        "id_column": "ID Post",
        "title_columns": [
            "Título",
        ],
        "required_columns": [
            "ID Post",
            "Título",
            "Conteúdo",
        ],
    },
    "conhecimento": {
        "id_column": "ID Conhecimento",
        "title_columns": [
            "Pergunta canônica",
            "Pergunta",
        ],
        "required_columns": [
            "ID Conhecimento",
            "Pergunta",
            "Resposta",
            "Fonte",
        ],
    },
    "particular": {
        "id_column": "ID Particular",
        "title_columns": [
            "Título",
        ],
        "required_columns": [
            "ID Particular",
            "Categoria",
            "Título",
            "Orientação completa",
            "Status",
        ],
    },
}


READY_STATUSES = {
    "ativo",
    "ativa",
    "publicado",
    "publicada",
    "publicavel",
    "revisado",
    "revisada",
    "validado",
    "validada",
}


PENDING_STATUSES = {
    "pendente",
    "em revisao",
    "em validacao",
    "rascunho",
}


INACTIVE_STATUSES = {
    "inativo",
    "inativa",
    "reprovado",
    "reprovada",
    "excluido",
    "excluida",
    "oculto",
    "oculta",
}


def _safe_series(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Retorna uma coluna textual, mesmo quando ela não existe."""

    if column not in dataframe.columns:
        return pd.Series(
            "",
            index=dataframe.index,
            dtype="object",
        )

    return (
        dataframe[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


def _first_filled_series(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.Series:
    """Retorna o primeiro valor preenchido entre várias colunas."""

    result = pd.Series(
        "",
        index=dataframe.index,
        dtype="object",
    )

    for column in columns:
        values = _safe_series(
            dataframe,
            column,
        )

        empty_mask = result.eq("")

        result.loc[empty_mask] = (
            values.loc[empty_mask]
        )

    return result


def _find_status_series(
    dataframe: pd.DataFrame,
) -> pd.Series:
    """Localiza o status mais específico disponível."""

    status_columns = [
        "Status publicação",
        "Status contingência",
        "Status revisão",
        "Status",
    ]

    return _first_filled_series(
        dataframe,
        status_columns,
    )


def _is_empty(
    series: pd.Series,
) -> pd.Series:
    """Identifica valores vazios."""

    normalized = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    return normalized.isin(
        {
            "",
            "nan",
            "none",
        }
    )


def _build_missing_fields(
    dataframe: pd.DataFrame,
    required_columns: list[str],
) -> pd.Series:
    """Lista campos obrigatórios ausentes por registro."""

    missing_values: list[str] = []

    for _, row in dataframe.iterrows():
        missing_columns: list[str] = []

        for column in required_columns:
            if column not in row.index:
                missing_columns.append(
                    column
                )
                continue

            value = row[column]

            if pd.isna(value):
                missing_columns.append(
                    column
                )
                continue

            text = str(value).strip()

            if (
                not text
                or text.casefold()
                in {
                    "nan",
                    "none",
                }
            ):
                missing_columns.append(
                    column
                )

        missing_values.append(
            ", ".join(
                missing_columns
            )
        )

    return pd.Series(
        missing_values,
        index=dataframe.index,
        dtype="object",
    )


def _classify_status(
    normalized_status: str,
    missing_fields: str,
) -> str:
    """Classifica um registro para publicação."""

    if missing_fields:
        return "Incompleto"

    if normalized_status in READY_STATUSES:
        return "Pronto"

    if normalized_status in PENDING_STATUSES:
        return "Pendente"

    if normalized_status in INACTIVE_STATUSES:
        return "Inativo"

    return "Não identificado"


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def analyze_publication_status(
    sheet_key: str,
) -> PublicationSummary:
    """Analisa a prontidão de publicação de uma aba."""

    if sheet_key not in SHEETS:
        raise ValueError(
            f"Módulo desconhecido: {sheet_key}"
        )

    if sheet_key not in PUBLICATION_RULES:
        raise ValueError(
            "O módulo ainda não possui regras "
            "de publicação configuradas."
        )

    worksheet = SHEETS[
        sheet_key
    ]

    dataframe = read_worksheet(
        worksheet=worksheet,
        ttl=600,
    )

    rules = PUBLICATION_RULES[
        sheet_key
    ]

    result = dataframe.copy()

    if result.empty:
        return PublicationSummary(
            sheet_key=sheet_key,
            worksheet=worksheet,
            total=0,
            ready=0,
            pending=0,
            inactive=0,
            unidentified=0,
            dataframe=result,
        )

    result["_record_id"] = _safe_series(
        result,
        rules["id_column"],
    )

    result["_record_title"] = (
        _first_filled_series(
            result,
            rules["title_columns"],
        )
    )

    result["_status_original"] = (
        _find_status_series(
            result
        )
    )

    result["_status_normalized"] = (
        result["_status_original"]
        .map(normalize_text)
    )

    result["_missing_fields"] = (
        _build_missing_fields(
            result,
            rules["required_columns"],
        )
    )

    result["_publication_status"] = (
        result.apply(
            lambda row: _classify_status(
                normalized_status=row[
                    "_status_normalized"
                ],
                missing_fields=row[
                    "_missing_fields"
                ],
            ),
            axis=1,
        )
    )

    result["_record_title"] = (
        result["_record_title"]
        .replace(
            "",
            "Registro sem título",
        )
    )

    result["_record_id"] = (
        result["_record_id"]
        .replace(
            "",
            "Sem ID",
        )
    )

    status_order = {
        "Incompleto": 0,
        "Pendente": 1,
        "Não identificado": 2,
        "Pronto": 3,
        "Inativo": 4,
    }

    result["_status_order"] = (
        result["_publication_status"]
        .map(status_order)
        .fillna(5)
    )

    result = result.sort_values(
        by=[
            "_status_order",
            "_record_title",
        ],
        na_position="last",
    ).reset_index(
        drop=True
    )

    ready = int(
        result["_publication_status"]
        .eq("Pronto")
        .sum()
    )

    pending = int(
        result["_publication_status"]
        .isin(
            {
                "Pendente",
                "Incompleto",
            }
        )
        .sum()
    )

    inactive = int(
        result["_publication_status"]
        .eq("Inativo")
        .sum()
    )

    unidentified = int(
        result["_publication_status"]
        .eq("Não identificado")
        .sum()
    )

    return PublicationSummary(
        sheet_key=sheet_key,
        worksheet=worksheet,
        total=len(result),
        ready=ready,
        pending=pending,
        inactive=inactive,
        unidentified=unidentified,
        dataframe=result,
    )

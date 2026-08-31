from __future__ import annotations

from dataclasses import dataclass
import logging

import pandas as pd
import streamlit as st

from config.settings import CACHE_SETTINGS
from core.data_service import (
    get_autorizacoes, get_coberturas, get_contatos, get_contingencias,
    get_dicas_operacionais, get_documentos, get_elegibilidade,
    get_operadoras, get_planos, get_portais,
)
from utils.formatting import normalize_text, shorten_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
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
    "rm": ["ressonancia", "ressonancia magnetica"],
    "pet": ["pet scan", "pet ct", "petscan"],
    "convenio": ["operadora"],
    "telefone": ["contato", "fone"],
    "guia": ["documento", "guia tiss"],
    "senha": ["portal", "login", "acesso"],
    "material especial": ["opme", "ortese", "protese"],
}


def _safe(row: pd.Series, column: str) -> str:
    if column not in row.index or pd.isna(row[column]):
        return ""
    return str(row[column]).strip()


def _first(row: pd.Series, columns: list[str]) -> str:
    for column in columns:
        value = _safe(row, column)
        if value:
            return value
    return ""


def _safe_load(loader, name: str) -> pd.DataFrame:
    try:
        return loader()
    except Exception:
        logger.exception("Não foi possível carregar %s para a pesquisa.", name)
        return pd.DataFrame()


def _expand_query(query: str) -> list[str]:
    normalized = normalize_text(query)
    terms = {normalized, *normalized.split()}
    for key, synonyms in SEARCH_SYNONYMS.items():
        candidates = [key, *synonyms]
        normalized_candidates = [normalize_text(item) for item in candidates]
        if any(item and (item in normalized or normalized in item) for item in normalized_candidates):
            terms.update(normalized_candidates)
    return [term for term in terms if term]


def _relevance(query: str, terms: list[str], title: str, subtitle: str, description: str) -> int:
    q = normalize_text(query)
    t = normalize_text(title)
    s = normalize_text(subtitle)
    d = normalize_text(description)
    score = 0
    if q == t:
        score += 100
    elif q in t:
        score += 70
    if q in s:
        score += 40
    if q in d:
        score += 25
    for term in terms:
        score += 15 if term in t else 0
        score += 8 if term in s else 0
        score += 4 if term in d else 0
    return score


def _name_map(dataframe: pd.DataFrame, key: str = "id", name: str = "nome") -> dict[str, str]:
    if dataframe.empty or key not in dataframe.columns:
        return {}
    result = {}
    for _, row in dataframe.iterrows():
        item_id = _safe(row, key)
        if item_id:
            result[item_id] = _safe(row, name)
    return result


@st.cache_data(ttl=CACHE_SETTINGS.SEARCH_INDEX, show_spinner=False)
def build_search_index() -> list[dict]:
    operadoras = _safe_load(get_operadoras, "operadoras")
    planos = _safe_load(get_planos, "planos")
    operator_names = _name_map(operadoras)
    plan_names = _name_map(planos)
    items: list[dict] = []

    specs = [
        ("Operadoras", "operadoras", operadoras, ["nome_curto", "nome"], ["codigo"], ["observacoes", "site_url"]),
        ("Planos", "planos", planos, ["nome_padronizado", "nome"], ["tipo_plano"], ["observacao_resumida"]),
        ("Portais", "portais", _safe_load(get_portais, "portais"), ["nome"], ["tipo"], ["instrucao_acesso", "dica_geral_acesso", "observacoes", "url"]),
        ("Elegibilidade", "elegibilidade", _safe_load(get_elegibilidade, "elegibilidade"), ["orientacao"], ["necessario"], ["observacoes"]),
        ("Documentos", "documentos", _safe_load(get_documentos, "documentos"), ["nome"], ["formato"], ["orientacao", "observacoes"]),
        ("Autorizações", "autorizacoes", _safe_load(get_autorizacoes, "autorizacoes"), ["orientacao"], ["momento_autorizacao", "meio_solicitacao"], ["quem_solicita", "prazo", "observacoes"]),
        ("Coberturas", "coberturas", _safe_load(get_coberturas, "coberturas"), ["restricoes_cobertura", "acomodacao"], ["coberto"], ["acompanhante", "observacoes"]),
        ("Contatos", "contatos", _safe_load(get_contatos, "contatos"), ["nome_setor", "finalidade"], ["tipo", "contato"], ["responsavel", "horario_atendimento", "observacoes"]),
        ("Contingências", "contingencias", _safe_load(get_contingencias, "contingencias"), ["titulo"], ["prioridade"], ["descricao", "orientacao_alternativa", "contato_alternativo"]),
        ("Dicas operacionais", "dicas_operacionais", _safe_load(get_dicas_operacionais, "dicas_operacionais"), ["titulo", "categoria"], ["palavras_chave"], ["dica"]),
    ]

    for category, source, dataframe, title_cols, subtitle_cols, desc_cols in specs:
        if dataframe.empty:
            continue
        for index, row in dataframe.iterrows():
            operator_id = _safe(row, "operadora_id") or (_safe(row, "id") if source == "operadoras" else "")
            plan_id = _safe(row, "plano_id") or (_safe(row, "id") if source == "planos" else "")
            title = _first(row, title_cols) or f"{category} sem título"
            subtitle_parts = [operator_names.get(operator_id, ""), plan_names.get(plan_id, "")]
            subtitle_parts.extend(_safe(row, col) for col in subtitle_cols)
            description_parts = [_safe(row, col) for col in desc_cols]
            items.append({
                "result_id": _safe(row, "id") or str(index),
                "category": category,
                "title": title,
                "subtitle": " • ".join(dict.fromkeys(v for v in subtitle_parts if v)),
                "description": " | ".join(v for v in description_parts if v),
                "operator_id": operator_id,
                "plan_id": plan_id,
                "source_dataset": source,
            })
    return items


def search_global(query: str, limit: int = 30) -> list[SearchResult]:
    if len(normalize_text(query)) < 2:
        return []
    terms = _expand_query(query)
    results: list[SearchResult] = []
    for item in build_search_index():
        score = _relevance(query, terms, item["title"], item["subtitle"], item["description"])
        if score <= 0:
            continue
        results.append(SearchResult(
            result_id=item["result_id"], category=item["category"], title=item["title"],
            subtitle=item["subtitle"], description=shorten_text(item["description"]),
            operator_id=item["operator_id"], plan_id=item["plan_id"], relevance=score,
            source_dataset=item["source_dataset"],
        ))
    results.sort(key=lambda item: (-item.relevance, item.category, item.title))
    return results[:limit]

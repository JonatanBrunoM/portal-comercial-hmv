from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from config.settings import CACHE_SETTINGS
from core.data_service import (
    get_autorizacoes,
    get_carteiras,
    get_coberturas,
    get_comunicados,
    get_consultores,
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

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class SearchResult:
    result_id: str
    category: str
    title: str
    subtitle: str
    description: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    relevance: int
    source_dataset: str
    target_module: str


CATEGORY_ALIASES = {
    "Operadoras": {
        "operadora", "operadoras", "convenio", "convenios", "plano de saude"
    },
    "Planos": {
        "plano", "planos", "produto", "produtos"
    },
    "Portais": {
        "portal", "portais", "site", "acesso", "login", "senha",
        "credencial", "credenciais", "usuario"
    },
    "Elegibilidade": {
        "elegibilidade", "elegivel", "beneficiario", "carteira",
        "validar carteira", "validacao"
    },
    "Documentos": {
        "documento", "documentos", "guia", "guias", "formulario",
        "anexo", "pdf"
    },
    "Autorizações": {
        "autorizacao", "autorizacoes", "autorizar", "senha de autorizacao",
        "pre autorizacao", "preautorizacao"
    },
    "Coberturas": {
        "cobertura", "coberturas", "coberto", "acomodacao",
        "acompanhante", "restricao"
    },
    "Contatos": {
        "contato", "contatos", "telefone", "fone", "email",
        "central", "atendimento"
    },
    "Consultores": {
        "consultor", "consultores", "relacionamento", "comercial"
    },
    "Comunicados": {
        "comunicado", "comunicados", "aviso", "avisos",
        "atualizacao", "novidade"
    },
    "Contingências": {
        "contingencia", "contingencias", "indisponivel", "indisponibilidade",
        "instabilidade", "fora do ar", "manutencao", "alternativa"
    },
    "Dicas operacionais": {
        "dica", "dicas", "orientacao", "orientacoes", "como fazer",
        "procedimento", "operacional"
    },
}

STOPWORDS = {
    "a", "ao", "aos", "as", "como", "da", "das", "de", "do", "dos",
    "e", "em", "na", "nas", "no", "nos", "o", "os", "para", "por",
    "pra", "pro", "qual", "quais", "que", "um", "uma", "me", "eu",
    "preciso", "quero", "ver", "consultar", "saber", "fazer", "sobre",
}

TERM_SYNONYMS = {
    "rm": {"ressonancia", "ressonancia magnetica"},
    "ressonancia": {"rm", "ressonancia magnetica"},
    "pet": {"pet scan", "pet ct", "petscan"},
    "opme": {"material especial", "ortese", "protese"},
    "telefone": {"fone", "contato"},
    "fone": {"telefone", "contato"},
    "email": {"e mail", "contato"},
    "senha": {"login", "acesso", "credencial", "portal"},
    "login": {"senha", "acesso", "credencial", "portal"},
    "credencial": {"senha", "login", "acesso", "portal"},
    "guia": {"documento", "formulario"},
    "autorizar": {"autorizacao", "autorizacoes"},
    "autoriza": {"autorizacao", "autorizacoes"},
    "autorizado": {"autorizacao", "autorizacoes"},
    "elegivel": {"elegibilidade", "beneficiario"},
    "beneficiario": {"elegibilidade", "carteira"},
    "coberto": {"cobertura", "coberturas"},
    "cobrir": {"cobertura", "coberturas"},
    "documentacao": {"documento", "documentos", "guia"},
    "formulario": {"documento", "documentos", "guia"},
    "internacao": {"internacao", "hospitalar"},
    "urgencia": {"urgencia", "emergencia"},
    "emergencia": {"emergencia", "urgencia"},
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


def _name_map(dataframe: pd.DataFrame, key: str = "id", name: str = "nome") -> dict[str, str]:
    if dataframe.empty or key not in dataframe.columns:
        return {}

    result: dict[str, str] = {}
    for _, row in dataframe.iterrows():
        item_id = _safe(row, key)
        if item_id:
            result[item_id] = _safe(row, name)
    return result


def _date_only(value: object):
    if value is None or pd.isna(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None

    parsed = pd.Timestamp(parsed)
    if parsed.tzinfo is not None:
        parsed = parsed.tz_convert(BRAZIL_TZ).tz_localize(None)

    return parsed.date()


def _period_active(row: pd.Series) -> bool:
    today = datetime.now(BRAZIL_TZ).date()
    start = _date_only(row.get("inicio_em"))
    end = _date_only(row.get("fim_em"))
    return not ((start and today < start) or (end and today > end))


def _published_notice(row: pd.Series) -> bool:
    status = normalize_text(row.get("status"))
    return status in {"ativo", "publicado", "publicada"} and _period_active(row)


def _expand_tokens(query: str) -> tuple[list[str], set[str]]:
    normalized_query = normalize_text(query)
    base_tokens = [
        token
        for token in normalized_query.split()
        if len(token) >= 2 and token not in STOPWORDS
    ]
    expanded: set[str] = set(base_tokens)

    for token in list(base_tokens):
        expanded.update(normalize_text(item) for item in TERM_SYNONYMS.get(token, set()))

    for aliases in CATEGORY_ALIASES.values():
        normalized_aliases = {normalize_text(alias) for alias in aliases}
        if any(
            alias == normalized_query
            or alias in normalized_query
            or normalized_query in alias
            for alias in normalized_aliases
        ):
            expanded.update(normalized_aliases)

    return base_tokens, {item for item in expanded if item}


def _category_intents(query: str) -> set[str]:
    normalized_query = normalize_text(query)
    tokens = set(normalized_query.split())
    intents: set[str] = set()

    for category, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            alias_tokens = set(normalized_alias.split())

            if (
                normalized_alias == normalized_query
                or normalized_alias in normalized_query
                or (alias_tokens and alias_tokens.issubset(tokens))
            ):
                intents.add(category)
                break

    return intents


def _field_score(needle: str, haystack: str, exact: int, contains: int) -> int:
    if not needle or not haystack:
        return 0
    if needle == haystack:
        return exact
    if needle in haystack:
        return contains
    return 0


def _score_item(
    query: str,
    base_tokens: list[str],
    expanded_terms: set[str],
    category_intents: set[str],
    item: dict,
) -> int:
    q = normalize_text(query)
    title = normalize_text(item["title"])
    subtitle = normalize_text(item["subtitle"])
    description = normalize_text(item["description"])
    operator = normalize_text(item["operator_name"])
    plan = normalize_text(item["plan_name"])
    category = normalize_text(item["category"])
    keywords = normalize_text(item["keywords"])

    searchable = " ".join(
        value for value in [
            title, subtitle, description, operator, plan, category, keywords
        ] if value
    )

    # Evita resultados "soltos": cada palavra real digitada deve aparecer
    # no item ou em um sinônimo associado.
    missing = []
    for token in base_tokens:
        alternatives = {token, *{
            normalize_text(value)
            for value in TERM_SYNONYMS.get(token, set())
        }}

        # Também considera sinônimos reversos. Isso faz, por exemplo,
        # "autorizar" encontrar itens indexados como "autorização".
        for source_term, synonyms in TERM_SYNONYMS.items():
            normalized_synonyms = {normalize_text(value) for value in synonyms}
            if token in normalized_synonyms:
                alternatives.add(normalize_text(source_term))
                alternatives.update(normalized_synonyms)

        if not any(
            alternative and alternative in searchable
            for alternative in alternatives
        ):
            missing.append(token)

    # Consultas com intenção de categoria podem ter o token atendido
    # pela própria categoria, mesmo que o texto operacional não repita a palavra.
    if missing:
        unresolved = []
        for token in missing:
            token_categories = {
                category_name
                for category_name, aliases in CATEGORY_ALIASES.items()
                if any(
                    normalize_text(alias) == token
                    or token in normalize_text(alias)
                    for alias in aliases
                )
            }
            if not token_categories.intersection(category_intents).intersection({item["category"]}):
                unresolved.append(token)
        if unresolved:
            return 0

    score = 0

    score += _field_score(q, title, 180, 110)
    score += _field_score(q, operator, 170, 105)
    score += _field_score(q, plan, 150, 90)
    score += _field_score(q, subtitle, 120, 75)
    score += _field_score(q, description, 80, 45)

    if item["category"] in category_intents:
        score += 95

    # Associação da operadora é extremamente importante em consultas como
    # "bradesco autorização" ou "cassi telefone".
    for token in base_tokens:
        alternatives = {token, *{
            normalize_text(value) for value in TERM_SYNONYMS.get(token, set())
        }}
        if any(term in operator for term in alternatives):
            score += 65
        if any(term in plan for term in alternatives):
            score += 45
        if any(term in title for term in alternatives):
            score += 35
        if any(term in category for term in alternatives):
            score += 30
        if any(term in subtitle for term in alternatives):
            score += 22
        if any(term in description for term in alternatives):
            score += 14

    for term in expanded_terms:
        if term in title:
            score += 16
        elif term in subtitle:
            score += 10
        elif term in description or term in keywords:
            score += 6

    # Pequeno bônus para informações diretamente operacionais.
    if item["category"] in {
        "Portais", "Autorizações", "Elegibilidade", "Contatos",
        "Contingências", "Documentos"
    }:
        score += 6

    return score


def _add_item(
    items: list[dict],
    *,
    row: pd.Series,
    category: str,
    source_dataset: str,
    title_columns: list[str],
    subtitle_columns: list[str],
    description_columns: list[str],
    operator_names: dict[str, str],
    plan_names: dict[str, str],
    target_module: str,
    keywords: str = "",
    forced_operator_id: str = "",
) -> None:
    operator_id = forced_operator_id or _safe(row, "operadora_id")
    if source_dataset == "operadoras":
        operator_id = _safe(row, "id")

    plan_id = _safe(row, "plano_id")
    if source_dataset == "planos":
        plan_id = _safe(row, "id")

    operator_name = operator_names.get(operator_id, "")
    plan_name = plan_names.get(plan_id, "")

    title = _first(row, title_columns) or f"{category} sem título"

    subtitle_parts = [
        operator_name,
        plan_name,
        *[_safe(row, column) for column in subtitle_columns],
    ]

    description_parts = [_safe(row, column) for column in description_columns]

    items.append(
        {
            "result_id": _safe(row, "id"),
            "category": category,
            "title": title,
            "subtitle": " • ".join(dict.fromkeys(value for value in subtitle_parts if value)),
            "description": " | ".join(value for value in description_parts if value),
            "operator_id": operator_id,
            "operator_name": operator_name,
            "plan_id": plan_id,
            "plan_name": plan_name,
            "source_dataset": source_dataset,
            "target_module": target_module,
            "keywords": keywords,
        }
    )


@st.cache_data(ttl=CACHE_SETTINGS.SEARCH_INDEX, show_spinner=False)
def build_search_index() -> list[dict]:
    operadoras = _safe_load(get_operadoras, "operadoras")
    planos = _safe_load(get_planos, "planos")
    portais = _safe_load(get_portais, "portais")
    elegibilidade = _safe_load(get_elegibilidade, "elegibilidade")
    documentos = _safe_load(get_documentos, "documentos")
    autorizacoes = _safe_load(get_autorizacoes, "autorizacoes")
    coberturas = _safe_load(get_coberturas, "coberturas")
    contatos = _safe_load(get_contatos, "contatos")
    contingencias = _safe_load(get_contingencias, "contingencias")
    dicas = _safe_load(get_dicas_operacionais, "dicas_operacionais")
    comunicados = _safe_load(get_comunicados, "comunicados")
    consultores = _safe_load(get_consultores, "consultores")
    carteiras = _safe_load(get_carteiras, "carteiras")

    operator_names = _name_map(operadoras)
    plan_names = _name_map(planos)
    items: list[dict] = []

    specs = [
        (
            "Operadoras", "operadoras", operadoras,
            ["nome_curto", "nome"], ["codigo"],
            ["observacoes", "site_url"], "Visão geral",
            "convênio operadora plano de saúde",
        ),
        (
            "Planos", "planos", planos,
            ["nome_padronizado", "nome"], ["tipo_plano", "codigo"],
            ["observacao_resumida"], "Planos",
            "plano produto",
        ),
        (
            "Portais", "portais", portais,
            ["nome"], ["tipo"],
            ["instrucao_acesso", "dica_geral_acesso", "observacoes", "url"],
            "Portais e acessos",
            "portal acesso login senha credencial usuário site",
        ),
        (
            "Elegibilidade", "elegibilidade", elegibilidade,
            ["orientacao"], ["codigo"],
            ["observacoes"], "Elegibilidade",
            "elegibilidade elegível beneficiário carteira validação",
        ),
        (
            "Documentos", "documentos", documentos,
            ["nome"], ["formato", "codigo"],
            ["orientacao", "observacoes"], "Documentos",
            "documento guia formulário anexo arquivo",
        ),
        (
            "Autorizações", "autorizacoes", autorizacoes,
            ["orientacao"], ["momento_autorizacao", "meio_solicitacao"],
            ["quem_solicita", "prazo", "observacoes"], "Autorizações",
            "autorização autorizar pré autorização senha",
        ),
        (
            "Coberturas", "coberturas", coberturas,
            ["restricoes_cobertura", "acomodacao"], ["codigo"],
            ["acompanhante", "observacoes"], "Coberturas",
            "cobertura coberto restrição acomodação acompanhante",
        ),
        (
            "Contatos", "contatos", contatos,
            ["finalidade", "nome_setor"], ["tipo", "contato"],
            ["responsavel", "horario_atendimento", "observacoes"], "Contatos",
            "contato telefone fone e-mail email central atendimento",
        ),
        (
            "Contingências", "contingencias",
            contingencias[contingencias.apply(_period_active, axis=1)].copy()
            if not contingencias.empty else contingencias,
            ["titulo"], ["prioridade"],
            ["descricao", "orientacao_alternativa", "contato_alternativo"],
            "Contingências",
            "contingência indisponibilidade instabilidade manutenção fora do ar alternativa",
        ),
        (
            "Dicas operacionais", "dicas_operacionais", dicas,
            ["titulo", "categoria"], ["palavras_chave"],
            ["dica"], "Dicas",
            "dica orientação como fazer procedimento operacional",
        ),
        (
            "Comunicados", "comunicados",
            comunicados[comunicados.apply(_published_notice, axis=1)].copy()
            if not comunicados.empty else comunicados,
            ["titulo"], ["categoria", "prioridade"],
            ["resumo", "conteudo", "publico_alvo"], "Comunicados",
            "comunicado aviso atualização novidade",
        ),
    ]

    for (
        category,
        source,
        dataframe,
        title_columns,
        subtitle_columns,
        description_columns,
        target_module,
        keywords,
    ) in specs:
        if dataframe.empty:
            continue

        for _, row in dataframe.iterrows():
            _add_item(
                items,
                row=row,
                category=category,
                source_dataset=source,
                title_columns=title_columns,
                subtitle_columns=subtitle_columns,
                description_columns=description_columns,
                operator_names=operator_names,
                plan_names=plan_names,
                target_module=target_module,
                keywords=keywords,
            )

    # Consultores se relacionam à operadora por carteiras.
    if not consultores.empty and not carteiras.empty:
        consultant_by_id = {
            _safe(row, "id"): row
            for _, row in consultores.iterrows()
            if _safe(row, "id")
        }

        for _, carteira in carteiras.iterrows():
            consultant_id = _safe(carteira, "consultor_id")
            operator_id = _safe(carteira, "operadora_id")
            consultant = consultant_by_id.get(consultant_id)

            if consultant is None or not operator_id:
                continue

            _add_item(
                items,
                row=consultant,
                category="Consultores",
                source_dataset="consultores",
                title_columns=["nome"],
                subtitle_columns=["cargo", "email", "telefone"],
                description_columns=["observacoes"],
                operator_names=operator_names,
                plan_names=plan_names,
                target_module="Consultores",
                keywords="consultor relacionamento comercial telefone email contato",
                forced_operator_id=operator_id,
            )

    return items


def analyze_search_query(query: str) -> dict[str, object]:
    """Retorna metadados simples para orientar a apresentação dos resultados."""
    normalized = normalize_text(query)
    base_tokens, _ = _expand_tokens(query)
    intents = _category_intents(query)

    operator_names: list[str] = []
    operadoras = _safe_load(get_operadoras, "operadoras")
    if not operadoras.empty:
        for _, row in operadoras.iterrows():
            name = _first(row, ["nome_curto", "nome"])
            normalized_name = normalize_text(name)
            if normalized_name and (
                normalized_name in normalized
                or any(token in normalized_name for token in base_tokens)
            ):
                operator_names.append(name)

    return {
        "normalized_query": normalized,
        "tokens": base_tokens,
        "category_intents": sorted(intents),
        "operator_names": list(dict.fromkeys(operator_names)),
        "is_operator_only": bool(operator_names) and not intents and len(base_tokens) <= 2,
        "is_specific": bool(intents) or len(base_tokens) >= 2,
    }


def group_search_results(results: list[SearchResult]) -> dict[str, list[SearchResult]]:
    groups: dict[str, list[SearchResult]] = {}
    for result in results:
        groups.setdefault(result.category, []).append(result)
    return groups

def search_global(query: str, limit: int = 30) -> list[SearchResult]:
    normalized = normalize_text(query)
    if len(normalized) < 2:
        return []

    base_tokens, expanded_terms = _expand_tokens(query)
    intents = _category_intents(query)

    results: list[SearchResult] = []
    for item in build_search_index():
        score = _score_item(
            query=query,
            base_tokens=base_tokens,
            expanded_terms=expanded_terms,
            category_intents=intents,
            item=item,
        )

        if score <= 0:
            continue

        results.append(
            SearchResult(
                result_id=item["result_id"],
                category=item["category"],
                title=item["title"],
                subtitle=item["subtitle"],
                description=shorten_text(item["description"], limit=260),
                operator_id=item["operator_id"],
                operator_name=item["operator_name"],
                plan_id=item["plan_id"],
                plan_name=item["plan_name"],
                relevance=score,
                source_dataset=item["source_dataset"],
                target_module=item["target_module"],
            )
        )

    # Remove duplicatas funcionais, principalmente consultores vinculados
    # por múltiplas carteiras da mesma operadora.
    unique: dict[tuple[str, str, str], SearchResult] = {}
    for result in results:
        key = (result.result_id, result.category, result.operator_id)
        current = unique.get(key)
        if current is None or result.relevance > current.relevance:
            unique[key] = result

    ordered = list(unique.values())
    ordered.sort(
        key=lambda item: (
            -item.relevance,
            item.operator_name.casefold(),
            item.category.casefold(),
            item.title.casefold(),
        )
    )

    return ordered[:limit]

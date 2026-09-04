from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Any

from nicegui_app.repositories.pesquisa_repository import load_search_catalog


def normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _status(row: dict[str, Any]) -> str:
    return normalize(_text(row, "status"))

def _active(row: dict[str, Any]) -> bool:
    status = _status(row)
    return not status or status == "ativo"

def _published(row: dict[str, Any]) -> bool:
    return _status(row) == "publicado"

def _visible_contingency(row: dict[str, Any]) -> bool:
    return _status(row) in {"programada", "ativa"}


@dataclass(frozen=True, slots=True)
class SearchResult:
    result_id: str
    kind: str
    eyebrow: str
    title: str
    subtitle: str
    description: str
    route: str
    icon: str
    search_text: str


@dataclass(frozen=True, slots=True)
class RankedSearchResult:
    item: SearchResult
    score: float
    reason: str


@dataclass(frozen=True, slots=True)
class SearchResponse:
    query: str
    interpreted_as: tuple[str, ...]
    results: tuple[RankedSearchResult, ...]
    relaxed: bool = False


def _operator_maps(catalog: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, str], dict[str, str]]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto", "nome")
        for row in catalog["operadoras"]
        if _text(row, "id")
    }
    plans = {
        _text(row, "id"): _text(row, "nome_padronizado", "nome")
        for row in catalog["planos"]
        if _text(row, "id")
    }
    return operators, plans


def _result(
    row: dict[str, Any],
    *,
    kind: str,
    eyebrow: str,
    title: str,
    subtitle: str,
    description: str,
    route: str,
    icon: str,
) -> SearchResult:
    searchable = " ".join(
        str(value or "")
        for value in row.values()
        if not isinstance(value, (dict, list))
    )
    searchable = " ".join((searchable, title, subtitle, description, eyebrow))
    return SearchResult(
        result_id=_text(row, "id"),
        kind=kind,
        eyebrow=eyebrow,
        title=title,
        subtitle=subtitle,
        description=description,
        route=route,
        icon=icon,
        search_text=normalize(searchable),
    )


def get_search_catalog() -> list[SearchResult]:
    catalog = load_search_catalog()
    operators, plans = _operator_maps(catalog)
    results: list[SearchResult] = []

    for row in catalog["operadoras"]:
        if not _active(row):
            continue
        rid = _text(row, "id")
        results.append(_result(
            row,
            kind="Operadoras",
            eyebrow="OPERADORA",
            title=_text(row, "nome_curto", "nome") or "Operadora",
            subtitle=_text(row, "nome"),
            description=_text(row, "observacoes"),
            route=f"/operadoras/{rid}",
            icon="business",
        ))

    for row in catalog["planos"]:
        if not _active(row):
            continue
        oid = _text(row, "operadora_id")
        results.append(_result(
            row,
            kind="Planos",
            eyebrow="PLANO",
            title=_text(row, "nome_padronizado", "nome") or "Plano",
            subtitle=operators.get(oid, ""),
            description=_text(row, "observacao_resumida", "tipo_plano"),
            route=f"/operadoras/{oid}" if oid else "/operadoras",
            icon="health_and_safety",
        ))

    for row in catalog["portais"]:
        if not _active(row):
            continue
        rid = _text(row, "id")
        oid = _text(row, "operadora_id")
        pid = _text(row, "plano_id")
        results.append(_result(
            row,
            kind="Portais",
            eyebrow="PORTAL",
            title=_text(row, "nome") or "Portal",
            subtitle=" · ".join(v for v in (operators.get(oid, ""), plans.get(pid, ""), _text(row, "tipo")) if v),
            description=_text(row, "instrucao_acesso", "dica_geral_acesso", "observacoes"),
            route=f"/portais/{rid}",
            icon="language",
        ))

    for row in catalog["documentos"]:
        if not _active(row):
            continue
        rid = _text(row, "id")
        oid = _text(row, "operadora_id")
        results.append(_result(
            row,
            kind="Documentos",
            eyebrow="DOCUMENTO",
            title=_text(row, "nome") or "Documento",
            subtitle=operators.get(oid, ""),
            description=_text(row, "orientacao", "observacoes", "formato"),
            route=f"/documentos/{rid}",
            icon="description",
        ))

    for row in catalog["contatos"]:
        if not _active(row):
            continue
        rid = _text(row, "id")
        oid = _text(row, "operadora_id")
        results.append(_result(
            row,
            kind="Contatos",
            eyebrow="CONTATO",
            title=_text(row, "nome_setor", "finalidade") or "Contato",
            subtitle=" · ".join(v for v in (operators.get(oid, ""), _text(row, "finalidade")) if v),
            description=" · ".join(v for v in (_text(row, "contato"), _text(row, "responsavel"), _text(row, "horario_atendimento")) if v),
            route=f"/contatos/{rid}",
            icon="contacts",
        ))

    for row in catalog["consultores"]:
        if not _active(row):
            continue
        rid = _text(row, "id")
        results.append(_result(
            row,
            kind="Consultores",
            eyebrow="CONSULTOR",
            title=_text(row, "nome") or "Consultor",
            subtitle=_text(row, "cargo"),
            description=" · ".join(v for v in (_text(row, "email"), _text(row, "telefone")) if v),
            route=f"/consultores/{rid}",
            icon="support_agent",
        ))

    for row in catalog["comunicados"]:
        if not _published(row):
            continue
        rid = _text(row, "id")
        oid = _text(row, "operadora_id")
        results.append(_result(
            row,
            kind="Comunicados",
            eyebrow="COMUNICADO",
            title=_text(row, "titulo") or "Comunicado",
            subtitle=" · ".join(v for v in (operators.get(oid, "Geral / institucional"), _text(row, "categoria")) if v),
            description=_text(row, "resumo", "conteudo"),
            route=f"/comunicados/{rid}",
            icon="campaign",
        ))

    for row in catalog["contingencias"]:
        if not _visible_contingency(row):
            continue
        rid = _text(row, "id")
        oid = _text(row, "operadora_id")
        results.append(_result(
            row,
            kind="Contingências",
            eyebrow="CONTINGÊNCIA",
            title=_text(row, "titulo") or "Contingência",
            subtitle=" · ".join(v for v in (operators.get(oid, ""), _text(row, "prioridade")) if v),
            description=_text(row, "orientacao_alternativa", "descricao", "contato_alternativo"),
            route=f"/contingencias/{rid}",
            icon="warning_amber",
        ))


    for row in catalog["elegibilidade"]:
        if not _active(row): continue
        oid, pid = _text(row,"operadora_id"), _text(row,"plano_id")
        results.append(_result(row, kind="Elegibilidade", eyebrow="ELEGIBILIDADE", title=_text(row,"orientacao") or "Orientação de elegibilidade", subtitle=" · ".join(v for v in (operators.get(oid,""),plans.get(pid,"")) if v), description=_text(row,"observacoes","codigo"), route=f"/operadoras/{oid}" if oid else "/operadoras", icon="verified"))

    for row in catalog["autorizacoes"]:
        if not _active(row): continue
        oid, pid = _text(row,"operadora_id"), _text(row,"plano_id")
        results.append(_result(row, kind="Autorizações", eyebrow="AUTORIZAÇÃO", title=_text(row,"orientacao") or "Regra de autorização", subtitle=" · ".join(v for v in (operators.get(oid,""),plans.get(pid,""),_text(row,"momento_autorizacao")) if v), description=" · ".join(v for v in (_text(row,"quem_solicita"),_text(row,"meio_solicitacao"),_text(row,"prazo"),_text(row,"observacoes")) if v), route=f"/operadoras/{oid}" if oid else "/operadoras", icon="fact_check"))

    for row in catalog["coberturas"]:
        if not _active(row): continue
        oid, pid = _text(row,"operadora_id"), _text(row,"plano_id")
        results.append(_result(row, kind="Coberturas", eyebrow="COBERTURA", title=_text(row,"restricoes_cobertura","acomodacao") or "Informação de cobertura", subtitle=" · ".join(v for v in (operators.get(oid,""),plans.get(pid,"")) if v), description=" · ".join(v for v in (_text(row,"acomodacao"),_text(row,"acompanhante"),_text(row,"observacoes")) if v), route=f"/operadoras/{oid}" if oid else "/operadoras", icon="health_and_safety"))

    for row in catalog["dicas_operacionais"]:
        if not _active(row): continue
        oid, pid = _text(row,"operadora_id"), _text(row,"plano_id")
        results.append(_result(row, kind="Dicas operacionais", eyebrow="DICA OPERACIONAL", title=_text(row,"titulo") or "Dica operacional", subtitle=" · ".join(v for v in (operators.get(oid,""),plans.get(pid,""),_text(row,"categoria")) if v), description=_text(row,"dica","palavras_chave"), route=f"/operadoras/{oid}" if oid else "/operadoras", icon="lightbulb"))

    return results



# ---------------------------------------------------------------------------
# Pesquisa Inteligente
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "eu", "me", "meu", "minha", "na", "nas", "no", "nos", "o",
    "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "preciso",
    "quero", "qual", "quais", "que", "se", "sobre", "um", "uma",
}

_INTENT_ALIASES: dict[str, tuple[str, ...]] = {
    "Portais": (
        "acesso", "acessar", "entrar", "login", "logar", "portal", "site",
        "senha", "usuario", "credencial",
    ),
    "Autorizações": (
        "autorizar", "autorizacao", "autorizacoes", "guia", "liberacao",
        "liberar", "pre autorizacao", "preautorizacao",
    ),
    "Elegibilidade": (
        "elegibilidade", "elegivel", "elegibilidade do paciente", "validar carteira",
        "validar carteirinha", "carteira", "carteirinha",
    ),
    "Contatos": (
        "contato", "telefone", "ramal", "whatsapp", "email", "e-mail", "falar",
        "central", "atendimento",
    ),
    "Consultores": (
        "consultor", "consultora", "executivo", "executiva", "gestor da conta",
        "gerente da conta",
    ),
    "Documentos": (
        "documento", "documentos", "formulario", "formulário", "manual", "arquivo",
        "anexo", "termo",
    ),
    "Coberturas": (
        "cobertura", "coberto", "cobre", "acomodacao", "acomodação",
        "acompanhante", "restricao", "restrição",
    ),
    "Planos": (
        "plano", "planos", "produto", "produtos",
    ),
    "Operadoras": (
        "operadora", "operadoras", "convenio", "convênio", "convenios", "convênios",
    ),
    "Comunicados": (
        "comunicado", "comunicados", "aviso", "avisos", "novidade", "atualizacao",
        "atualização",
    ),
    "Contingências": (
        "contingencia", "contingência", "contingencias", "contingências",
        "indisponivel", "indisponível", "fora do ar", "instabilidade", "falha",
    ),
    "Dicas operacionais": (
        "dica", "dicas", "orientacao", "orientação", "procedimento", "como fazer",
    ),
}

_KIND_PRIORITY = {
    "Portais": 8,
    "Autorizações": 8,
    "Elegibilidade": 8,
    "Contatos": 7,
    "Documentos": 7,
    "Coberturas": 7,
    "Contingências": 7,
    "Operadoras": 6,
    "Planos": 6,
    "Consultores": 6,
    "Comunicados": 5,
    "Dicas operacionais": 5,
}


def _tokens(value: str) -> list[str]:
    normalized = normalize(value)
    return [
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) > 1 and token not in _STOPWORDS
    ]


def _intent_kinds(query: str) -> tuple[str, ...]:
    normalized_query = normalize(query)
    tokens = set(_tokens(query))
    found: list[str] = []

    for kind, aliases in _INTENT_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize(alias)
            alias_tokens = set(_tokens(normalized_alias))
            if (
                normalized_alias in normalized_query
                or (alias_tokens and alias_tokens.issubset(tokens))
            ):
                found.append(kind)
                break

    return tuple(found)


def _field_score(
    query_tokens: list[str],
    field: str,
    *,
    exact_weight: float,
    prefix_weight: float,
    fuzzy_weight: float,
) -> float:
    if not query_tokens or not field:
        return 0.0

    normalized_field = normalize(field)
    field_tokens = _tokens(field)
    score = 0.0

    for token in query_tokens:
        if token in field_tokens:
            score += exact_weight
            continue

        if any(candidate.startswith(token) or token.startswith(candidate) for candidate in field_tokens):
            score += prefix_weight
            continue

        best_ratio = max(
            (SequenceMatcher(None, token, candidate).ratio() for candidate in field_tokens),
            default=0.0,
        )
        if best_ratio >= 0.84:
            score += fuzzy_weight * best_ratio

    phrase = " ".join(query_tokens)
    if phrase and phrase in normalized_field:
        score += exact_weight * 1.35

    return score


def _operator_terms(results: list[SearchResult]) -> set[str]:
    terms: set[str] = set()
    for item in results:
        if item.kind != "Operadoras":
            continue
        for token in _tokens(f"{item.title} {item.subtitle}"):
            if len(token) >= 3:
                terms.add(token)
    return terms


def _rank_item(
    item: SearchResult,
    *,
    query: str,
    query_tokens: list[str],
    intent_kinds: tuple[str, ...],
    operator_terms: set[str],
) -> tuple[float, str, int]:
    title_score = _field_score(
        query_tokens,
        item.title,
        exact_weight=22,
        prefix_weight=15,
        fuzzy_weight=10,
    )
    subtitle_score = _field_score(
        query_tokens,
        item.subtitle,
        exact_weight=15,
        prefix_weight=10,
        fuzzy_weight=7,
    )
    description_score = _field_score(
        query_tokens,
        item.description,
        exact_weight=7,
        prefix_weight=4.5,
        fuzzy_weight=3,
    )
    body_score = _field_score(
        query_tokens,
        item.search_text,
        exact_weight=3.2,
        prefix_weight=2.2,
        fuzzy_weight=1.4,
    )

    score = title_score + subtitle_score + description_score + body_score

    normalized_query = normalize(query)
    normalized_title = normalize(item.title)
    normalized_subtitle = normalize(item.subtitle)

    if normalized_query == normalized_title:
        score += 90
    elif normalized_title.startswith(normalized_query):
        score += 52
    elif normalized_query and normalized_query in normalized_title:
        score += 34

    if normalized_query and normalized_query in normalized_subtitle:
        score += 16

    if item.kind in intent_kinds:
        score += 38 + _KIND_PRIORITY.get(item.kind, 0)

    # Quando a busca contém o nome de uma operadora, valoriza fortemente
    # registros relacionados a ela.
    query_operator_tokens = operator_terms.intersection(query_tokens)
    subtitle_tokens = set(_tokens(item.subtitle))
    title_tokens = set(_tokens(item.title))
    operator_hits = len(query_operator_tokens.intersection(subtitle_tokens | title_tokens))
    if operator_hits:
        score += 34 * operator_hits

    matched_tokens = 0
    searchable_tokens = set(_tokens(
        f"{item.title} {item.subtitle} {item.description} {item.search_text}"
    ))
    for token in query_tokens:
        if token in searchable_tokens:
            matched_tokens += 1
            continue
        best = max(
            (SequenceMatcher(None, token, candidate).ratio() for candidate in searchable_tokens),
            default=0.0,
        )
        if best >= 0.84:
            matched_tokens += 1

    if query_tokens:
        coverage = matched_tokens / len(query_tokens)
        score += coverage * 24
    else:
        coverage = 0

    if item.kind in intent_kinds and operator_hits:
        reason = f"{item.kind} relacionado à operadora pesquisada"
    elif item.kind in intent_kinds:
        reason = f"Corresponde à intenção de {item.kind.lower()}"
    elif operator_hits:
        reason = "Relacionado à operadora pesquisada"
    elif title_score >= subtitle_score and title_score > 0:
        reason = "Correspondência forte no título"
    elif subtitle_score > 0:
        reason = "Correspondência no contexto"
    else:
        reason = "Termos encontrados no conteúdo"

    return score, reason, matched_tokens


def search_catalog_smart(
    results: list[SearchResult],
    query: str,
    kind: str = "Tudo",
    *,
    limit: int = 60,
) -> SearchResponse:
    clean_query = str(query or "").strip()
    if len(normalize(clean_query)) < 2:
        return SearchResponse(clean_query, (), ())

    query_tokens = _tokens(clean_query)
    if not query_tokens:
        query_tokens = _tokens(normalize(clean_query))

    intent_kinds = _intent_kinds(clean_query)
    operator_terms = _operator_terms(results)

    pool = [
        item
        for item in results
        if kind == "Tudo" or item.kind == kind
    ]

    ranked: list[RankedSearchResult] = []
    for item in pool:
        score, reason, matched_tokens = _rank_item(
            item,
            query=clean_query,
            query_tokens=query_tokens,
            intent_kinds=intent_kinds,
            operator_terms=operator_terms,
        )

        # Primeira passagem: boa cobertura ou intenção explícita.
        required_matches = 1 if len(query_tokens) <= 2 else 2
        intent_match = item.kind in intent_kinds
        if score >= 22 and (matched_tokens >= required_matches or intent_match):
            ranked.append(RankedSearchResult(item=item, score=score, reason=reason))

    relaxed = False

    # Se a busca natural não encontrou nada, relaxa a exigência para tolerar
    # erros de digitação ou frases muito abertas.
    if not ranked:
        relaxed = True
        for item in pool:
            score, reason, matched_tokens = _rank_item(
                item,
                query=clean_query,
                query_tokens=query_tokens,
                intent_kinds=intent_kinds,
                operator_terms=operator_terms,
            )
            if score >= 13 and (matched_tokens >= 1 or item.kind in intent_kinds):
                ranked.append(
                    RankedSearchResult(
                        item=item,
                        score=score,
                        reason=reason,
                    )
                )

    ranked.sort(
        key=lambda match: (
            -match.score,
            -_KIND_PRIORITY.get(match.item.kind, 0),
            match.item.title.casefold(),
        )
    )

    interpreted: list[str] = []
    if intent_kinds:
        interpreted.extend(intent_kinds[:3])

    # Mostra também a operadora reconhecida quando seu nome aparece na consulta.
    query_token_set = set(query_tokens)
    for item in results:
        if item.kind != "Operadoras":
            continue
        name_tokens = set(_tokens(f"{item.title} {item.subtitle}"))
        if name_tokens.intersection(query_token_set):
            label = item.title
            if label and label not in interpreted:
                interpreted.insert(0, label)
            break

    return SearchResponse(
        query=clean_query,
        interpreted_as=tuple(interpreted[:4]),
        results=tuple(ranked[:limit]),
        relaxed=relaxed,
    )


def search_catalog(
    results: list[SearchResult],
    query: str,
    kind: str = "Tudo",
) -> list[SearchResult]:
    """Compatibilidade com chamadas antigas."""
    return [
        match.item
        for match in search_catalog_smart(results, query, kind).results
    ]

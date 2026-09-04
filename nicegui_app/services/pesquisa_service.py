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
class ConversationalAnswer:
    title: str
    lead: str
    bullets: tuple[str, ...]
    note: str
    confidence: str
    source_route: str
    source_label: str


@dataclass(frozen=True, slots=True)
class SearchResponse:
    query: str
    corrected_query: str
    corrections: tuple[tuple[str, str], ...]
    interpreted_as: tuple[str, ...]
    results: tuple[RankedSearchResult, ...]
    answer: ConversationalAnswer | None = None
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



def _edit_distance(a: str, b: str) -> int:
    """Damerau-Levenshtein simples para tolerar troca de letras adjacentes."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    rows = len(a) + 1
    cols = len(b) + 1
    matrix = [[0] * cols for _ in range(rows)]

    for i in range(rows):
        matrix[i][0] = i
    for j in range(cols):
        matrix[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )
            if (
                i > 1
                and j > 1
                and a[i - 1] == b[j - 2]
                and a[i - 2] == b[j - 1]
            ):
                matrix[i][j] = min(
                    matrix[i][j],
                    matrix[i - 2][j - 2] + cost,
                )

    return matrix[-1][-1]


def _max_typo_distance(token: str) -> int:
    size = len(token)
    if size <= 3:
        return 0
    if size <= 5:
        return 1
    if size <= 8:
        return 2
    return 3


def _search_vocabulary(results: list[SearchResult]) -> set[str]:
    vocabulary: set[str] = set()

    for aliases in _INTENT_ALIASES.values():
        for alias in aliases:
            vocabulary.update(_tokens(alias))

    for item in results:
        # Título e subtítulo têm maior valor semântico e normalmente contêm
        # nomes de operadoras, planos, setores e tipos de informação.
        vocabulary.update(_tokens(item.title))
        vocabulary.update(_tokens(item.subtitle))

        # Também aprende palavras relevantes do conteúdo cadastrado.
        for token in _tokens(item.description):
            if len(token) >= 4:
                vocabulary.add(token)

    return vocabulary


def _best_token_correction(
    token: str,
    vocabulary: set[str],
) -> tuple[str, float] | None:
    if len(token) <= 3 or token in vocabulary:
        return None

    max_distance = _max_typo_distance(token)
    candidates: list[tuple[float, int, str]] = []

    # Restringe por comprimento antes de calcular similaridade.
    for candidate in vocabulary:
        if abs(len(candidate) - len(token)) > max_distance:
            continue

        distance = _edit_distance(token, candidate)
        if distance > max_distance:
            continue

        ratio = SequenceMatcher(None, token, candidate).ratio()

        # Tolerância propositalmente maior que a versão anterior, mas ainda
        # exige proximidade suficiente para não "inventar" termos.
        min_ratio = 0.66 if len(token) >= 7 else 0.72
        if ratio < min_ratio:
            continue

        score = ratio - (distance * 0.035)
        candidates.append((score, distance, candidate))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    best_score, _distance, best = candidates[0]

    # Se existem duas opções quase empatadas, prefere não autocorrigir.
    if len(candidates) > 1:
        second_score = candidates[1][0]
        if best_score - second_score < 0.045:
            return None

    return best, best_score


def _correct_query(
    query: str,
    results: list[SearchResult],
) -> tuple[str, tuple[tuple[str, str], ...]]:
    vocabulary = _search_vocabulary(results)
    normalized = normalize(query)
    raw_tokens = re.findall(r"[a-z0-9]+", normalized)

    corrected_tokens: list[str] = []
    corrections: list[tuple[str, str]] = []

    for token in raw_tokens:
        if token in _STOPWORDS or token.isdigit():
            corrected_tokens.append(token)
            continue

        correction = _best_token_correction(token, vocabulary)
        if correction is None:
            corrected_tokens.append(token)
            continue

        replacement, _score = correction
        corrected_tokens.append(replacement)
        if replacement != token:
            corrections.append((token, replacement))

    corrected_query = " ".join(corrected_tokens).strip()
    return corrected_query or normalized, tuple(corrections)



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
        if best_ratio >= 0.72:
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
        if best >= 0.72:
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



def _compact(value: str, *, limit: int = 230) -> str:
    value = " ".join(str(value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip(" ,.;:-") + "…"


def _unique_lines(*values: str) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()

    for value in values:
        clean = _compact(value)
        key = normalize(clean)
        if not clean or not key or key in seen:
            continue
        seen.add(key)
        output.append(clean)

    return tuple(output)


def _answer_confidence(
    matches: tuple[RankedSearchResult, ...],
) -> str:
    if not matches:
        return "baixa"

    first = matches[0].score
    second = matches[1].score if len(matches) > 1 else 0
    gap = first - second

    if first >= 105 and gap >= 14:
        return "alta"
    if first >= 62:
        return "média"
    return "baixa"


def _build_conversational_answer(
    query: str,
    matches: tuple[RankedSearchResult, ...],
    *,
    interpreted_as: tuple[str, ...],
    corrections: tuple[tuple[str, str], ...],
) -> ConversationalAnswer | None:
    if not matches:
        return None

    first = matches[0]
    item = first.item
    confidence = _answer_confidence(matches)

    # Se os primeiros resultados estão muito próximos, não afirma que existe
    # uma única resposta correta.
    ambiguous = (
        len(matches) > 1
        and first.score - matches[1].score < 10
        and matches[1].item.kind == item.kind
    )

    kind = item.kind

    if kind == "Portais":
        title = (
            "Encontrei mais de um acesso possível."
            if ambiguous
            else "Este é o acesso mais provável."
        )
        lead = (
            f"O Portal Comercial relacionou sua pergunta ao portal "
            f"“{item.title}”"
            + (f" ({item.subtitle})." if item.subtitle else ".")
        )
        bullets = _unique_lines(
            item.description,
            "Abra o registro para consultar instruções e, quando permitido, "
            "as credenciais protegidas do acesso.",
        )

    elif kind == "Autorizações":
        title = (
            "Encontrei mais de uma regra de autorização."
            if ambiguous
            else "Esta é a orientação de autorização mais relevante."
        )
        lead = (
            f"Para sua pergunta, o cadastro priorizou “{item.title}”"
            + (f", no contexto {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Elegibilidade":
        title = (
            "Encontrei orientações possíveis de elegibilidade."
            if ambiguous
            else "Esta é a orientação de elegibilidade mais provável."
        )
        lead = (
            f"O resultado mais relacionado é “{item.title}”"
            + (f" para {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Contatos":
        title = (
            "Encontrei mais de um contato possível."
            if ambiguous
            else "Este é o contato mais provável."
        )
        lead = (
            f"O contato priorizado é “{item.title}”"
            + (f" — {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Documentos":
        title = (
            "Encontrei mais de um documento relacionado."
            if ambiguous
            else "Este é o documento mais relacionado à sua pergunta."
        )
        lead = (
            f"O Portal priorizou “{item.title}”"
            + (f" no contexto {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Coberturas":
        title = (
            "Encontrei mais de uma informação de cobertura."
            if ambiguous
            else "Esta é a informação de cobertura mais relacionada."
        )
        lead = (
            f"O cadastro priorizou “{item.title}”"
            + (f" para {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Contingências":
        title = (
            "Há mais de uma contingência relacionada."
            if ambiguous
            else "Há uma contingência relacionada à sua pergunta."
        )
        lead = (
            f"A ocorrência mais relevante é “{item.title}”"
            + (f" — {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Consultores":
        title = (
            "Encontrei mais de um consultor relacionado."
            if ambiguous
            else "Este é o consultor mais relacionado."
        )
        lead = (
            f"O Portal priorizou “{item.title}”"
            + (f" — {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Planos":
        title = (
            "Encontrei mais de um plano relacionado."
            if ambiguous
            else "Este é o plano mais relacionado."
        )
        lead = (
            f"O resultado priorizado é “{item.title}”"
            + (f" da operadora {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    elif kind == "Operadoras":
        title = (
            "Encontrei operadoras relacionadas."
            if ambiguous
            else "Esta é a operadora mais relacionada."
        )
        lead = f"O resultado priorizado é “{item.title}”."
        bullets = _unique_lines(item.subtitle, item.description)

    elif kind == "Comunicados":
        title = (
            "Encontrei comunicados relacionados."
            if ambiguous
            else "Este comunicado parece responder melhor à sua busca."
        )
        lead = (
            f"O comunicado priorizado é “{item.title}”"
            + (f" — {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    else:
        title = "Encontrei uma orientação relacionada."
        lead = (
            f"O resultado que melhor corresponde à sua pergunta é "
            f"“{item.title}”"
            + (f" — {item.subtitle}." if item.subtitle else ".")
        )
        bullets = _unique_lines(item.description)

    note_parts: list[str] = [
        "Resposta montada somente com informações cadastradas no Portal Comercial."
    ]
    if corrections:
        correction_text = ", ".join(
            f"“{source}” → “{target}”"
            for source, target in corrections[:3]
        )
        note_parts.append(f"Corrigi automaticamente: {correction_text}.")
    if confidence == "baixa":
        note_parts.append(
            "A correspondência ainda é ampla; confira o registro antes de orientar o atendimento."
        )
    elif ambiguous:
        note_parts.append(
            "Existem resultados próximos; confira também as alternativas abaixo."
        )

    return ConversationalAnswer(
        title=title,
        lead=lead,
        bullets=bullets[:3],
        note=" ".join(note_parts),
        confidence=confidence,
        source_route=item.route,
        source_label=f"Abrir {item.eyebrow.lower()}",
    )



def search_catalog_smart(
    results: list[SearchResult],
    query: str,
    kind: str = "Tudo",
    *,
    limit: int = 60,
) -> SearchResponse:
    clean_query = str(query or "").strip()
    if len(normalize(clean_query)) < 2:
        return SearchResponse(
            query=clean_query,
            corrected_query=clean_query,
            corrections=(),
            interpreted_as=(),
            results=(),
            answer=None,
        )

    corrected_query, corrections = _correct_query(clean_query, results)
    query_for_search = corrected_query or clean_query

    query_tokens = _tokens(query_for_search)
    if not query_tokens:
        query_tokens = _tokens(normalize(query_for_search))

    intent_kinds = _intent_kinds(query_for_search)
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
            query=query_for_search,
            query_tokens=query_tokens,
            intent_kinds=intent_kinds,
            operator_terms=operator_terms,
        )

        # Com a correção ortográfica, podemos aceitar uma cobertura um pouco
        # mais ampla sem perder segurança.
        required_matches = 1 if len(query_tokens) <= 3 else 2
        intent_match = item.kind in intent_kinds
        if score >= 18 and (matched_tokens >= required_matches or intent_match):
            ranked.append(
                RankedSearchResult(
                    item=item,
                    score=score,
                    reason=reason,
                )
            )

    relaxed = bool(corrections)

    # Segunda passagem deliberadamente mais tolerante para perguntas com
    # muitos erros ou linguagem coloquial.
    if not ranked:
        relaxed = True
        for item in pool:
            score, reason, matched_tokens = _rank_item(
                item,
                query=query_for_search,
                query_tokens=query_tokens,
                intent_kinds=intent_kinds,
                operator_terms=operator_terms,
            )
            if score >= 9.5 and (
                matched_tokens >= 1
                or item.kind in intent_kinds
            ):
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

    final_results = tuple(ranked[:limit])
    interpreted_tuple = tuple(interpreted[:4])

    return SearchResponse(
        query=clean_query,
        corrected_query=query_for_search,
        corrections=corrections,
        interpreted_as=interpreted_tuple,
        results=final_results,
        answer=_build_conversational_answer(
            clean_query,
            final_results,
            interpreted_as=interpreted_tuple,
            corrections=corrections,
        ),
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

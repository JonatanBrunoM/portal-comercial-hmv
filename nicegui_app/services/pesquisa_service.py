from __future__ import annotations

from dataclasses import dataclass
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


def search_catalog(results: list[SearchResult], query: str, kind: str = "Tudo") -> list[SearchResult]:
    term = normalize(query)
    if len(term) < 2:
        return []

    words = [word for word in term.split() if word]
    matches = [
        item for item in results
        if (kind == "Tudo" or item.kind == kind)
        and all(word in item.search_text for word in words)
    ]

    def score(item: SearchResult) -> tuple[int, str]:
        title = normalize(item.title)
        subtitle = normalize(item.subtitle)
        points = 0
        if term == title:
            points += 100
        elif title.startswith(term):
            points += 70
        elif term in title:
            points += 50
        if term in subtitle:
            points += 20
        return (-points, item.title.lower())

    return sorted(matches, key=score)

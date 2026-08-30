from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.search_service import (
    SearchResult,
    search_global,
)
from core.data_service import (
    get_operadoras,
    read_dataset,
)
from utils.formatting import (
    normalize_text,
    shorten_text,
)


KNOWLEDGE_DATASET = "conhecimento"
MAX_RELATED_RESULTS = 5


@dataclass(frozen=True)
class KnowledgeAnswer:
    """Representa uma resposta encontrada na base oficial."""

    knowledge_id: str
    question: str
    answer: str
    category: str
    operator_name: str
    source: str
    source_record_id: str
    keywords: str
    confidence: str
    review_status: str
    last_review: str
    relevance: int


def _safe_value(
    row: pd.Series,
    column: str,
) -> str:
    """Retorna um valor textual sem gerar erro."""

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
    """Retorna o primeiro campo preenchido disponível."""

    for column in columns:
        value = _safe_value(
            row,
            column,
        )

        if value:
            return value

    return ""


def _format_date(
    value: object,
) -> str:
    """Formata uma data para exibição."""

    if value is None or pd.isna(value):
        return ""

    text = str(value).strip()

    if not text or text.casefold() == "nan":
        return ""

    parsed = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=True,
    )

    if pd.isna(parsed):
        return text

    return parsed.strftime("%d/%m/%Y")


def _is_visible_status(
    value: object,
) -> bool:
    """Define quais respostas podem ser mostradas."""

    status = normalize_text(value)

    if not status:
        return True

    hidden_statuses = {
        "inativo",
        "inativa",
        "excluido",
        "excluida",
        "reprovado",
        "reprovada",
        "oculto",
        "oculta",
    }

    return status not in hidden_statuses


def _confidence_score(
    value: object,
) -> int:
    """Converte o nível de confiança em uma pontuação."""

    normalized = normalize_text(value)

    scores = {
        "alta": 30,
        "revisado": 30,
        "validado": 30,
        "media": 20,
        "em revisao": 15,
        "baixa": 5,
        "pendente": 0,
    }

    return scores.get(
        normalized,
        10,
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _build_knowledge_dataset() -> pd.DataFrame:
    """
    Carrega a base de conhecimento e vincula
    o nome das operadoras.
    """

    knowledge = read_dataset(
        dataset=KNOWLEDGE_DATASET,
        ttl=1800,
    )

    operadoras = get_operadoras()

    if knowledge is None or knowledge.empty:
        return pd.DataFrame()

    result = knowledge.copy()

    if (
        not operadoras.empty
        and "ID Operadora" in operadoras.columns
        and "ID Operadora" in result.columns
    ):
        operator_name_column = next(
            (
                column
                for column in [
                    "Nome curto",
                    "Operadora",
                ]
                if column in operadoras.columns
            ),
            None,
        )

        if operator_name_column:
            operator_lookup = (
                operadoras[
                    [
                        "ID Operadora",
                        operator_name_column,
                    ]
                ]
                .drop_duplicates(
                    subset=["ID Operadora"]
                )
                .rename(
                    columns={
                        operator_name_column: (
                            "Nome Operadora"
                        )
                    }
                )
            )

            result = result.merge(
                operator_lookup,
                how="left",
                on="ID Operadora",
            )

    if "Nome Operadora" not in result.columns:
        result["Nome Operadora"] = ""

    required_columns = [
        "ID Conhecimento",
        "Pergunta",
        "Pergunta canônica",
        "Intenção",
        "Categoria",
        "Resposta",
        "Resposta oficial",
        "Fonte",
        "ID Registro Fonte",
        "Palavras-chave",
        "Sinônimos",
        "Confiança",
        "Nível de confiança",
        "Status",
        "Status revisão",
        "Última revisão",
        "Data revisão",
        "Nome Operadora",
    ]

    for column in required_columns:
        if column not in result.columns:
            result[column] = ""

        result[column] = (
            result[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    visible_status = result.apply(
        lambda row: _is_visible_status(
            _first_available(
                row,
                [
                    "Status revisão",
                    "Status",
                ],
            )
        ),
        axis=1,
    )

    result = result[
        visible_status
    ].copy()

    result["_question"] = result.apply(
        lambda row: _first_available(
            row,
            [
                "Pergunta canônica",
                "Pergunta",
            ],
        ),
        axis=1,
    )

    result["_answer"] = result.apply(
        lambda row: _first_available(
            row,
            [
                "Resposta oficial",
                "Resposta",
            ],
        ),
        axis=1,
    )

    result["_confidence"] = result.apply(
        lambda row: _first_available(
            row,
            [
                "Nível de confiança",
                "Confiança",
            ],
        ),
        axis=1,
    )

    result["_review_status"] = result.apply(
        lambda row: _first_available(
            row,
            [
                "Status revisão",
                "Status",
            ],
        ),
        axis=1,
    )

    result["_last_review"] = result.apply(
        lambda row: _first_available(
            row,
            [
                "Última revisão",
                "Data revisão",
            ],
        ),
        axis=1,
    )

    result["_search_text"] = result.apply(
        lambda row: normalize_text(
            " ".join(
                [
                    row["_question"],
                    row["_answer"],
                    _safe_value(row, "Intenção"),
                    _safe_value(row, "Categoria"),
                    _safe_value(row, "Palavras-chave"),
                    _safe_value(row, "Sinônimos"),
                    _safe_value(row, "Nome Operadora"),
                ]
            )
        ),
        axis=1,
    )

    return result.reset_index(
        drop=True
    )


def _calculate_relevance(
    query: str,
    row: pd.Series,
) -> int:
    """Calcula a relevância da resposta."""

    normalized_query = normalize_text(
        query
    )

    query_words = {
        word
        for word in normalized_query.split()
        if len(word) >= 2
    }

    question = normalize_text(
        row["_question"]
    )

    answer = normalize_text(
        row["_answer"]
    )

    keywords = normalize_text(
        _safe_value(
            row,
            "Palavras-chave",
        )
    )

    synonyms = normalize_text(
        _safe_value(
            row,
            "Sinônimos",
        )
    )

    operator_name = normalize_text(
        _safe_value(
            row,
            "Nome Operadora",
        )
    )

    category = normalize_text(
        _safe_value(
            row,
            "Categoria",
        )
    )

    score = 0

    if normalized_query == question:
        score += 150

    elif normalized_query in question:
        score += 100

    if normalized_query in keywords:
        score += 70

    if normalized_query in synonyms:
        score += 60

    if normalized_query in operator_name:
        score += 35

    if normalized_query in category:
        score += 25

    if normalized_query in answer:
        score += 20

    for word in query_words:
        if word in question:
            score += 20

        if word in keywords:
            score += 15

        if word in synonyms:
            score += 12

        if word in operator_name:
            score += 10

        if word in category:
            score += 8

        if word in answer:
            score += 4

    score += _confidence_score(
        row["_confidence"]
    )

    return score


def _search_knowledge(
    query: str,
) -> list[KnowledgeAnswer]:
    """Pesquisa respostas oficiais na base de conhecimento."""

    dataframe = _build_knowledge_dataset()

    if dataframe.empty:
        return []

    answers: list[KnowledgeAnswer] = []

    for index, row in dataframe.iterrows():
        relevance = _calculate_relevance(
            query=query,
            row=row,
        )

        if relevance <= 10:
            continue

        answer_text = row["_answer"]

        if not answer_text:
            continue

        answers.append(
            KnowledgeAnswer(
                knowledge_id=(
                    _safe_value(
                        row,
                        "ID Conhecimento",
                    )
                    or str(index)
                ),
                question=(
                    row["_question"]
                    or "Pergunta não informada"
                ),
                answer=answer_text,
                category=(
                    _safe_value(
                        row,
                        "Categoria",
                    )
                    or "Geral"
                ),
                operator_name=(
                    _safe_value(
                        row,
                        "Nome Operadora",
                    )
                    or "Informação geral"
                ),
                source=(
                    _safe_value(
                        row,
                        "Fonte",
                    )
                    or "Base comercial"
                ),
                source_record_id=_safe_value(
                    row,
                    "ID Registro Fonte",
                ),
                keywords=_safe_value(
                    row,
                    "Palavras-chave",
                ),
                confidence=(
                    row["_confidence"]
                    or "Não informada"
                ),
                review_status=(
                    row["_review_status"]
                    or "Não informado"
                ),
                last_review=_format_date(
                    row["_last_review"]
                ),
                relevance=relevance,
            )
        )

    answers.sort(
        key=lambda answer: (
            -answer.relevance,
            answer.question,
        )
    )

    return answers


def _confidence_icon(
    confidence: str,
) -> str:
    """Retorna o ícone do nível de confiança."""

    normalized = normalize_text(
        confidence
    )

    if normalized in {
        "alta",
        "revisado",
        "validado",
    }:
        return "🟢"

    if normalized in {
        "media",
        "em revisao",
    }:
        return "🟡"

    return "🔴"


def _render_official_answer(
    answer: KnowledgeAnswer,
) -> None:
    """Renderiza a melhor resposta oficial."""

    confidence_icon = _confidence_icon(
        answer.confidence
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            "### Resposta encontrada"
        )

        st.caption(
            f"{answer.category} • "
            f"{answer.operator_name}"
        )

        st.write(
            answer.answer
        )

        detail_1, detail_2 = st.columns(
            2
        )

        detail_1.markdown(
            f"**Confiança:** "
            f"{confidence_icon} "
            f"{answer.confidence}"
        )

        detail_2.markdown(
            f"**Revisão:** "
            f"{answer.review_status}"
        )

        source_text = answer.source

        if answer.source_record_id:
            source_text += (
                f" • Registro "
                f"{answer.source_record_id}"
            )

        st.markdown(
            f"**Fonte:** {source_text}"
        )

        if answer.last_review:
            st.caption(
                "Última revisão: "
                f"{answer.last_review}"
            )


def _render_alternative_answers(
    answers: list[KnowledgeAnswer],
) -> None:
    """Renderiza outras respostas relacionadas."""

    if len(answers) <= 1:
        return

    with st.expander(
        "Outras respostas relacionadas",
        expanded=False,
    ):
        for answer in answers[1:4]:
            st.markdown(
                f"**{answer.question}**"
            )

            st.write(
                shorten_text(
                    answer.answer,
                    limit=280,
                )
            )

            st.caption(
                f"{answer.category} • "
                f"{answer.operator_name} • "
                f"Fonte: {answer.source}"
            )

            st.divider()


def _render_related_result(
    result: SearchResult,
    position: int,
) -> None:
    """Renderiza um resultado relacionado da busca global."""

    with st.container(
        border=True,
    ):
        st.markdown(
            f"**{result.category} — "
            f"{result.title}**"
        )

        if result.subtitle:
            st.caption(
                result.subtitle
            )

        if result.description:
            st.write(
                result.description
            )

        st.caption(
            f"Fonte: {result.source_dataset}"
        )


def _render_related_results(
    query: str,
) -> None:
    """Mostra registros relacionados de outros módulos."""

    try:
        results = search_global(
            query=query,
            limit=MAX_RELATED_RESULTS,
        )

    except RuntimeError:
        results = []

    if not results:
        return

    st.markdown(
        "### Informações relacionadas"
    )

    for position, result in enumerate(
        results
    ):
        _render_related_result(
            result=result,
            position=position,
        )


def _render_suggestions() -> None:
    """Renderiza perguntas de exemplo."""

    st.markdown(
        "### Exemplos de perguntas"
    )

    suggestions = [
        "Como consultar a elegibilidade da Unimed?",
        "Quais documentos o Bradesco exige?",
        "Como solicitar autorização da CASSI?",
        "Qual é o portal da Unimed?",
        "Qual contato devo usar para autorizações?",
        "Existe alguma contingência ativa?",
    ]

    columns = st.columns(2)

    for index, suggestion in enumerate(
        suggestions
    ):
        with columns[index % 2]:
            if st.button(
                suggestion,
                key=(
                    "assistant_suggestion_"
                    f"{index}"
                ),
                use_container_width=True,
            ):
                st.session_state[
                    "assistant_pending_question"
                ] = suggestion

                st.rerun()


def render_assistente() -> None:
    """Renderiza o Assistente Comercial."""

    render_hero(
        eyebrow="Base oficial de conhecimento",
        title="Assistente Comercial",
        description=(
            "Faça perguntas sobre operadoras, planos, "
            "documentos, portais, autorizações, contatos "
            "e orientações comerciais."
        ),
    )

    st.info(
        "Esta versão responde exclusivamente com informações "
        "cadastradas na base comercial. Ela ainda não utiliza "
        "uma inteligência artificial externa."
    )

    pending_question = st.session_state.pop(
        "assistant_pending_question",
        None,
    )

    if pending_question is not None:
        st.session_state[
            "assistant_question_input"
        ] = pending_question

    question = st.text_input(
        label="Pergunta",
        placeholder=(
            "Exemplo: como solicitar autorização "
            "da CASSI?"
        ),
        key="assistant_question_input",
    )

    ask_button = st.button(
        "Pesquisar resposta",
        type="primary",
        use_container_width=True,
        disabled=len(
            question.strip()
        ) < 3,
    )

    if (
        not ask_button
        and len(question.strip()) < 3
    ):
        _render_suggestions()
        return

    if len(question.strip()) < 3:
        st.warning(
            "Digite uma pergunta com pelo menos "
            "três caracteres."
        )
        return

    with st.spinner(
        "Consultando a base comercial..."
    ):
        official_answers = _search_knowledge(
            question
        )

    st.divider()

    if official_answers:
        _render_official_answer(
            official_answers[0]
        )

        _render_alternative_answers(
            official_answers
        )

    else:
        st.warning(
            "Não encontramos uma resposta oficial pronta "
            "para essa pergunta."
        )

        st.caption(
            "Abaixo estão registros relacionados que podem "
            "ajudar na consulta."
        )

    _render_related_results(
        question
    )

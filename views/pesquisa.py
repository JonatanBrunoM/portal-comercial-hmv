import streamlit as st

from components.hero import render_hero
from components.search_results import render_search_results
from core.search_service import analyze_search_query, search_global


EXAMPLE_QUERIES = [
    "Bradesco autorização",
    "CASSI telefone",
    "Unimed portal",
    "Como autorizar CASSI",
]


def _apply_example_query(example: str) -> None:
    st.session_state["full_search_query"] = example
    st.session_state["last_search_query"] = example


def _render_query_context(analysis: dict[str, object]) -> None:
    operator_names = analysis.get("operator_names") or []
    intents = analysis.get("category_intents") or []

    parts: list[str] = []
    if operator_names:
        parts.append("Operadora: " + ", ".join(operator_names))
    if intents:
        parts.append("Assunto: " + ", ".join(intents))

    if parts:
        st.caption(" · ".join(parts))


def render_pesquisa() -> None:
    render_hero(
        eyebrow="Consulta central",
        title="Pesquisa Global",
        description=(
            "Digite a operadora e o que você precisa. "
            "A pesquisa consulta toda a base comercial e leva você ao ponto certo."
        ),
    )

    if "full_search_query" not in st.session_state:
        st.session_state["full_search_query"] = st.session_state.get(
            "last_search_query",
            "",
        )

    query = st.text_input(
        label="O que você precisa encontrar?",
        placeholder="Ex.: Bradesco autorização, CASSI telefone, Unimed portal...",
        key="full_search_query",
    )
    st.session_state["last_search_query"] = query

    if len(query.strip()) < 2:
        st.caption("Exemplos de pesquisa")
        columns = st.columns(2)

        for index, example in enumerate(EXAMPLE_QUERIES):
            with columns[index % 2]:
                st.button(
                    f"🔎 {example}",
                    key=f"search_example_{index}",
                    use_container_width=True,
                    on_click=_apply_example_query,
                    args=(example,),
                )

        st.info(
            "Você pode pesquisar de forma natural, por exemplo: "
            "“como autorizar CASSI”, “telefone Bradesco”, "
            "“senha portal Unimed” ou “documentos internação Bradesco”."
        )
        return

    analysis = analyze_search_query(query)
    _render_query_context(analysis)

    with st.spinner("Consultando toda a base comercial..."):
        results = search_global(query=query, limit=50)

    render_search_results(
        results=results,
        key_prefix="full_search",
        query=query,
        query_analysis=analysis,
    )

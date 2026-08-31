import streamlit as st

from components.hero import render_hero
from components.search_results import render_search_results
from core.search_service import search_global


EXAMPLE_QUERIES = [
    "Bradesco autorização",
    "CASSI telefone",
    "Unimed portal",
    "Bradesco comunicado",
]


def _apply_example_query(example: str) -> None:
    """Callback executado antes do rerun do Streamlit."""
    st.session_state["full_search_query"] = example
    st.session_state["last_search_query"] = example


def render_pesquisa() -> None:
    render_hero(
        eyebrow="Consulta central",
        title="Pesquisa Global",
        description=(
            "Pesquise do jeito que você pensaria no dia a dia. "
            "O Portal procura a informação em toda a base comercial."
        ),
    )

    # O widget passa a ser a única fonte de verdade da pesquisa.
    # A inicialização acontece antes da criação do text_input para evitar
    # StreamlitAPIException ao tentar alterar seu estado posteriormente.
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
            "Digite pelo menos dois caracteres. Você pode combinar "
            "a operadora com a necessidade, como “Bradesco senha”, "
            "“CASSI elegibilidade” ou “Unimed contato”."
        )
        return

    with st.spinner("Consultando toda a base comercial..."):
        results = search_global(query=query, limit=50)

    render_search_results(
        results=results,
        key_prefix="full_search",
    )

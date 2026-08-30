from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import (
    get_operadoras,
    read_dataset,
)
from utils.formatting import normalize_text


FORUM_POSTS_DATASET = "forum_posts"
FORUM_COMMENTS_DATASET = "forum_comentarios"

ITEMS_PER_PAGE = 8


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

    if isinstance(value, (datetime, date)):
        return value.strftime(
            "%d/%m/%Y %H:%M"
        )

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

    if (
        parsed.hour == 0
        and parsed.minute == 0
        and parsed.second == 0
    ):
        return parsed.strftime(
            "%d/%m/%Y"
        )

    return parsed.strftime(
        "%d/%m/%Y %H:%M"
    )


def _is_visible_status(
    value: object,
) -> bool:
    """Define quais registros podem aparecer no portal."""

    status = normalize_text(
        value
    )

    if not status:
        return True

    hidden_statuses = {
        "inativo",
        "excluido",
        "excluida",
        "removido",
        "removida",
        "oculto",
        "oculta",
        "reprovado",
        "reprovada",
    }

    return status not in hidden_statuses


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def _build_forum_dataset() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Carrega tópicos e comentários do fórum.
    """

    posts = read_dataset(
        dataset=FORUM_POSTS_DATASET,
        ttl=600,
    )

    comments = read_dataset(
        dataset=FORUM_COMMENTS_DATASET,
        ttl=600,
    )

    operadoras = get_operadoras()

    if posts is None:
        posts = pd.DataFrame()

    if comments is None:
        comments = pd.DataFrame()

    posts = posts.copy()
    comments = comments.copy()

    if posts.empty:
        return posts, comments

    # Adiciona nome da operadora aos tópicos.
    if (
        not operadoras.empty
        and "ID Operadora" in operadoras.columns
        and "ID Operadora" in posts.columns
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

            posts = posts.merge(
                operator_lookup,
                how="left",
                on="ID Operadora",
            )

    if "Nome Operadora" not in posts.columns:
        posts["Nome Operadora"] = ""

    required_post_columns = [
        "ID Post",
        "ID Tópico",
        "Título",
        "Conteúdo",
        "Categoria",
        "Autor",
        "Data",
        "Data publicação",
        "Status",
        "Nome Operadora",
        "Palavras-chave",
    ]

    for column in required_post_columns:
        if column not in posts.columns:
            posts[column] = ""

        posts[column] = (
            posts[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    visible_posts = posts["Status"].map(
        _is_visible_status
    )

    posts = posts[
        visible_posts
    ].copy()

    required_comment_columns = [
        "ID Comentário",
        "ID Post",
        "ID Tópico",
        "Comentário",
        "Conteúdo",
        "Autor",
        "Data",
        "Data publicação",
        "Status",
    ]

    for column in required_comment_columns:
        if column not in comments.columns:
            comments[column] = ""

        comments[column] = (
            comments[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    if not comments.empty:
        visible_comments = comments[
            "Status"
        ].map(
            _is_visible_status
        )

        comments = comments[
            visible_comments
        ].copy()

    post_date_column = next(
        (
            column
            for column in [
                "Data publicação",
                "Data",
            ]
            if column in posts.columns
        ),
        None,
    )

    if post_date_column:
        posts["_date_sort"] = pd.to_datetime(
            posts[post_date_column],
            errors="coerce",
            dayfirst=True,
        )

        posts = posts.sort_values(
            by="_date_sort",
            ascending=False,
            na_position="last",
        )

    return (
        posts.reset_index(drop=True),
        comments.reset_index(drop=True),
    )


def _post_id(
    row: pd.Series,
) -> str:
    """Retorna o identificador do tópico."""

    return _first_available(
        row,
        [
            "ID Post",
            "ID Tópico",
        ],
    )


def _comment_post_id(
    row: pd.Series,
) -> str:
    """Retorna o tópico associado ao comentário."""

    return _first_available(
        row,
        [
            "ID Post",
            "ID Tópico",
        ],
    )


def _count_comments(
    comments: pd.DataFrame,
    post_id: str,
) -> int:
    """Conta os comentários de um tópico."""

    if comments.empty or not post_id:
        return 0

    identifiers = comments.apply(
        _comment_post_id,
        axis=1,
    )

    return int(
        identifiers.eq(post_id).sum()
    )


def _filter_posts(
    posts: pd.DataFrame,
    query: str,
    operator_name: str,
    category: str,
) -> pd.DataFrame:
    """Aplica os filtros do fórum."""

    filtered = posts.copy()

    if operator_name != "Todas":
        filtered = filtered[
            filtered["Nome Operadora"].eq(
                operator_name
            )
        ]

    if category != "Todas":
        filtered = filtered[
            filtered["Categoria"].eq(
                category
            )
        ]

    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        searchable_columns = [
            column
            for column in [
                "Título",
                "Conteúdo",
                "Categoria",
                "Autor",
                "Nome Operadora",
                "Palavras-chave",
            ]
            if column in filtered.columns
        ]

        searchable_text = (
            filtered[searchable_columns]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .map(normalize_text)
        )

        filtered = filtered[
            searchable_text.str.contains(
                normalized_query,
                regex=False,
                na=False,
            )
        ]

    return filtered.reset_index(
        drop=True
    )


def _render_comments(
    comments: pd.DataFrame,
    post_id: str,
) -> None:
    """Renderiza os comentários de um tópico."""

    if comments.empty or not post_id:
        st.caption(
            "Este tópico ainda não possui comentários."
        )
        return

    identifiers = comments.apply(
        _comment_post_id,
        axis=1,
    )

    filtered = comments[
        identifiers.eq(post_id)
    ].copy()

    if filtered.empty:
        st.caption(
            "Este tópico ainda não possui comentários."
        )
        return

    date_column = next(
        (
            column
            for column in [
                "Data publicação",
                "Data",
            ]
            if column in filtered.columns
        ),
        None,
    )

    if date_column:
        filtered["_date_sort"] = pd.to_datetime(
            filtered[date_column],
            errors="coerce",
            dayfirst=True,
        )

        filtered = filtered.sort_values(
            by="_date_sort",
            ascending=True,
            na_position="last",
        )

    for _, comment in filtered.iterrows():
        author = (
            _safe_value(
                comment,
                "Autor",
            )
            or "Colaborador"
        )

        content = _first_available(
            comment,
            [
                "Comentário",
                "Conteúdo",
            ],
        )

        comment_date = _format_date(
            _first_available(
                comment,
                [
                    "Data publicação",
                    "Data",
                ],
            )
        )

        with st.container(
            border=True,
        ):
            st.markdown(
                f"**{author}**"
            )

            if comment_date:
                st.caption(
                    comment_date
                )

            if content:
                st.write(
                    content
                )


def _render_post(
    post: pd.Series,
    comments: pd.DataFrame,
    position: int,
) -> None:
    """Renderiza um tópico do fórum."""

    post_id = (
        _post_id(post)
        or str(position)
    )

    title = (
        _safe_value(
            post,
            "Título",
        )
        or "Tópico sem título"
    )

    content = _safe_value(
        post,
        "Conteúdo",
    )

    category = (
        _safe_value(
            post,
            "Categoria",
        )
        or "Geral"
    )

    author = (
        _safe_value(
            post,
            "Autor",
        )
        or "Colaborador"
    )

    operator_name = (
        _safe_value(
            post,
            "Nome Operadora",
        )
        or "Assunto geral"
    )

    publication_date = _format_date(
        _first_available(
            post,
            [
                "Data publicação",
                "Data",
            ],
        )
    )

    comments_count = _count_comments(
        comments,
        post_id,
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### 💬 {title}"
        )

        st.caption(
            f"{category} • {operator_name}"
        )

        if content:
            st.write(
                content
            )

        detail_1, detail_2, detail_3 = (
            st.columns(3)
        )

        detail_1.markdown(
            f"**Autor:** {author}"
        )

        detail_2.markdown(
            "**Publicado:** "
            f"{publication_date or 'Não informado'}"
        )

        detail_3.markdown(
            f"**Comentários:** {comments_count}"
        )

        with st.expander(
            (
                "Ver comentários "
                f"({comments_count})"
            ),
            expanded=False,
        ):
            _render_comments(
                comments=comments,
                post_id=post_id,
            )


def _render_pagination(
    total_items: int,
) -> tuple[int, int]:
    """Renderiza a paginação dos tópicos."""

    total_pages = max(
        1,
        (
            total_items
            + ITEMS_PER_PAGE
            - 1
        )
        // ITEMS_PER_PAGE,
    )

    current_page = int(
        st.session_state.get(
            "forum_page",
            1,
        )
    )

    if current_page > total_pages:
        current_page = 1
        st.session_state.forum_page = 1

    previous_col, page_col, next_col = (
        st.columns(
            [1, 2, 1]
        )
    )

    with previous_col:
        if st.button(
            "← Anterior",
            disabled=current_page <= 1,
            use_container_width=True,
            key="forum_previous_page",
        ):
            st.session_state.forum_page = (
                current_page - 1
            )
            st.rerun()

    with page_col:
        st.markdown(
            (
                "<div style='text-align:center;"
                "padding:0.65rem;'>"
                f"Página {current_page} "
                f"de {total_pages}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    with next_col:
        if st.button(
            "Próxima →",
            disabled=current_page >= total_pages,
            use_container_width=True,
            key="forum_next_page",
        ):
            st.session_state.forum_page = (
                current_page + 1
            )
            st.rerun()

    start = (
        current_page - 1
    ) * ITEMS_PER_PAGE

    end = start + ITEMS_PER_PAGE

    return start, end


def render_forum() -> None:
    """Renderiza o fórum em modo de leitura."""

    render_hero(
        eyebrow="Conhecimento colaborativo",
        title="Fórum Comercial",
        description=(
            "Consulte informações, experiências e "
            "orientações compartilhadas pelos "
            "colaboradores."
        ),
    )

    st.info(
        "Nesta primeira versão, o fórum está disponível "
        "somente para consulta. A publicação de tópicos e "
        "comentários será habilitada com identificação."
    )

    try:
        with st.spinner(
            "Carregando o fórum..."
        ):
            posts, comments = (
                _build_forum_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar o fórum "
            "neste momento."
        )
        return

    if posts.empty:
        st.info(
            "Nenhum tópico foi encontrado."
        )
        return

    query = st.text_input(
        label="Pesquisar no fórum",
        placeholder=(
            "Pesquise por assunto, operadora, "
            "categoria ou palavra-chave..."
        ),
        key="forum_search_query",
    )

    operator_options = sorted(
        value
        for value in posts[
            "Nome Operadora"
        ].unique()
        if value
    )

    category_options = sorted(
        value
        for value in posts[
            "Categoria"
        ].unique()
        if value
    )

    filter_1, filter_2 = st.columns(
        2
    )

    with filter_1:
        selected_operator = st.selectbox(
            label="Operadora",
            options=[
                "Todas",
                *operator_options,
            ],
            key="forum_operator_filter",
        )

    with filter_2:
        selected_category = st.selectbox(
            label="Categoria",
            options=[
                "Todas",
                *category_options,
            ],
            key="forum_category_filter",
        )

    filtered = _filter_posts(
        posts=posts,
        query=query,
        operator_name=selected_operator,
        category=selected_category,
    )

    filter_signature = (
        query,
        selected_operator,
        selected_category,
    )

    previous_signature = (
        st.session_state.get(
            "forum_filter_signature"
        )
    )

    if (
        previous_signature
        != filter_signature
    ):
        st.session_state[
            "forum_filter_signature"
        ] = filter_signature

        st.session_state.forum_page = 1

    total_comments = sum(
        _count_comments(
            comments,
            _post_id(row),
        )
        for _, row in filtered.iterrows()
    )

    metric_1, metric_2 = st.columns(
        2
    )

    metric_1.metric(
        "Tópicos encontrados",
        len(filtered),
    )

    metric_2.metric(
        "Comentários",
        total_comments,
    )

    if filtered.empty:
        st.info(
            "Nenhum tópico corresponde aos "
            "filtros selecionados."
        )
        return

    start, end = _render_pagination(
        len(filtered)
    )

    current_page = filtered.iloc[
        start:end
    ]

    for index, post in (
        current_page.iterrows()
    ):
        _render_post(
            post=post,
            comments=comments,
            position=index,
        )

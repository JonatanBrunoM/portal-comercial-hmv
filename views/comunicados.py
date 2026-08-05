from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.sheets_service import (
    get_comunicados,
    get_operadoras,
)
from utils.formatting import normalize_text


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


def _parse_date(
    value: object,
) -> pd.Timestamp | None:
    """Converte um valor para data."""

    if value is None or pd.isna(value):
        return None

    if isinstance(value, (datetime, date)):
        return pd.Timestamp(value).normalize()

    text = str(value).strip()

    if not text or text.casefold() == "nan":
        return None

    parsed = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=True,
    )

    if pd.isna(parsed):
        return None

    return pd.Timestamp(parsed).normalize()


def _format_date(
    value: object,
) -> str:
    """Formata uma data para exibição."""

    parsed = _parse_date(value)

    if parsed is None:
        return ""

    return parsed.strftime("%d/%m/%Y")


def _priority_order(
    value: object,
) -> int:
    """Define a ordem de exibição das prioridades."""

    priority = normalize_text(value)

    order = {
        "alta": 0,
        "media": 1,
        "baixa": 2,
    }

    return order.get(priority, 3)


def _is_published_status(
    value: object,
) -> bool:
    """Verifica se o comunicado está publicado."""

    status = normalize_text(value)

    return status in {
        "ativo",
        "ativa",
        "publicado",
        "publicada",
        "publicavel",
        "revisado",
    }


def _is_currently_active(
    row: pd.Series,
) -> bool:
    """
    Verifica status e vigência do comunicado.
    """

    status = _safe_value(
        row,
        "Status",
    )

    if not status:
        status = _safe_value(
            row,
            "Status publicação",
        )

    if not _is_published_status(status):
        return False

    today = pd.Timestamp.today().normalize()

    start_date = _parse_date(
        _safe_value(
            row,
            "Data início",
        )
    )

    end_date = _parse_date(
        _safe_value(
            row,
            "Data fim",
        )
    )

    if start_date is not None and today < start_date:
        return False

    if end_date is not None and today > end_date:
        return False

    return True


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def _build_comunicados_dataset() -> pd.DataFrame:
    """
    Une os comunicados ao nome das operadoras.
    """

    comunicados = get_comunicados()
    operadoras = get_operadoras()

    if comunicados is None or comunicados.empty:
        return pd.DataFrame()

    result = comunicados.copy()

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
        "Nome Operadora",
        "Título",
        "Resumo",
        "Conteúdo",
        "Categoria",
        "Prioridade",
        "Público-alvo",
        "Data início",
        "Data fim",
        "Status",
        "Status publicação",
        "Link",
        "Responsável",
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

    result["_active"] = result.apply(
        _is_currently_active,
        axis=1,
    )

    result["_priority_order"] = (
        result["Prioridade"]
        .map(_priority_order)
    )

    result["_start_date_sort"] = pd.to_datetime(
        result["Data início"],
        errors="coerce",
        dayfirst=True,
    )

    result = result.sort_values(
        by=[
            "_active",
            "_priority_order",
            "_start_date_sort",
            "Título",
        ],
        ascending=[
            False,
            True,
            False,
            True,
        ],
        na_position="last",
    )

    return result.reset_index(drop=True)


def _filter_comunicados(
    dataframe: pd.DataFrame,
    query: str,
    operator_name: str,
    category: str,
    priority: str,
    audience: str,
    only_active: bool,
) -> pd.DataFrame:
    """Aplica os filtros da página."""

    filtered = dataframe.copy()

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

    if priority != "Todas":
        filtered = filtered[
            filtered["Prioridade"].eq(
                priority
            )
        ]

    if audience != "Todos":
        filtered = filtered[
            filtered["Público-alvo"].eq(
                audience
            )
        ]

    if only_active:
        filtered = filtered[
            filtered["_active"]
        ]

    normalized_query = normalize_text(query)

    if normalized_query:
        searchable_columns = [
            "Nome Operadora",
            "Título",
            "Resumo",
            "Conteúdo",
            "Categoria",
            "Prioridade",
            "Público-alvo",
            "Responsável",
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

    return filtered.reset_index(drop=True)


def _render_comunicado(
    row: pd.Series,
    position: int,
) -> None:
    """Renderiza um comunicado individual."""

    title = (
        _safe_value(
            row,
            "Título",
        )
        or "Comunicado sem título"
    )

    summary = _safe_value(
        row,
        "Resumo",
    )

    content = _safe_value(
        row,
        "Conteúdo",
    )

    operator_name = (
        _safe_value(
            row,
            "Nome Operadora",
        )
        or "Comunicado geral"
    )

    category = (
        _safe_value(
            row,
            "Categoria",
        )
        or "Geral"
    )

    priority = (
        _safe_value(
            row,
            "Prioridade",
        )
        or "Não informada"
    )

    audience = (
        _safe_value(
            row,
            "Público-alvo",
        )
        or "Todos"
    )

    responsible = (
        _safe_value(
            row,
            "Responsável",
        )
        or "Não informado"
    )

    start_date = _format_date(
        _safe_value(
            row,
            "Data início",
        )
    )

    end_date = _format_date(
        _safe_value(
            row,
            "Data fim",
        )
    )

    link = _safe_value(
        row,
        "Link",
    )

    is_active = bool(
        row.get(
            "_active",
            False,
        )
    )

    priority_icon = {
        "alta": "🔴",
        "media": "🟠",
        "baixa": "🔵",
    }.get(
        normalize_text(priority),
        "📢",
    )

    with st.container(
        border=True,
    ):
        top_left, top_right = st.columns(
            [5, 1]
        )

        with top_left:
            st.markdown(
                f"### {priority_icon} {title}"
            )

        with top_right:
            if is_active:
                st.success(
                    "Ativo"
                )
            else:
                st.caption(
                    "Inativo"
                )

        st.caption(
            f"{category} • {operator_name}"
        )

        if summary:
            st.write(
                summary
            )

        detail_1, detail_2, detail_3 = (
            st.columns(3)
        )

        detail_1.markdown(
            f"**Prioridade:** {priority}"
        )

        detail_2.markdown(
            f"**Público:** {audience}"
        )

        detail_3.markdown(
            f"**Responsável:** {responsible}"
        )

        if start_date or end_date:
            period_1, period_2 = st.columns(
                2
            )

            period_1.markdown(
                "**Início:** "
                f"{start_date or 'Não informado'}"
            )

            period_2.markdown(
                "**Fim:** "
                f"{end_date or 'Sem previsão'}"
            )

        if content:
            with st.expander(
                "Ler comunicado completo",
                expanded=False,
            ):
                st.write(
                    content
                )

        if link.startswith(
            ("https://", "http://")
        ):
            st.link_button(
                "Abrir conteúdo relacionado",
                link,
                use_container_width=True,
            )


def render_comunicados() -> None:
    """Renderiza a página geral de comunicados."""

    render_hero(
        eyebrow="Atualizações comerciais",
        title="Comunicados",
        description=(
            "Acompanhe alterações de fluxo, "
            "orientações, novidades e informações "
            "importantes da área Comercial."
        ),
    )

    try:
        with st.spinner(
            "Carregando comunicados..."
        ):
            dataframe = (
                _build_comunicados_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar os comunicados "
            "neste momento."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhum comunicado foi encontrado."
        )
        return

    active_count = int(
        dataframe["_active"].sum()
    )

    high_priority_count = int(
        dataframe["Prioridade"]
        .map(normalize_text)
        .eq("alta")
        .sum()
    )

    metric_1, metric_2, metric_3 = (
        st.columns(3)
    )

    metric_1.metric(
        "Comunicados",
        len(dataframe),
    )

    metric_2.metric(
        "Ativos",
        active_count,
    )

    metric_3.metric(
        "Prioridade alta",
        high_priority_count,
    )

    query = st.text_input(
        label="Pesquisar comunicados",
        placeholder=(
            "Pesquise pelo título, conteúdo, "
            "operadora ou responsável..."
        ),
        key="comunicados_search_query",
    )

    operator_options = sorted(
        value
        for value in dataframe[
            "Nome Operadora"
        ].unique()
        if value
    )

    category_options = sorted(
        value
        for value in dataframe[
            "Categoria"
        ].unique()
        if value
    )

    priority_options = sorted(
        value
        for value in dataframe[
            "Prioridade"
        ].unique()
        if value
    )

    audience_options = sorted(
        value
        for value in dataframe[
            "Público-alvo"
        ].unique()
        if value
    )

    filter_1, filter_2 = st.columns(2)

    with filter_1:
        selected_operator = st.selectbox(
            label="Operadora",
            options=[
                "Todas",
                *operator_options,
            ],
            key="comunicados_operator_filter",
        )

        selected_priority = st.selectbox(
            label="Prioridade",
            options=[
                "Todas",
                *priority_options,
            ],
            key="comunicados_priority_filter",
        )

    with filter_2:
        selected_category = st.selectbox(
            label="Categoria",
            options=[
                "Todas",
                *category_options,
            ],
            key="comunicados_category_filter",
        )

        selected_audience = st.selectbox(
            label="Público-alvo",
            options=[
                "Todos",
                *audience_options,
            ],
            key="comunicados_audience_filter",
        )

    only_active = st.checkbox(
        label="Mostrar somente comunicados ativos",
        value=True,
        key="comunicados_active_filter",
    )

    filtered = _filter_comunicados(
        dataframe=dataframe,
        query=query,
        operator_name=selected_operator,
        category=selected_category,
        priority=selected_priority,
        audience=selected_audience,
        only_active=only_active,
    )

    st.caption(
        f"{len(filtered)} comunicado(s) encontrado(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhum comunicado corresponde aos "
            "filtros selecionados."
        )
        return

    for index, row in filtered.head(
        ITEMS_PER_PAGE
    ).iterrows():
        _render_comunicado(
            row=row,
            position=index,
        )

    if len(filtered) > ITEMS_PER_PAGE:
        st.info(
            "Existem mais comunicados. A paginação será "
            "adicionada quando ampliarmos a base real."
        )

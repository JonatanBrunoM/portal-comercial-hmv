from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import (
    get_contingencias,
    get_operadoras,
    get_planos,
)
from utils.formatting import normalize_text


ITEMS_PER_PAGE = 10


def _safe_value(
    row: pd.Series,
    column: str,
) -> str:
    """Retorna um campo textual sem gerar erro."""

    if column not in row.index:
        return ""

    value = row[column]

    if pd.isna(value):
        return ""

    return str(value).strip()


def _format_date(value: object) -> str:
    """Formata datas sem interromper a página."""

    if value is None or pd.isna(value):
        return ""

    if isinstance(value, (datetime, date)):
        return value.strftime("%d/%m/%Y")

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


def _priority_order(value: object) -> int:
    """Define a ordem visual das prioridades."""

    priority = normalize_text(value)

    order = {
        "alta": 0,
        "media": 1,
        "baixa": 2,
    }

    return order.get(priority, 3)


def _is_active_status(value: object) -> bool:
    """Identifica contingências atualmente ativas."""

    status = normalize_text(value)

    return status in {
        "ativa",
        "ativo",
        "publicavel",
        "publicável",
        "revisado",
    }


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def _build_contingencias_dataset() -> pd.DataFrame:
    """
    Une contingências, operadoras e planos em uma base única.
    """

    contingencias = get_contingencias()
    operadoras = get_operadoras()
    planos = get_planos()

    if contingencias is None or contingencias.empty:
        return pd.DataFrame()

    result = contingencias.copy()

    # Nome da operadora
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
                        operator_name_column: "Nome Operadora"
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

    # Nome do plano
    if (
        not planos.empty
        and "ID Plano" in planos.columns
        and "ID Plano" in result.columns
    ):
        plan_name_column = next(
            (
                column
                for column in [
                    "Nome padronizado",
                    "Plano",
                ]
                if column in planos.columns
            ),
            None,
        )

        if plan_name_column:
            plan_lookup = (
                planos[
                    [
                        "ID Plano",
                        plan_name_column,
                    ]
                ]
                .drop_duplicates(
                    subset=["ID Plano"]
                )
                .rename(
                    columns={
                        plan_name_column: "Nome Plano"
                    }
                )
            )

            result = result.merge(
                plan_lookup,
                how="left",
                on="ID Plano",
            )

    if "Nome Plano" not in result.columns:
        result["Nome Plano"] = ""

    required_columns = [
        "Nome Operadora",
        "Nome Plano",
        "Unidade",
        "Evento",
        "Data início",
        "Data fim",
        "Status contingência",
        "Orientação alternativa",
        "Contato alternativo",
        "Prioridade",
        "Destaque portal",
        "Status revisão",
        "Observações",
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

    result["_priority_order"] = (
        result["Prioridade"]
        .map(_priority_order)
    )

    result = result.sort_values(
        by=[
            "_priority_order",
            "Nome Operadora",
            "Evento",
        ],
        na_position="last",
    )

    return result.reset_index(drop=True)


def _filter_contingencias(
    dataframe: pd.DataFrame,
    query: str,
    operator_name: str,
    plan_name: str,
    unit: str,
    priority: str,
    status: str,
    only_highlighted: bool,
) -> pd.DataFrame:
    """Aplica os filtros da página."""

    filtered = dataframe.copy()

    if operator_name != "Todas":
        filtered = filtered[
            filtered["Nome Operadora"].eq(
                operator_name
            )
        ]

    if plan_name != "Todos":
        filtered = filtered[
            filtered["Nome Plano"].eq(
                plan_name
            )
        ]

    if unit != "Todas":
        filtered = filtered[
            filtered["Unidade"].eq(
                unit
            )
        ]

    if priority != "Todas":
        filtered = filtered[
            filtered["Prioridade"].eq(
                priority
            )
        ]

    if status != "Todos":
        filtered = filtered[
            filtered["Status contingência"].eq(
                status
            )
        ]

    if only_highlighted:
        highlighted = (
            filtered["Destaque portal"]
            .fillna("")
            .astype(str)
            .map(normalize_text)
        )

        filtered = filtered[
            highlighted.eq("sim")
        ]

    normalized_query = normalize_text(
        query
    )

    if normalized_query:
        searchable_columns = [
            "Nome Operadora",
            "Nome Plano",
            "Unidade",
            "Evento",
            "Status contingência",
            "Orientação alternativa",
            "Contato alternativo",
            "Prioridade",
            "Observações",
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


def _render_contingencia(
    row: pd.Series,
    position: int,
) -> None:
    """Renderiza uma contingência individual."""

    event = (
        _safe_value(
            row,
            "Evento",
        )
        or "Contingência sem identificação"
    )

    operator_name = (
        _safe_value(
            row,
            "Nome Operadora",
        )
        or "Operadora não identificada"
    )

    plan_name = (
        _safe_value(
            row,
            "Nome Plano",
        )
        or "Todos os planos"
    )

    unit = (
        _safe_value(
            row,
            "Unidade",
        )
        or "Não informada"
    )

    priority = (
        _safe_value(
            row,
            "Prioridade",
        )
        or "Não informada"
    )

    status = (
        _safe_value(
            row,
            "Status contingência",
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

    guidance = _safe_value(
        row,
        "Orientação alternativa",
    )

    alternative_contact = _safe_value(
        row,
        "Contato alternativo",
    )

    observations = _safe_value(
        row,
        "Observações",
    )

    contingency_id = (
        _safe_value(
            row,
            "ID Contingência",
        )
        or str(position)
    )

    priority_icon = {
        "alta": "🔴",
        "media": "🟠",
        "baixa": "🟡",
    }.get(
        normalize_text(priority),
        "⚠️",
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### {priority_icon} {event}"
        )

        st.caption(
            f"{operator_name} • {plan_name}"
        )

        detail_1, detail_2, detail_3 = (
            st.columns(3)
        )

        detail_1.markdown(
            f"**Prioridade:** {priority}"
        )

        detail_2.markdown(
            f"**Status:** {status}"
        )

        detail_3.markdown(
            f"**Unidade:** {unit}"
        )

        if start_date or end_date:
            date_1, date_2 = st.columns(2)

            date_1.markdown(
                "**Início:** "
                f"{start_date or 'Não informado'}"
            )

            date_2.markdown(
                "**Fim:** "
                f"{end_date or 'Sem previsão'}"
            )

        if guidance:
            st.markdown(
                "**Orientação alternativa:**"
            )

            st.write(
                guidance
            )

        if alternative_contact:
            st.markdown(
                f"**Contato alternativo:** "
                f"{alternative_contact}"
            )

        if observations:
            with st.expander(
                "Observações",
                expanded=False,
            ):
                st.write(
                    observations
                )

        if _is_active_status(status):
            st.success(
                "Contingência ativa ou validada."
            )

        else:
            st.caption(
                "Registro ainda não marcado como ativo."
            )

        st.caption(
            f"Identificador: {contingency_id}"
        )


def _render_pagination(
    total_items: int,
) -> tuple[int, int]:
    """Cria a paginação e retorna o intervalo atual."""

    total_pages = max(
        1,
        (
            total_items
            + ITEMS_PER_PAGE
            - 1
        )
        // ITEMS_PER_PAGE,
    )

    if (
        "contingencias_page"
        not in st.session_state
    ):
        st.session_state.contingencias_page = 1

    if (
        st.session_state.contingencias_page
        > total_pages
    ):
        st.session_state.contingencias_page = 1

    previous_col, page_col, next_col = (
        st.columns(
            [1, 2, 1]
        )
    )

    with previous_col:
        if st.button(
            "← Anterior",
            disabled=(
                st.session_state.contingencias_page
                <= 1
            ),
            use_container_width=True,
            key="contingencias_previous_page",
        ):
            st.session_state.contingencias_page -= 1
            st.rerun()

    with page_col:
        st.markdown(
            (
                "<div style='text-align:center;"
                "padding:0.65rem;'>"
                f"Página "
                f"{st.session_state.contingencias_page} "
                f"de {total_pages}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    with next_col:
        if st.button(
            "Próxima →",
            disabled=(
                st.session_state.contingencias_page
                >= total_pages
            ),
            use_container_width=True,
            key="contingencias_next_page",
        ):
            st.session_state.contingencias_page += 1
            st.rerun()

    start = (
        st.session_state.contingencias_page
        - 1
    ) * ITEMS_PER_PAGE

    end = start + ITEMS_PER_PAGE

    return start, end


def render_contingencias() -> None:
    """Renderiza a página geral de contingências."""

    render_hero(
        eyebrow="Alertas e fluxos alternativos",
        title="Contingências",
        description=(
            "Consulte indisponibilidades, restrições, "
            "exceções operacionais e orientações "
            "alternativas das operadoras."
        ),
    )

    try:
        with st.spinner(
            "Carregando contingências..."
        ):
            dataframe = (
                _build_contingencias_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar as contingências "
            "neste momento."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhuma contingência foi encontrada "
            "na base."
        )
        return

    active_count = int(
        dataframe[
            "Status contingência"
        ]
        .map(_is_active_status)
        .sum()
    )

    high_priority_count = int(
        dataframe[
            "Prioridade"
        ]
        .map(normalize_text)
        .eq("alta")
        .sum()
    )

    metric_1, metric_2, metric_3 = (
        st.columns(3)
    )

    metric_1.metric(
        "Registros",
        len(dataframe),
    )

    metric_2.metric(
        "Ativas ou validadas",
        active_count,
    )

    metric_3.metric(
        "Prioridade alta",
        high_priority_count,
    )

    query = st.text_input(
        label="Pesquisar contingências",
        placeholder=(
            "Pesquise por operadora, evento, "
            "orientação ou contato..."
        ),
        key="contingencias_search_query",
    )

    operator_options = sorted(
        value
        for value in dataframe[
            "Nome Operadora"
        ].unique()
        if value
    )

    selected_operator = st.selectbox(
        label="Operadora",
        options=[
            "Todas",
            *operator_options,
        ],
        key="contingencias_operator_filter",
    )

    operator_filtered = dataframe

    if selected_operator != "Todas":
        operator_filtered = dataframe[
            dataframe["Nome Operadora"].eq(
                selected_operator
            )
        ]

    plan_options = sorted(
        value
        for value in operator_filtered[
            "Nome Plano"
        ].unique()
        if value
    )

    unit_options = sorted(
        value
        for value in operator_filtered[
            "Unidade"
        ].unique()
        if value
    )

    priority_options = sorted(
        value
        for value in operator_filtered[
            "Prioridade"
        ].unique()
        if value
    )

    status_options = sorted(
        value
        for value in operator_filtered[
            "Status contingência"
        ].unique()
        if value
    )

    filter_1, filter_2 = st.columns(2)

    with filter_1:
        selected_plan = st.selectbox(
            label="Plano",
            options=[
                "Todos",
                *plan_options,
            ],
            key="contingencias_plan_filter",
        )

        selected_priority = st.selectbox(
            label="Prioridade",
            options=[
                "Todas",
                *priority_options,
            ],
            key="contingencias_priority_filter",
        )

    with filter_2:
        selected_unit = st.selectbox(
            label="Unidade",
            options=[
                "Todas",
                *unit_options,
            ],
            key="contingencias_unit_filter",
        )

        selected_status = st.selectbox(
            label="Status",
            options=[
                "Todos",
                *status_options,
            ],
            key="contingencias_status_filter",
        )

    only_highlighted = st.checkbox(
        label=(
            "Mostrar somente registros marcados "
            "para destaque no portal"
        ),
        key="contingencias_highlight_filter",
    )

    filtered = _filter_contingencias(
        dataframe=dataframe,
        query=query,
        operator_name=selected_operator,
        plan_name=selected_plan,
        unit=selected_unit,
        priority=selected_priority,
        status=selected_status,
        only_highlighted=only_highlighted,
    )

    # Volta à primeira página quando os filtros mudam.
    filter_signature = (
        query,
        selected_operator,
        selected_plan,
        selected_unit,
        selected_priority,
        selected_status,
        only_highlighted,
    )

    previous_signature = (
        st.session_state.get(
            "contingencias_filter_signature"
        )
    )

    if previous_signature != filter_signature:
        st.session_state[
            "contingencias_filter_signature"
        ] = filter_signature

        st.session_state.contingencias_page = 1

    st.caption(
        f"{len(filtered)} contingência(s) "
        "encontrada(s)."
    )

    if filtered.empty:
        st.info(
            "Nenhuma contingência corresponde aos "
            "filtros selecionados."
        )
        return

    start, end = _render_pagination(
        len(filtered)
    )

    current_page = filtered.iloc[
        start:end
    ]

    for index, row in current_page.iterrows():
        _render_contingencia(
            row=row,
            position=index,
        )

    if len(filtered) > ITEMS_PER_PAGE:
        _render_pagination(
            len(filtered)
        )

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.sheets_service import get_particular
from utils.formatting import normalize_text


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


def _is_email(value: str) -> bool:
    """Valida um endereço de e-mail em formato básico."""

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value.strip(),
        )
    )


def _clean_phone(value: str) -> str:
    """Remove caracteres desnecessários do telefone."""

    return re.sub(
        r"[^\d+]",
        "",
        value,
    )


def _is_active(value: object) -> bool:
    """Verifica se o registro está ativo."""

    return normalize_text(value) in {
        "ativo",
        "ativa",
        "publicavel",
        "revisado",
    }


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _build_particular_dataset() -> pd.DataFrame:
    """Carrega e padroniza a base do atendimento particular."""

    dataframe = get_particular()

    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    result = dataframe.copy()

    required_columns = [
        "ID Particular",
        "Categoria",
        "Subcategoria",
        "Título",
        "Resumo",
        "Orientação completa",
        "Unidade",
        "Tipo atendimento",
        "Especialidade",
        "Documento necessário",
        "Canal de contato",
        "Telefone",
        "E-mail",
        "Link",
        "Valor informado",
        "Observação sobre valor",
        "Público-alvo",
        "Palavras-chave",
        "Prioridade",
        "Destaque portal",
        "Data início",
        "Data fim",
        "Status",
        "Status revisão",
        "Responsável revisão",
        "Data revisão",
        "Observações internas",
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

    result = result[
        result["Status"].map(_is_active)
    ].copy()

    priority_order = {
        "alta": 0,
        "media": 1,
        "baixa": 2,
    }

    result["_priority_order"] = (
        result["Prioridade"]
        .map(normalize_text)
        .map(priority_order)
        .fillna(3)
    )

    result = result.sort_values(
        by=[
            "_priority_order",
            "Categoria",
            "Subcategoria",
            "Título",
        ],
        na_position="last",
    )

    return result.reset_index(drop=True)


def _filter_particular(
    dataframe: pd.DataFrame,
    query: str,
    category: str,
    subcategory: str,
    unit: str,
    attendance_type: str,
    only_highlighted: bool,
) -> pd.DataFrame:
    """Aplica os filtros do módulo Particular."""

    filtered = dataframe.copy()

    if category != "Todas":
        filtered = filtered[
            filtered["Categoria"].eq(
                category
            )
        ]

    if subcategory != "Todas":
        filtered = filtered[
            filtered["Subcategoria"].eq(
                subcategory
            )
        ]

    if unit != "Todas":
        filtered = filtered[
            filtered["Unidade"].eq(
                unit
            )
        ]

    if attendance_type != "Todos":
        filtered = filtered[
            filtered["Tipo atendimento"].eq(
                attendance_type
            )
        ]

    if only_highlighted:
        highlighted = (
            filtered["Destaque portal"]
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
            "Categoria",
            "Subcategoria",
            "Título",
            "Resumo",
            "Orientação completa",
            "Unidade",
            "Tipo atendimento",
            "Especialidade",
            "Documento necessário",
            "Canal de contato",
            "Público-alvo",
            "Palavras-chave",
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


def _render_contact_actions(
    email: str,
    phone: str,
    link: str,
    item_id: str,
) -> None:
    """Renderiza ações disponíveis para o registro."""

    actions: list[tuple[str, str]] = []

    if _is_email(email):
        actions.append(
            (
                "Enviar e-mail",
                f"mailto:{email}",
            )
        )

    cleaned_phone = _clean_phone(
        phone
    )

    if cleaned_phone:
        actions.append(
            (
                "Ligar",
                f"tel:{cleaned_phone}",
            )
        )

    if link.startswith(
        ("https://", "http://")
    ):
        actions.append(
            (
                "Abrir link",
                link,
            )
        )

    if not actions:
        st.button(
            "Sem ação disponível",
            key=f"particular_no_action_{item_id}",
            disabled=True,
            use_container_width=True,
        )
        return

    columns = st.columns(
        len(actions)
    )

    for column, (
        label,
        url,
    ) in zip(
        columns,
        actions,
    ):
        with column:
            st.link_button(
                label,
                url,
                use_container_width=True,
            )


def _render_particular_item(
    row: pd.Series,
    position: int,
) -> None:
    """Renderiza uma orientação do módulo Particular."""

    title = (
        _safe_value(
            row,
            "Título",
        )
        or "Orientação sem título"
    )

    category = (
        _safe_value(
            row,
            "Categoria",
        )
        or "Geral"
    )

    subcategory = (
        _safe_value(
            row,
            "Subcategoria",
        )
        or "Geral"
    )

    summary = _safe_value(
        row,
        "Resumo",
    )

    guidance = _safe_value(
        row,
        "Orientação completa",
    )

    unit = (
        _safe_value(
            row,
            "Unidade",
        )
        or "Não informada"
    )

    attendance_type = (
        _safe_value(
            row,
            "Tipo atendimento",
        )
        or "Não informado"
    )

    specialty = (
        _safe_value(
            row,
            "Especialidade",
        )
        or "Não informada"
    )

    document = (
        _safe_value(
            row,
            "Documento necessário",
        )
        or "Não informado"
    )

    channel = (
        _safe_value(
            row,
            "Canal de contato",
        )
        or "Não informado"
    )

    phone = _safe_value(
        row,
        "Telefone",
    )

    email = _safe_value(
        row,
        "E-mail",
    )

    link = _safe_value(
        row,
        "Link",
    )

    informed_value = _safe_value(
        row,
        "Valor informado",
    )

    value_observation = _safe_value(
        row,
        "Observação sobre valor",
    )

    audience = (
        _safe_value(
            row,
            "Público-alvo",
        )
        or "Não informado"
    )

    priority = (
        _safe_value(
            row,
            "Prioridade",
        )
        or "Não informada"
    )

    review_status = (
        _safe_value(
            row,
            "Status revisão",
        )
        or "Não informado"
    )

    review_responsible = (
        _safe_value(
            row,
            "Responsável revisão",
        )
        or "Não informado"
    )

    item_id = (
        _safe_value(
            row,
            "ID Particular",
        )
        or str(position)
    )

    icon = {
        "alta": "🔴",
        "media": "🟠",
        "baixa": "🔵",
    }.get(
        normalize_text(priority),
        "💳",
    )

    with st.container(
        border=True,
    ):
        st.markdown(
            f"### {icon} {title}"
        )

        st.caption(
            f"{category} • {subcategory}"
        )

        if summary:
            st.write(
                summary
            )

        detail_1, detail_2, detail_3 = (
            st.columns(3)
        )

        detail_1.markdown(
            f"**Unidade:** {unit}"
        )

        detail_2.markdown(
            f"**Atendimento:** {attendance_type}"
        )

        detail_3.markdown(
            f"**Prioridade:** {priority}"
        )

        st.markdown(
            f"**Especialidade:** {specialty}"
        )

        st.markdown(
            f"**Documento necessário:** {document}"
        )

        if guidance:
            with st.expander(
                "Orientação completa",
                expanded=False,
            ):
                st.write(
                    guidance
                )

        with st.expander(
            "Contato e direcionamento",
            expanded=False,
        ):
            st.markdown(
                f"**Canal:** {channel}"
            )

            st.markdown(
                f"**Telefone:** "
                f"{phone or 'Não informado'}"
            )

            st.markdown(
                f"**E-mail:** "
                f"{email or 'Não informado'}"
            )

            st.markdown(
                f"**Público-alvo:** {audience}"
            )

        if informed_value or value_observation:
            with st.expander(
                "Informações sobre valores",
                expanded=False,
            ):
                if informed_value:
                    st.markdown(
                        f"**Valor informado:** "
                        f"{informed_value}"
                    )

                if value_observation:
                    st.warning(
                        value_observation
                    )

        st.caption(
            f"Revisão: {review_status} • "
            f"Responsável: {review_responsible}"
        )

        _render_contact_actions(
            email=email,
            phone=phone,
            link=link,
            item_id=item_id,
        )


def render_particular() -> None:
    """Renderiza a página de atendimento particular."""

    render_hero(
        eyebrow="Atendimento sem convênio",
        title="Particular",
        description=(
            "Consulte orientações de atendimento, "
            "documentos, orçamentos, pagamentos e "
            "canais de contato para pacientes particulares."
        ),
    )

    try:
        with st.spinner(
            "Carregando informações..."
        ):
            dataframe = (
                _build_particular_dataset()
            )

    except RuntimeError:
        st.error(
            "Não foi possível carregar as informações "
            "do atendimento particular."
        )
        return

    if dataframe.empty:
        st.info(
            "Nenhuma informação de atendimento "
            "particular foi encontrada."
        )
        return

    query = st.text_input(
        label="Pesquisar atendimento particular",
        placeholder=(
            "Pesquise por consulta, exame, orçamento, "
            "internação ou pagamento..."
        ),
        key="particular_search_query",
    )

    category_options = sorted(
        value
        for value in dataframe[
            "Categoria"
        ].unique()
        if value
    )

    selected_category = st.selectbox(
        label="Categoria",
        options=[
            "Todas",
            *category_options,
        ],
        key="particular_category_filter",
    )

    category_filtered = dataframe

    if selected_category != "Todas":
        category_filtered = dataframe[
            dataframe["Categoria"].eq(
                selected_category
            )
        ]

    subcategory_options = sorted(
        value
        for value in category_filtered[
            "Subcategoria"
        ].unique()
        if value
    )

    unit_options = sorted(
        value
        for value in category_filtered[
            "Unidade"
        ].unique()
        if value
    )

    attendance_options = sorted(
        value
        for value in category_filtered[
            "Tipo atendimento"
        ].unique()
        if value
    )

    filter_1, filter_2, filter_3 = (
        st.columns(3)
    )

    with filter_1:
        selected_subcategory = st.selectbox(
            label="Subcategoria",
            options=[
                "Todas",
                *subcategory_options,
            ],
            key="particular_subcategory_filter",
        )

    with filter_2:
        selected_unit = st.selectbox(
            label="Unidade",
            options=[
                "Todas",
                *unit_options,
            ],
            key="particular_unit_filter",
        )

    with filter_3:
        selected_attendance = st.selectbox(
            label="Tipo de atendimento",
            options=[
                "Todos",
                *attendance_options,
            ],
            key="particular_attendance_filter",
        )

    only_highlighted = st.checkbox(
        label=(
            "Mostrar somente conteúdos destacados "
            "para o portal"
        ),
        key="particular_highlight_filter",
    )

    filtered = _filter_particular(
        dataframe=dataframe,
        query=query,
        category=selected_category,
        subcategory=selected_subcategory,
        unit=selected_unit,
        attendance_type=selected_attendance,
        only_highlighted=only_highlighted,
    )

    metric_1, metric_2, metric_3 = (
        st.columns(3)
    )

    metric_1.metric(
        "Orientações",
        len(filtered),
    )

    metric_2.metric(
        "Categorias",
        filtered["Categoria"].nunique(),
    )

    metric_3.metric(
        "Destaques",
        int(
            filtered["Destaque portal"]
            .map(normalize_text)
            .eq("sim")
            .sum()
        ),
    )

    if filtered.empty:
        st.info(
            "Nenhuma orientação corresponde aos "
            "filtros selecionados."
        )
        return

    for index, row in filtered.iterrows():
        _render_particular_item(
            row=row,
            position=index,
        )

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from components.operadora_cards import render_operadora_card
from core.operadoras_service import (
    get_operadora_autorizacoes,
    get_operadora_by_id,
    get_operadora_coberturas,
    get_operadora_contatos,
    get_operadora_contingencias,
    get_operadora_documentos,
    get_operadora_elegibilidade,
    get_operadora_planos,
    get_operadora_portais,
    search_operadoras,
)


def _safe_text(row: pd.Series, column: str) -> str:
    """Retorna o valor textual de uma coluna sem gerar erro."""
    if column not in row.index:
        return ""

    value = row[column]
    if pd.isna(value):
        return ""

    return str(value).strip()


def _render_empty_module(message: str) -> None:
    """Exibe um estado vazio padronizado."""
    st.info(message)


def _render_planos(operator_id: str) -> None:
    """Renderiza os planos vinculados à operadora."""
    planos = get_operadora_planos(operator_id)

    if planos.empty:
        _render_empty_module("Nenhum plano ativo foi encontrado.")
        return

    st.caption(f"{len(planos)} plano(s) cadastrado(s).")

    for _, plano in planos.iterrows():
        plan_name = (
            _safe_text(plano, "nome_padronizado")
            or "Plano sem nome"
        )
        plan_type = _safe_text(plano, "tipo_plano") or "Tipo não informado"

        with st.expander(f"📋 {plan_name}", expanded=False):
            col_1, col_2 = st.columns(2)
            col_1.markdown(f"**Tipo:** {plan_type}")
            col_2.markdown(f"**Código:** {_safe_text(plano, 'codigo') or 'Não informado'}")

            observation = _safe_text(plano, "observacao_resumida")
            if observation:
                st.markdown(f"**Observação:** {observation}")


def _render_portais(operator_id: str) -> None:
    """Renderiza os portais vinculados à operadora."""
    portais = get_operadora_portais(operator_id)

    if portais.empty:
        _render_empty_module("Nenhum portal foi encontrado.")
        return

    st.caption(f"{len(portais)} portal(is) encontrado(s).")

    for _, portal in portais.iterrows():
        name = _safe_text(portal, "nome") or "Portal sem nome"
        url = _safe_text(portal, "url")
        portal_type = _safe_text(portal, "tipo")
        instructions = _safe_text(portal, "instrucao_acesso")

        with st.expander(f"🌐 {name}", expanded=False):
            if portal_type:
                st.markdown(f"**Tipo:** {portal_type}")
            if instructions:
                st.markdown(f"**Orientação:** {instructions}")
            if url:
                st.link_button("Abrir portal", url, use_container_width=True)


def _render_elegibilidade(operator_id: str) -> None:
    """Renderiza as regras de elegibilidade."""
    dataframe = get_operadora_elegibilidade(operator_id)

    if dataframe.empty:
        _render_empty_module("Nenhuma regra de elegibilidade foi encontrada.")
        return

    st.caption(f"{len(dataframe)} regra(s) encontrada(s).")

    for _, item in dataframe.iterrows():
        attendance_type = "Regra específica" if _safe_text(item, "tipo_atendimento_id") else "Regra geral"

        with st.expander(f"✅ {attendance_type}", expanded=False):
            how_to = _safe_text(item, "orientacao")
            necessary = bool(item.get("necessario", True))
            st.markdown(
                f"**Verificação necessária:** {'Sim' if necessary else 'Não'}"
            )
            if how_to:
                st.markdown("**Orientação:**")
                st.write(how_to)


def _render_documentos(operator_id: str) -> None:
    """Renderiza os documentos necessários."""
    dataframe = get_operadora_documentos(operator_id)

    if dataframe.empty:
        _render_empty_module("Nenhum documento foi encontrado.")
        return

    st.caption(f"{len(dataframe)} registro(s) encontrado(s).")

    for _, item in dataframe.iterrows():
        document = _safe_text(item, "nome") or "Documento sem identificação"
        attendance_type = "Atendimento específico" if _safe_text(item, "tipo_atendimento_id") else ""

        with st.expander(f"📄 {document}", expanded=False):
            col_1, col_2 = st.columns(2)
            col_1.markdown(
                "**Obrigatório:** "
                f"{'Sim' if bool(item.get('obrigatorio', False)) else 'Não'}"
            )

            validity = _safe_text(item, "validade_dias")
            col_2.markdown(
                "**Validade:** "
                f"{validity + ' dias' if validity else 'Não informada'}"
            )

            if attendance_type:
                st.markdown(f"**Atendimento:** {attendance_type}")

            original_copy = _safe_text(item, "formato")
            if original_copy:
                st.markdown(f"**Formato:** {original_copy}")

            observations = _safe_text(item, "observacoes")
            if observations:
                st.write(observations)


def _render_autorizacoes(operator_id: str) -> None:
    """Renderiza as regras de autorização."""
    dataframe = get_operadora_autorizacoes(operator_id)

    if dataframe.empty:
        _render_empty_module("Nenhuma regra de autorização foi encontrada.")
        return

    st.caption(f"{len(dataframe)} regra(s) encontrada(s).")

    for _, item in dataframe.iterrows():
        attendance_type = "Autorização específica" if _safe_text(item, "tipo_atendimento_id") else "Autorização geral"

        with st.expander(f"🔑 {attendance_type}", expanded=False):
            col_1, col_2 = st.columns(2)
            col_1.markdown(
                "**Necessita autorização:** "
                f"{'Sim' if bool(item.get('necessita_autorizacao', True)) else 'Não'}"
            )
            col_2.markdown(
                "**Momento:** "
                f"{_safe_text(item, 'momento_autorizacao') or 'Não informado'}"
            )

            requester = _safe_text(item, "quem_solicita")
            method = _safe_text(item, "meio_solicitacao")
            return_time = _safe_text(item, "prazo")

            if requester:
                st.markdown(f"**Quem solicita:** {requester}")
            if method:
                st.markdown(f"**Meio:** {method}")
            if return_time:
                st.markdown(f"**Prazo:** {return_time}")

            observations = _safe_text(item, "observacoes")
            if observations:
                st.write(observations)


def _render_coberturas(operator_id: str) -> None:
    """Renderiza as coberturas da operadora."""
    dataframe = get_operadora_coberturas(operator_id)

    if dataframe.empty:
        _render_empty_module("Nenhuma cobertura foi encontrada.")
        return

    st.caption(f"{len(dataframe)} cobertura(s) encontrada(s).")

    for _, item in dataframe.iterrows():
        attendance_type = "Cobertura específica" if _safe_text(item, "tipo_atendimento_id") else "Cobertura geral"
        covered_raw = item.get("coberto")
        covered = "Sim" if covered_raw is True else "Não" if covered_raw is False else "Não informado"

        with st.expander(f"🩺 {attendance_type} — {covered}", expanded=False):
            accommodation = _safe_text(item, "acomodacao")
            companion = _safe_text(item, "acompanhante")
            restriction = _safe_text(item, "restricoes_cobertura")

            if accommodation:
                st.markdown(f"**Acomodação:** {accommodation}")
            if companion:
                st.markdown(f"**Acompanhante:** {companion}")
            if restriction:
                st.markdown(f"**Restrição:** {restriction}")

            observations = _safe_text(item, "observacoes")
            if observations:
                st.write(observations)


def _render_contatos(operator_id: str) -> None:
    """Renderiza os contatos da operadora."""
    dataframe = get_operadora_contatos(operator_id)

    if dataframe.empty:
        _render_empty_module("Nenhum contato foi encontrado.")
        return

    st.caption(f"{len(dataframe)} contato(s) encontrado(s).")

    for _, item in dataframe.iterrows():
        purpose = _safe_text(item, "finalidade") or "Contato geral"
        contact_type = _safe_text(item, "tipo")
        contact = _safe_text(item, "contato")

        with st.expander(f"📞 {purpose}", expanded=False):
            if contact_type:
                st.markdown(f"**Tipo:** {contact_type}")
            if contact:
                st.markdown(f"**Contato:** {contact}")

            responsible = _safe_text(item, "responsavel")
            schedule = _safe_text(item, "horario_atendimento")

            if responsible:
                st.markdown(f"**Responsável:** {responsible}")
            if schedule:
                st.markdown(f"**Horário:** {schedule}")


def _render_contingencias(operator_id: str) -> None:
    """Renderiza contingências e exceções operacionais."""
    dataframe = get_operadora_contingencias(operator_id)

    if dataframe.empty:
        _render_empty_module("Nenhuma contingência foi encontrada.")
        return

    st.warning(
        f"{len(dataframe)} contingência(s) ou exceção(ões) operacional(is) "
        "encontrada(s)."
    )

    for _, item in dataframe.iterrows():
        event = _safe_text(item, "titulo") or "Contingência"
        priority = _safe_text(item, "prioridade")

        with st.expander(
            f"⚠️ {event}",
            expanded=priority.casefold() == "alta",
        ):
            if priority:
                st.markdown(f"**Prioridade:** {priority}")

            guidance = _safe_text(item, "orientacao_alternativa")
            if guidance:
                st.markdown("**Orientação:**")
                st.write(guidance)

            observations = _safe_text(item, "observacoes")
            if observations:
                st.caption(observations)


def render_operadora_detail(operator_id: str) -> None:
    """Renderiza a ficha completa de uma operadora."""
    operadora = get_operadora_by_id(operator_id)

    if operadora is None:
        st.error("Não foi possível localizar essa operadora.")

        if st.button("Voltar para operadoras", use_container_width=False):
            st.session_state.pop("selected_operator_id", None)
            st.rerun()
        return

    top_left, top_right = st.columns([5, 1])

    with top_left:
        render_hero(
            eyebrow="Ficha da operadora",
            title=operadora.short_name,
            description=(
                operadora.name
                if operadora.name != operadora.short_name
                else "Consulte os planos e informações relacionadas a esta operadora."
            ),
        )

    with top_right:
        if st.button("← Voltar", use_container_width=True):
            st.session_state.pop("selected_operator_id", None)
            st.rerun()

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Planos cadastrados", operadora.plans_count)
    metric_2.metric("Status", operadora.status or "Não informado")
    metric_3.metric("Consultor", operadora.consultant or "Não definido")

    if operadora.observations:
        with st.expander("Observações da operadora", expanded=False):
            st.write(operadora.observations)

    st.markdown(
        "## Informações da operadora"
    )

    module_options = {
        "Planos": "📋",
        "Portais": "🌐",
        "Elegibilidade": "✅",
        "Documentos": "📄",
        "Autorizações": "🔑",
        "Coberturas": "🩺",
        "Contatos": "📞",
        "Contingências": "⚠️",
    }

    selected_module = st.segmented_control(
        label="Selecione uma categoria",
        options=list(module_options),
        default="Planos",
        format_func=lambda option: (
            f"{module_options[option]} {option}"
        ),
        key=(
            "operator_module_"
            f"{operator_id}"
        ),
        selection_mode="single",
        width="stretch",
        label_visibility="collapsed",
    )

    st.divider()

    if selected_module == "Planos":
        _render_planos(
            operator_id
        )

    elif selected_module == "Portais":
        _render_portais(
            operator_id
        )

    elif selected_module == "Elegibilidade":
        _render_elegibilidade(
            operator_id
        )

    elif selected_module == "Documentos":
        _render_documentos(
            operator_id
        )

    elif selected_module == "Autorizações":
        _render_autorizacoes(
            operator_id
        )

    elif selected_module == "Coberturas":
        _render_coberturas(
            operator_id
        )

    elif selected_module == "Contatos":
        _render_contatos(
            operator_id
        )

    elif selected_module == "Contingências":
        _render_contingencias(
            operator_id
        )


def render_operadoras() -> None:
    """Renderiza a listagem ou a ficha de operadoras."""
    selected_operator_id = st.session_state.get("selected_operator_id")

    if selected_operator_id:
        render_operadora_detail(selected_operator_id)
        return

    render_hero(
        eyebrow="Convênios e planos",
        title="Operadoras",
        description=(
            "Encontre uma operadora e consulte seus planos e informações relacionadas."
        ),
    )

    query = st.text_input(
        label="Pesquisar operadora",
        placeholder="Digite o nome da operadora...",
        key="operator_search_query",
    )

    with st.spinner("Carregando operadoras..."):
        operadoras = search_operadoras(query)

    st.caption(f"{len(operadoras)} operadora(s) encontrada(s).")

    if not operadoras:
        st.info("Nenhuma operadora foi encontrada para essa pesquisa.")
        return

    columns_per_row = 3

    for start in range(0, len(operadoras), columns_per_row):
        columns = st.columns(columns_per_row)
        batch = operadoras[start : start + columns_per_row]

        for column, operadora in zip(columns, batch):
            with column:
                if render_operadora_card(operadora):
                    st.session_state["selected_operator_id"] = operadora.operator_id
                    st.rerun()

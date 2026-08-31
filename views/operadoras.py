from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from components.hero import render_hero
from components.operadora_cards import render_operadora_card
from core.operadoras_service import (
    get_operadora_autorizacoes,
    get_operadora_by_id,
    get_operadora_coberturas,
    get_operadora_comunicados,
    get_operadora_consultores,
    get_operadora_contatos,
    get_operadora_contingencias,
    get_operadora_counts,
    get_operadora_dicas,
    get_operadora_documentos,
    get_operadora_elegibilidade,
    get_operadora_planos,
    get_operadora_portais,
    search_operadoras,
)


BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def _safe_text(row: pd.Series, column: str) -> str:
    if column not in row.index:
        return ""
    value = row[column]
    if pd.isna(value):
        return ""
    return str(value).strip()


def _safe_bool(value: object, default: bool = False) -> bool:
    if value is None or pd.isna(value):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() in {"1", "true", "sim", "yes"}


def _date_only(value: object):
    if value is None or pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    parsed = pd.Timestamp(parsed)
    if parsed.tzinfo is not None:
        parsed = parsed.tz_convert(BRAZIL_TZ).tz_localize(None)
    return parsed.date()


def _period_active(row: pd.Series) -> bool:
    today = datetime.now(BRAZIL_TZ).date()
    start = _date_only(row.get("inicio_em"))
    end = _date_only(row.get("fim_em"))
    return not ((start and today < start) or (end and today > end))


def _render_empty_module(message: str) -> None:
    st.info(message)


def _section_intro(title: str, description: str) -> None:
    st.markdown(f"### {title}")
    st.caption(description)


def _render_overview(operator_id: str, operadora) -> None:
    counts = get_operadora_counts(operator_id)

    _section_intro(
        "Visão geral",
        "Resumo rápido das principais informações disponíveis para esta operadora.",
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Planos", counts["planos"])
    m2.metric("Portais", counts["portais"])
    m3.metric("Documentos", counts["documentos"])
    m4.metric("Contatos", counts["contatos"])

    contingencias = get_operadora_contingencias(operator_id)
    if not contingencias.empty:
        active = contingencias[contingencias.apply(_period_active, axis=1)]
        if not active.empty:
            high = active[
                active.get("prioridade", pd.Series(index=active.index, dtype=str))
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
                .eq("alta")
            ]
            message = (
                f"Há {len(active)} contingência(s) vigente(s) para esta operadora."
            )
            if not high.empty:
                message += f" {len(high)} com prioridade alta."
            st.warning(message)

    comunicados = get_operadora_comunicados(operator_id)
    if not comunicados.empty:
        published = comunicados[
            comunicados.apply(
                lambda row: (
                    _safe_text(row, "status").casefold()
                    in {"publicado", "publicada", "ativo"}
                    and _period_active(row)
                ),
                axis=1,
            )
        ]
        if not published.empty:
            st.info(f"{len(published)} comunicado(s) vigente(s) disponível(is).")

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("**Identificação**")
            st.write(f"**Nome:** {operadora.name}")
            st.write(f"**Código:** {operadora.code or 'Não informado'}")
            st.write(f"**Status:** {operadora.status or 'Não informado'}")
            if operadora.consultant:
                st.write(f"**Consultor:** {operadora.consultant}")

    with c2:
        with st.container(border=True):
            st.markdown("**Acesso rápido**")
            if operadora.site_url:
                st.link_button(
                    "Abrir site da operadora",
                    operadora.site_url,
                    use_container_width=True,
                )
            if counts["portais"]:
                st.caption(
                    "Os portais operacionais estão disponíveis na categoria "
                    "**Portais e acessos**."
                )
            else:
                st.caption("Nenhum portal operacional cadastrado.")

    if operadora.observations:
        with st.expander("Observações da operadora", expanded=False):
            st.write(operadora.observations)


def _render_planos(operator_id: str) -> None:
    planos = get_operadora_planos(operator_id)
    _section_intro("Planos", "Planos ativos vinculados à operadora.")

    if planos.empty:
        _render_empty_module("Nenhum plano ativo foi encontrado.")
        return

    for _, plano in planos.iterrows():
        plan_name = (
            _safe_text(plano, "nome_padronizado")
            or _safe_text(plano, "nome")
            or "Plano sem nome"
        )
        plan_type = _safe_text(plano, "tipo_plano") or "Tipo não informado"

        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{plan_name}**")
                st.caption(plan_type)
            with right:
                code = _safe_text(plano, "codigo") or "—"
                st.caption(f"Código: {code}")

            observation = _safe_text(plano, "observacao_resumida")
            if observation:
                st.write(observation)


def _render_portais(operator_id: str) -> None:
    portais = get_operadora_portais(operator_id)
    _section_intro(
        "Portais e acessos",
        "Canais digitais usados para elegibilidade, autorização e outras rotinas.",
    )

    if portais.empty:
        _render_empty_module("Nenhum portal foi encontrado.")
        return

    for _, portal in portais.iterrows():
        with st.container(border=True):
            name = _safe_text(portal, "nome") or "Portal sem nome"
            portal_type = _safe_text(portal, "tipo")
            url = _safe_text(portal, "url")

            st.markdown(f"**🌐 {name}**")
            if portal_type:
                st.caption(portal_type)

            requires_login = _safe_bool(portal.get("exige_login"), False)
            st.write(
                f"**Acesso autenticado:** {'Sim' if requires_login else 'Não'}"
            )

            instructions = _safe_text(portal, "instrucao_acesso")
            tip = _safe_text(portal, "dica_geral_acesso")
            observations = _safe_text(portal, "observacoes")

            if instructions:
                st.markdown("**Como acessar**")
                st.write(instructions)
            if tip:
                st.caption(f"💡 {tip}")
            if observations:
                st.caption(observations)
            if url:
                st.link_button("Abrir portal", url, use_container_width=True)


def _render_elegibilidade(operator_id: str) -> None:
    dataframe = get_operadora_elegibilidade(operator_id)
    _section_intro(
        "Elegibilidade",
        "Orientações para confirmar a situação do beneficiário antes do atendimento.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhuma regra de elegibilidade foi encontrada.")
        return

    for _, item in dataframe.iterrows():
        with st.container(border=True):
            necessary = _safe_bool(item.get("necessario"), True)
            st.markdown(
                f"**Verificação necessária:** {'Sim' if necessary else 'Não'}"
            )
            how_to = _safe_text(item, "orientacao")
            if how_to:
                st.write(how_to)
            observations = _safe_text(item, "observacoes")
            if observations:
                st.caption(observations)


def _render_documentos(operator_id: str) -> None:
    dataframe = get_operadora_documentos(operator_id)
    _section_intro(
        "Documentos",
        "Documentos e requisitos associados aos fluxos da operadora.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhum documento foi encontrado.")
        return

    for _, item in dataframe.iterrows():
        document = _safe_text(item, "nome") or "Documento sem identificação"

        with st.container(border=True):
            st.markdown(f"**📄 {document}**")
            c1, c2, c3 = st.columns(3)
            c1.caption(
                f"Obrigatório: {'Sim' if _safe_bool(item.get('obrigatorio')) else 'Não'}"
            )
            c2.caption(f"Formato: {_safe_text(item, 'formato') or '—'}")
            validity = _safe_text(item, "validade_dias")
            c3.caption(f"Validade: {validity + ' dias' if validity else '—'}")

            orientation = _safe_text(item, "orientacao")
            if orientation:
                st.write(orientation)

            file_url = _safe_text(item, "arquivo_url")
            if file_url:
                st.link_button("Abrir documento", file_url)


def _render_autorizacoes(operator_id: str) -> None:
    dataframe = get_operadora_autorizacoes(operator_id)
    _section_intro(
        "Autorizações",
        "Regras e orientações para solicitar autorização à operadora.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhuma regra de autorização foi encontrada.")
        return

    for _, item in dataframe.iterrows():
        with st.container(border=True):
            needs_auth = _safe_bool(item.get("necessita_autorizacao"), True)
            st.markdown(
                f"**Necessita autorização:** {'Sim' if needs_auth else 'Não'}"
            )

            c1, c2 = st.columns(2)
            c1.caption(
                f"Momento: {_safe_text(item, 'momento_autorizacao') or '—'}"
            )
            c2.caption(f"Prazo: {_safe_text(item, 'prazo') or '—'}")

            requester = _safe_text(item, "quem_solicita")
            method = _safe_text(item, "meio_solicitacao")
            if requester:
                st.write(f"**Quem solicita:** {requester}")
            if method:
                st.write(f"**Canal:** {method}")

            orientation = _safe_text(item, "orientacao")
            if orientation:
                st.write(orientation)

            observations = _safe_text(item, "observacoes")
            if observations:
                st.caption(observations)


def _render_coberturas(operator_id: str) -> None:
    dataframe = get_operadora_coberturas(operator_id)
    _section_intro(
        "Coberturas",
        "Informações operacionais de cobertura vinculadas à operadora e seus planos.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhuma cobertura foi encontrada.")
        return

    for _, item in dataframe.iterrows():
        covered_raw = item.get("coberto")
        if pd.isna(covered_raw):
            covered_label = "Não informado"
        else:
            covered_label = "Sim" if _safe_bool(covered_raw) else "Não"

        with st.container(border=True):
            st.markdown(f"**Coberto:** {covered_label}")
            c1, c2 = st.columns(2)
            c1.caption(f"Acomodação: {_safe_text(item, 'acomodacao') or '—'}")
            c2.caption(f"Acompanhante: {_safe_text(item, 'acompanhante') or '—'}")

            restriction = _safe_text(item, "restricoes_cobertura")
            if restriction:
                st.write(f"**Restrições:** {restriction}")

            observations = _safe_text(item, "observacoes")
            if observations:
                st.caption(observations)


def _render_contatos(operator_id: str) -> None:
    dataframe = get_operadora_contatos(operator_id)
    _section_intro(
        "Contatos",
        "Canais e responsáveis úteis para as rotinas com a operadora.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhum contato foi encontrado.")
        return

    for _, item in dataframe.iterrows():
        purpose = _safe_text(item, "finalidade") or "Contato geral"

        with st.container(border=True):
            st.markdown(f"**📞 {purpose}**")
            sector = _safe_text(item, "nome_setor")
            if sector:
                st.caption(sector)

            contact = _safe_text(item, "contato")
            contact_type = _safe_text(item, "tipo")
            if contact:
                st.write(f"**{contact_type or 'Contato'}:** {contact}")

            responsible = _safe_text(item, "responsavel")
            schedule = _safe_text(item, "horario_atendimento")
            if responsible:
                st.write(f"**Responsável:** {responsible}")
            if schedule:
                st.caption(f"Horário: {schedule}")

            observations = _safe_text(item, "observacoes")
            if observations:
                st.caption(observations)


def _render_consultores(operator_id: str) -> None:
    dataframe = get_operadora_consultores(operator_id)
    _section_intro(
        "Consultores",
        "Consultores de relacionamento vinculados à operadora.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhum consultor foi vinculado a esta operadora.")
        return

    for _, item in dataframe.iterrows():
        with st.container(border=True):
            st.markdown(f"**👤 {_safe_text(item, 'nome') or 'Consultor'}**")
            role = _safe_text(item, "cargo")
            if role:
                st.caption(role)

            email = _safe_text(item, "email")
            phone = _safe_text(item, "telefone")
            if email:
                st.write(f"**E-mail:** {email}")
            if phone:
                st.write(f"**Telefone:** {phone}")

            observations = _safe_text(item, "observacoes")
            if observations:
                st.caption(observations)


def _render_comunicados(operator_id: str) -> None:
    dataframe = get_operadora_comunicados(operator_id)
    _section_intro(
        "Comunicados",
        "Atualizações e orientações publicadas para esta operadora.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhum comunicado foi encontrado.")
        return

    visible = dataframe[
        dataframe.apply(
            lambda row: (
                _safe_text(row, "status").casefold()
                in {"publicado", "publicada", "ativo"}
                and _period_active(row)
            ),
            axis=1,
        )
    ]

    if visible.empty:
        _render_empty_module("Nenhum comunicado vigente foi encontrado.")
        return

    for _, item in visible.iterrows():
        title = _safe_text(item, "titulo") or "Comunicado"
        priority = _safe_text(item, "prioridade")

        with st.container(border=True):
            st.markdown(f"**📢 {title}**")
            if priority:
                st.caption(f"Prioridade: {priority}")

            summary = _safe_text(item, "resumo")
            content = _safe_text(item, "conteudo")
            if summary:
                st.write(summary)

            with st.expander("Ver comunicado completo", expanded=False):
                st.write(content or summary)
                audience = _safe_text(item, "publico_alvo")
                if audience:
                    st.caption(f"Público-alvo: {audience}")


def _render_contingencias(operator_id: str) -> None:
    dataframe = get_operadora_contingencias(operator_id)
    _section_intro(
        "Contingências",
        "Situações temporárias e alternativas operacionais vigentes.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhuma contingência foi encontrada.")
        return

    active = dataframe[dataframe.apply(_period_active, axis=1)]
    if active.empty:
        _render_empty_module("Nenhuma contingência vigente foi encontrada.")
        return

    for _, item in active.iterrows():
        title = _safe_text(item, "titulo") or "Contingência"
        priority = _safe_text(item, "prioridade")

        with st.container(border=True):
            st.markdown(f"**⚠️ {title}**")
            if priority:
                st.caption(f"Prioridade: {priority}")

            description = _safe_text(item, "descricao")
            if description:
                st.write(description)

            guidance = _safe_text(item, "orientacao_alternativa")
            if guidance:
                st.markdown("**Orientação alternativa**")
                st.write(guidance)

            alternative = _safe_text(item, "contato_alternativo")
            if alternative:
                st.write(f"**Contato alternativo:** {alternative}")


def _render_dicas(operator_id: str) -> None:
    dataframe = get_operadora_dicas(operator_id)
    _section_intro(
        "Dicas operacionais",
        "Atalhos e observações úteis para o dia a dia com a operadora.",
    )

    if dataframe.empty:
        _render_empty_module("Nenhuma dica operacional foi encontrada.")
        return

    if "destaque" in dataframe.columns:
        dataframe = dataframe.sort_values(
            by="destaque",
            ascending=False,
            na_position="last",
        )

    for _, item in dataframe.iterrows():
        with st.container(border=True):
            title = _safe_text(item, "titulo") or "Dica operacional"
            st.markdown(f"**💡 {title}**")
            category = _safe_text(item, "categoria")
            if category:
                st.caption(category)
            st.write(_safe_text(item, "dica"))


def render_operadora_detail(operator_id: str) -> None:
    operadora = get_operadora_by_id(operator_id)

    if operadora is None:
        st.error("Não foi possível localizar essa operadora.")
        if st.button("Voltar para operadoras"):
            st.session_state.pop("selected_operator_id", None)
            st.rerun()
        return

    top_left, top_right = st.columns([5, 1])

    with top_left:
        render_hero(
            eyebrow="Central da operadora",
            title=operadora.short_name,
            description=(
                "Tudo o que você precisa consultar sobre esta operadora "
                "em um único lugar."
            ),
        )

    with top_right:
        if st.button("← Voltar", use_container_width=True):
            st.session_state.pop("selected_operator_id", None)
            st.rerun()

    counts = get_operadora_counts(operator_id)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Planos", counts["planos"])
    m2.metric("Portais", counts["portais"])
    m3.metric("Comunicados", counts["comunicados"])
    m4.metric("Contingências", counts["contingencias"])

    st.markdown("### Central de informações")

    module_options = {
        "Visão geral": "🏠",
        "Planos": "📋",
        "Portais e acessos": "🌐",
        "Elegibilidade": "✅",
        "Autorizações": "🔑",
        "Coberturas": "🩺",
        "Documentos": "📄",
        "Contatos": "📞",
        "Consultores": "👤",
        "Comunicados": "📢",
        "Contingências": "⚠️",
        "Dicas": "💡",
    }

    selected_module = st.segmented_control(
        label="Selecione uma categoria",
        options=list(module_options),
        default="Visão geral",
        format_func=lambda option: f"{module_options[option]} {option}",
        key=f"operator_module_{operator_id}",
        selection_mode="single",
        width="stretch",
        label_visibility="collapsed",
    )

    st.divider()

    renderers = {
        "Visão geral": lambda: _render_overview(operator_id, operadora),
        "Planos": lambda: _render_planos(operator_id),
        "Portais e acessos": lambda: _render_portais(operator_id),
        "Elegibilidade": lambda: _render_elegibilidade(operator_id),
        "Autorizações": lambda: _render_autorizacoes(operator_id),
        "Coberturas": lambda: _render_coberturas(operator_id),
        "Documentos": lambda: _render_documentos(operator_id),
        "Contatos": lambda: _render_contatos(operator_id),
        "Consultores": lambda: _render_consultores(operator_id),
        "Comunicados": lambda: _render_comunicados(operator_id),
        "Contingências": lambda: _render_contingencias(operator_id),
        "Dicas": lambda: _render_dicas(operator_id),
    }

    renderers.get(selected_module or "Visão geral", renderers["Visão geral"])()


def render_operadoras() -> None:
    selected_operator_id = st.session_state.get("selected_operator_id")

    if selected_operator_id:
        render_operadora_detail(selected_operator_id)
        return

    render_hero(
        eyebrow="Convênios e planos",
        title="Operadoras",
        description=(
            "Escolha uma operadora para acessar sua central completa de informações."
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

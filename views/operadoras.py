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


def _set_operator_module(operator_id: str, module: str) -> None:
    st.session_state[f"operator_module_{operator_id}"] = module


def _inject_hub_styles() -> None:
    st.markdown(
        """
        <style>
        .hmv-operator-header {
            background: linear-gradient(135deg, #005691 0%, #0077a8 100%);
            border-radius: 18px;
            padding: 26px 28px;
            margin: 4px 0 18px 0;
            color: white;
            box-shadow: 0 8px 24px rgba(0, 86, 145, .14);
        }
        .hmv-operator-kicker {
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .10em;
            text-transform: uppercase;
            opacity: .86;
            margin-bottom: 7px;
        }
        .hmv-operator-title {
            font-size: 2rem;
            line-height: 1.08;
            font-weight: 750;
            margin: 0 0 8px 0;
        }
        .hmv-operator-meta {
            font-size: .94rem;
            opacity: .94;
        }
        .hmv-stat {
            background: #ffffff;
            border: 1px solid #dfe7ed;
            border-radius: 14px;
            padding: 15px 16px;
            min-height: 88px;
            box-shadow: 0 2px 8px rgba(22, 46, 68, .04);
        }
        .hmv-stat-label {
            color: #5d6b78;
            font-size: .79rem;
            font-weight: 650;
            margin-bottom: 5px;
        }
        .hmv-stat-value {
            color: #0d2638;
            font-size: 1.55rem;
            font-weight: 760;
            line-height: 1;
        }
        .hmv-section-label {
            color: #0d2638;
            font-size: 1.18rem;
            font-weight: 750;
            margin: 22px 0 3px 0;
        }
        .hmv-section-help {
            color: #697987;
            font-size: .88rem;
            margin-bottom: 12px;
        }
        .hmv-alert-danger, .hmv-alert-info, .hmv-panel {
            border-radius: 14px;
            padding: 17px 18px;
            min-height: 132px;
        }
        .hmv-alert-danger {
            background: #fff4f2;
            border: 1px solid #f0b5aa;
        }
        .hmv-alert-info {
            background: #eef7fc;
            border: 1px solid #b7d9ec;
        }
        .hmv-panel {
            background: #ffffff;
            border: 1px solid #dfe7ed;
        }
        .hmv-card-eyebrow {
            color: #5c6b77;
            font-size: .75rem;
            font-weight: 750;
            letter-spacing: .06em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .hmv-card-title {
            color: #102b3d;
            font-size: 1rem;
            font-weight: 750;
            margin-bottom: 7px;
        }
        .hmv-card-body {
            color: #425463;
            font-size: .89rem;
            line-height: 1.45;
        }
        div[data-testid="stButton"] > button {
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _html_escape(value: object) -> str:
    import html
    return html.escape(str(value or ""))


def _render_stat_card(label: str, value: object) -> None:
    st.markdown(
        f"""
        <div class="hmv-stat">
            <div class="hmv-stat-label">{_html_escape(label)}</div>
            <div class="hmv-stat-value">{_html_escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview(operator_id: str, operadora) -> None:
    counts = get_operadora_counts(operator_id)
    portais = get_operadora_portais(operator_id)
    elegibilidade = get_operadora_elegibilidade(operator_id)
    autorizacoes = get_operadora_autorizacoes(operator_id)
    coberturas = get_operadora_coberturas(operator_id)
    documentos = get_operadora_documentos(operator_id)
    contatos = get_operadora_contatos(operator_id)
    consultores = get_operadora_consultores(operator_id)
    dicas = get_operadora_dicas(operator_id)
    contingencias = get_operadora_contingencias(operator_id)
    comunicados = get_operadora_comunicados(operator_id)

    active_contingencies = (
        contingencias[contingencias.apply(_period_active, axis=1)].copy()
        if not contingencias.empty
        else contingencias
    )
    active_notices = (
        comunicados[
            comunicados.apply(
                lambda row: (
                    _safe_text(row, "status").casefold()
                    in {"publicado", "publicada", "ativo"}
                    and _period_active(row)
                ),
                axis=1,
            )
        ].copy()
        if not comunicados.empty
        else comunicados
    )

    st.markdown(
        '<div class="hmv-section-label">Resumo da operadora</div>'
        '<div class="hmv-section-help">As informações mais consultadas, sem precisar procurar em cada módulo.</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        _render_stat_card("Planos ativos", counts["planos"])
    with s2:
        _render_stat_card("Portais", counts["portais"])
    with s3:
        _render_stat_card("Contatos", counts["contatos"])
    with s4:
        _render_stat_card("Documentos", counts["documentos"])

    if not active_contingencies.empty or not active_notices.empty:
        st.markdown(
            '<div class="hmv-section-label">Informações importantes agora</div>'
            '<div class="hmv-section-help">Alertas vigentes que podem mudar a rotina de atendimento.</div>',
            unsafe_allow_html=True,
        )

        alert_columns = st.columns(2)

        with alert_columns[0]:
            if not active_contingencies.empty:
                item = active_contingencies.iloc[0]
                title = _safe_text(item, "titulo") or "Contingência ativa"
                description = _safe_text(item, "descricao") or _safe_text(
                    item, "orientacao_alternativa"
                )
                priority = _safe_text(item, "prioridade") or "Prioridade não informada"
                st.markdown(
                    f"""
                    <div class="hmv-alert-danger">
                        <div class="hmv-card-eyebrow">⚠ Contingência • {_html_escape(priority)}</div>
                        <div class="hmv-card-title">{_html_escape(title)}</div>
                        <div class="hmv-card-body">{_html_escape(description)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Ver orientação de contingência",
                    key=f"overview_contingency_{operator_id}",
                    use_container_width=True,
                ):
                    _set_operator_module(operator_id, "Contingências")
                    st.rerun()
            else:
                st.markdown(
                    """
                    <div class="hmv-panel">
                        <div class="hmv-card-eyebrow">✓ Operação</div>
                        <div class="hmv-card-title">Sem contingências vigentes</div>
                        <div class="hmv-card-body">Nenhuma contingência ativa foi cadastrada para esta operadora.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with alert_columns[1]:
            if not active_notices.empty:
                item = active_notices.iloc[0]
                title = _safe_text(item, "titulo") or "Comunicado"
                summary = _safe_text(item, "resumo") or _safe_text(item, "conteudo")
                priority = _safe_text(item, "prioridade") or "Normal"
                st.markdown(
                    f"""
                    <div class="hmv-alert-info">
                        <div class="hmv-card-eyebrow">📢 Comunicado • {_html_escape(priority)}</div>
                        <div class="hmv-card-title">{_html_escape(title)}</div>
                        <div class="hmv-card-body">{_html_escape(summary)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Ler comunicado",
                    key=f"overview_notice_{operator_id}",
                    use_container_width=True,
                ):
                    _set_operator_module(operator_id, "Comunicados")
                    st.rerun()
            else:
                st.markdown(
                    """
                    <div class="hmv-panel">
                        <div class="hmv-card-eyebrow">📢 Comunicados</div>
                        <div class="hmv-card-title">Nenhum comunicado vigente</div>
                        <div class="hmv-card-body">Não há atualizações publicadas para esta operadora neste momento.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        '<div class="hmv-section-label">Acessos rápidos</div>'
        '<div class="hmv-section-help">Entre direto na informação que normalmente é necessária durante o atendimento.</div>',
        unsafe_allow_html=True,
    )

    quick = [
        ("🌐", "Portais", "Portais e acessos", len(portais)),
        ("🔑", "Autorizações", "Autorizações", len(autorizacoes)),
        ("✅", "Elegibilidade", "Elegibilidade", len(elegibilidade)),
        ("🩺", "Coberturas", "Coberturas", len(coberturas)),
        ("📄", "Documentos", "Documentos", len(documentos)),
        ("📞", "Contatos", "Contatos", len(contatos)),
    ]
    quick_cols = st.columns(3)
    for index, (icon, label, module, amount) in enumerate(quick):
        with quick_cols[index % 3]:
            if st.button(
                f"{icon}  {label}  ·  {amount}",
                key=f"quick_{operator_id}_{module}",
                use_container_width=True,
            ):
                _set_operator_module(operator_id, module)
                st.rerun()

    st.markdown(
        '<div class="hmv-section-label">Portais e acessos</div>'
        '<div class="hmv-section-help">O acesso operacional principal já fica visível na página inicial da operadora.</div>',
        unsafe_allow_html=True,
    )

    if portais.empty:
        st.info("Nenhum portal operacional cadastrado.")
    else:
        for _, portal in portais.head(2).iterrows():
            name = _safe_text(portal, "nome") or "Portal sem nome"
            portal_type = _safe_text(portal, "tipo") or "Portal operacional"
            url = _safe_text(portal, "url")
            instructions = _safe_text(portal, "instrucao_acesso")
            requires_login = _safe_bool(portal.get("exige_login"), False)

            with st.container(border=True):
                left, right = st.columns([4, 1.4])
                with left:
                    st.markdown(f"**🌐 {name}**")
                    st.caption(portal_type)
                    st.write(
                        f"**Login necessário:** {'Sim' if requires_login else 'Não'}"
                    )
                    if instructions:
                        st.write(instructions)
                with right:
                    if url:
                        st.link_button(
                            "Abrir portal ↗",
                            url,
                            use_container_width=True,
                        )
                    if st.button(
                        "Ver detalhes",
                        key=f"portal_detail_{operator_id}_{portal.get('id', name)}",
                        use_container_width=True,
                    ):
                        _set_operator_module(operator_id, "Portais e acessos")
                        st.rerun()

    st.markdown(
        '<div class="hmv-section-label">Orientações operacionais</div>'
        '<div class="hmv-section-help">Resumo das regras que mais impactam o fluxo de atendimento.</div>',
        unsafe_allow_html=True,
    )

    orientation_cols = st.columns(3)
    orientation_specs = [
        (
            "Elegibilidade",
            "✅",
            elegibilidade,
            "orientacao",
            "Nenhuma orientação cadastrada.",
        ),
        (
            "Autorizações",
            "🔑",
            autorizacoes,
            "orientacao",
            "Nenhuma orientação cadastrada.",
        ),
        (
            "Coberturas",
            "🩺",
            coberturas,
            "restricoes_cobertura",
            "Nenhuma restrição cadastrada.",
        ),
    ]

    for col, (label, icon, dataframe, field, empty_text) in zip(
        orientation_cols, orientation_specs
    ):
        with col:
            body = empty_text
            if not dataframe.empty:
                body = _safe_text(dataframe.iloc[0], field) or empty_text
            st.markdown(
                f"""
                <div class="hmv-panel">
                    <div class="hmv-card-eyebrow">{icon} {label}</div>
                    <div class="hmv-card-body">{_html_escape(body)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Ver {label.lower()}",
                key=f"orientation_{operator_id}_{label}",
                use_container_width=True,
            ):
                _set_operator_module(operator_id, label)
                st.rerun()

    st.markdown(
        '<div class="hmv-section-label">Relacionamento e apoio</div>'
        '<div class="hmv-section-help">Pessoas e dicas que ajudam a resolver situações fora do fluxo padrão.</div>',
        unsafe_allow_html=True,
    )

    support_cols = st.columns(2)
    with support_cols[0]:
        if not consultores.empty:
            consultant = consultores.iloc[0]
            st.markdown(
                f"""
                <div class="hmv-panel">
                    <div class="hmv-card-eyebrow">👤 Consultor de relacionamento</div>
                    <div class="hmv-card-title">{_html_escape(_safe_text(consultant, "nome"))}</div>
                    <div class="hmv-card-body">{_html_escape(_safe_text(consultant, "cargo"))}<br>
                    {_html_escape(_safe_text(consultant, "email"))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Ver consultores",
                key=f"support_consultants_{operator_id}",
                use_container_width=True,
            ):
                _set_operator_module(operator_id, "Consultores")
                st.rerun()
        else:
            st.info("Nenhum consultor vinculado.")

    with support_cols[1]:
        if not dicas.empty:
            tip = dicas.iloc[0]
            st.markdown(
                f"""
                <div class="hmv-panel">
                    <div class="hmv-card-eyebrow">💡 Dica operacional</div>
                    <div class="hmv-card-title">{_html_escape(_safe_text(tip, "titulo"))}</div>
                    <div class="hmv-card-body">{_html_escape(_safe_text(tip, "dica"))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Ver todas as dicas",
                key=f"support_tips_{operator_id}",
                use_container_width=True,
            ):
                _set_operator_module(operator_id, "Dicas")
                st.rerun()
        else:
            st.info("Nenhuma dica operacional cadastrada.")

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

    _inject_hub_styles()

    back_col, spacer = st.columns([1.2, 5])
    with back_col:
        if st.button("← Operadoras", use_container_width=True):
            st.session_state.pop("selected_operator_id", None)
            st.rerun()

    status = operadora.status or "Não informado"
    plan_label = (
        f"{operadora.plans_count} plano"
        if operadora.plans_count == 1
        else f"{operadora.plans_count} planos"
    )
    consultant_meta = (
        f" • Consultor: {_html_escape(operadora.consultant)}"
        if operadora.consultant
        else ""
    )

    st.markdown(
        f"""
        <div class="hmv-operator-header">
            <div class="hmv-operator-kicker">Central da operadora</div>
            <div class="hmv-operator-title">{_html_escape(operadora.short_name)}</div>
            <div class="hmv-operator-meta">
                {_html_escape(status)} • {_html_escape(plan_label)}{consultant_meta}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if operadora.site_url:
        site_col, _ = st.columns([1.5, 4.5])
        with site_col:
            st.link_button(
                "Abrir site da operadora ↗",
                operadora.site_url,
                use_container_width=True,
            )

    module_options = [
        "Visão geral",
        "Planos",
        "Portais e acessos",
        "Elegibilidade",
        "Autorizações",
        "Coberturas",
        "Documentos",
        "Contatos",
        "Consultores",
        "Comunicados",
        "Contingências",
        "Dicas",
    ]

    state_key = f"operator_module_{operator_id}"
    if st.session_state.get(state_key) not in module_options:
        st.session_state[state_key] = "Visão geral"

    selected_module = st.selectbox(
        "Consultar outra informação",
        module_options,
        key=state_key,
        help="Use este seletor para aprofundar uma categoria. A Visão geral concentra os atalhos principais.",
    )

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

    renderers[selected_module]()

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

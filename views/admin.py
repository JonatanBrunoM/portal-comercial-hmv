from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from config.settings import DATASETS
from core.auth_service import get_current_profile
from core.data_service import clear_data_cache, read_dataset
from core.supabase_repository import (
    check_supabase_connection,
    fetch_table,
)


ADMIN_DATASETS = [
    "operadoras", "planos", "portais", "elegibilidade", "documentos",
    "autorizacoes", "coberturas", "contatos", "contingencias",
    "dicas_operacionais", "consultores", "carteiras", "comunicados",
    "locais_atendimento", "tipos_atendimento", "plano_locais",
]


def _is_admin() -> bool:
    profile = get_current_profile()
    return bool(profile and profile.get("status") == "Ativo" and profile.get("role") == "admin")


def _render_overview() -> None:
    st.markdown("## Visão geral da base")
    cols = st.columns(4)
    counts: list[tuple[str, int]] = []
    for key in ADMIN_DATASETS:
        try:
            counts.append((key, len(read_dataset(key))))
        except Exception:
            counts.append((key, -1))

    for index, (key, count) in enumerate(counts):
        label = key.replace("_", " ").title()
        value = count if count >= 0 else "Erro"
        cols[index % 4].metric(label, value)


def _render_dataset_browser() -> None:
    st.markdown("## Dados no Supabase")
    selected = st.selectbox(
        "Conjunto de dados",
        options=ADMIN_DATASETS,
        format_func=lambda item: item.replace("_", " ").title(),
    )

    try:
        dataframe = read_dataset(selected)
    except Exception as error:
        st.error(f"Não foi possível carregar '{selected}': {error}")
        return

    st.caption(f"Tabela: `{DATASETS[selected]}` · {len(dataframe)} registro(s)")
    if dataframe.empty:
        st.info("Este conjunto ainda não possui registros.")
        return

    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def _render_users() -> None:
    st.markdown("## Usuários")
    try:
        dataframe = fetch_table(
            "profiles",
            order_by="nome",
        )

        visible_columns = [
            "id",
            "nome",
            "email",
            "role",
            "status",
            "primeiro_acesso_em",
            "ultimo_acesso_em",
            "ultimo_login_em",
        ]

        dataframe = dataframe[
            [
                column
                for column in visible_columns
                if column in dataframe.columns
            ]
        ]
    except Exception as error:
        st.error(f"Não foi possível carregar os usuários: {error}")
        return

    if dataframe.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    st.dataframe(dataframe, use_container_width=True, hide_index=True)
    st.caption("A alteração de perfis e permissões será tratada no próximo módulo administrativo.")


def render_admin() -> None:
    if not _is_admin():
        st.error("Esta área é restrita aos administradores do Portal Comercial.")
        return

    render_hero(
        eyebrow="Gestão do Portal",
        title="Administração",
        description="Acompanhe a base Supabase, os módulos do portal e os usuários autorizados.",
    )

    connected, connection_message = check_supabase_connection()

    if connected:
        st.success("Supabase conectado e operacional.", icon="✅")
    else:
        st.error(connection_message, icon="❌")
        return

    if st.button("Atualizar dados agora", use_container_width=False):
        clear_data_cache()
        st.success("Cache atualizado.")
        st.rerun()

    tab_overview, tab_data, tab_users = st.tabs([
        "📊 Visão geral", "🗃️ Dados", "👥 Usuários"
    ])

    with tab_overview:
        _render_overview()
    with tab_data:
        _render_dataset_browser()
    with tab_users:
        _render_users()

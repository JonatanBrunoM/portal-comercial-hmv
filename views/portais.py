from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from components.portal_cards import render_portal_card
from core.data_service import get_operadoras, get_planos, get_portais


def _safe(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    return "" if pd.isna(value) else str(value).strip()


def _maps():
    operadoras = get_operadoras()
    planos = get_planos()

    operator_names = {
        str(row["id"]): (row.get("nome_curto") or row.get("nome") or "")
        for _, row in operadoras.iterrows()
    }
    plan_names = {
        str(row["id"]): (row.get("nome_padronizado") or row.get("nome") or "")
        for _, row in planos.iterrows()
    }

    return operator_names, plan_names


def render_portais() -> None:
    render_hero(
        eyebrow="Acessos operacionais",
        title="Portais e Credenciais",
        description=(
            "Consulte os portais das operadoras, orientações de acesso "
            "e credenciais institucionais disponíveis."
        ),
    )

    try:
        dataframe = get_portais()
        operator_names, plan_names = _maps()
    except Exception:
        st.error("Não foi possível carregar os portais neste momento.")
        return

    if dataframe.empty:
        st.info("Nenhum portal cadastrado até o momento.")
        return

    query = st.text_input(
        "Pesquisar portal",
        placeholder="Operadora, portal ou finalidade...",
    )

    if query.strip():
        term = query.casefold()
        mask = dataframe.apply(
            lambda row: term
            in " ".join(
                [
                    _safe(row, "nome"),
                    _safe(row, "tipo"),
                    operator_names.get(_safe(row, "operadora_id"), ""),
                    plan_names.get(_safe(row, "plano_id"), ""),
                ]
            ).casefold(),
            axis=1,
        )
        dataframe = dataframe[mask]

    st.caption(f"{len(dataframe)} portal(is) encontrado(s).")

    for _, portal in dataframe.iterrows():
        operator_name = operator_names.get(
            _safe(portal, "operadora_id"),
            "Operadora não identificada",
        )
        plan_name = plan_names.get(_safe(portal, "plano_id"), "")

        render_portal_card(
            portal,
            operator_name=operator_name,
            plan_name=plan_name,
            show_credentials=True,
            key_prefix="portals_page",
        )

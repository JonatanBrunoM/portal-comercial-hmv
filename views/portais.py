from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import get_operadoras, get_planos, get_portais


def _safe(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    return "" if pd.isna(value) else str(value).strip()


def _maps():
    ops, plans = get_operadoras(), get_planos()
    op_names = {str(r["id"]): (r.get("nome_curto") or r.get("nome") or "") for _, r in ops.iterrows()}
    plan_names = {str(r["id"]): (r.get("nome_padronizado") or r.get("nome") or "") for _, r in plans.iterrows()}
    return op_names, plan_names


def render_portais() -> None:
    render_hero(eyebrow="Acessos operacionais", title="Portais", description="Consulte os portais das operadoras, finalidades, links e orientações de acesso.")
    try:
        df = get_portais(); op_names, plan_names = _maps()
    except Exception:
        st.error("Não foi possível carregar os portais neste momento."); return
    if df.empty:
        st.info("Nenhum portal cadastrado até o momento."); return
    query = st.text_input("Pesquisar portal", placeholder="Operadora, portal ou finalidade...")
    if query.strip():
        term=query.casefold()
        mask=df.apply(lambda r: term in " ".join([_safe(r,"nome"), _safe(r,"tipo"), op_names.get(_safe(r,"operadora_id"),""), plan_names.get(_safe(r,"plano_id"),"")]).casefold(), axis=1)
        df=df[mask]
    st.caption(f"{len(df)} portal(is) encontrado(s).")
    for _, row in df.iterrows():
        with st.container(border=True):
            st.markdown(f"### 🌐 {_safe(row,'nome') or 'Portal sem nome'}")
            op=op_names.get(_safe(row,"operadora_id"), "Operadora não identificada")
            plan=plan_names.get(_safe(row,"plano_id"), "")
            st.caption(" • ".join(v for v in [op, plan, _safe(row,"tipo")] if v))
            if _safe(row,"instrucao_acesso"): st.write(_safe(row,"instrucao_acesso"))
            if _safe(row,"dica_geral_acesso"): st.info(_safe(row,"dica_geral_acesso"), icon="💡")
            if _safe(row,"observacoes"): st.caption(_safe(row,"observacoes"))
            url=_safe(row,"url")
            if url: st.link_button("Abrir portal", url, use_container_width=False)
            if str(row.get("exige_login", False)).lower() in {"true","1"}: st.caption("🔐 Este portal exige autenticação.")

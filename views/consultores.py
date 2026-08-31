from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import get_carteiras, get_consultores, get_operadoras, get_planos


def _safe(row,col):
    value=row.get(col,""); return "" if pd.isna(value) else str(value).strip()


def render_consultores() -> None:
    render_hero(eyebrow="Relacionamento comercial", title="Consultores", description="Consulte os consultores e as carteiras de operadoras e planos sob sua responsabilidade.")
    try: consultants=get_consultores(); wallets=get_carteiras(); ops=get_operadoras(); plans=get_planos()
    except Exception: st.error("Não foi possível carregar os consultores neste momento."); return
    if consultants.empty: st.info("Nenhum consultor cadastrado até o momento."); return
    op_names={str(r['id']): (r.get('nome_curto') or r.get('nome') or '') for _,r in ops.iterrows()}; plan_names={str(r['id']): (r.get('nome_padronizado') or r.get('nome') or '') for _,r in plans.iterrows()}
    query=st.text_input("Pesquisar consultor", placeholder="Nome, cargo, operadora ou e-mail...")
    for _,row in consultants.iterrows():
        cid=_safe(row,'id'); linked=wallets[wallets.get('consultor_id',pd.Series(dtype=str)).fillna('').astype(str).eq(cid)] if not wallets.empty and 'consultor_id' in wallets else pd.DataFrame()
        operators=" • ".join(dict.fromkeys(op_names.get(_safe(r,'operadora_id'),'') for _,r in linked.iterrows() if op_names.get(_safe(r,'operadora_id'),'')))
        plans_txt=" • ".join(dict.fromkeys(plan_names.get(_safe(r,'plano_id'),'') for _,r in linked.iterrows() if plan_names.get(_safe(r,'plano_id'),'')))
        hay=" ".join([_safe(row,'nome'),_safe(row,'cargo'),_safe(row,'email'),operators,plans_txt]).casefold()
        if query.strip() and query.casefold() not in hay: continue
        with st.container(border=True):
            st.markdown(f"### 👤 {_safe(row,'nome') or 'Consultor sem nome'}")
            st.caption(_safe(row,'cargo') or 'Cargo não informado')
            c1,c2=st.columns(2); c1.write(f"**E-mail:** {_safe(row,'email') or 'Não informado'}"); c2.write(f"**Telefone:** {_safe(row,'telefone') or 'Não informado'}")
            if operators: st.write(f"**Operadoras:** {operators}")
            if plans_txt: st.write(f"**Planos:** {plans_txt}")
            if _safe(row,'observacoes'): st.caption(_safe(row,'observacoes'))

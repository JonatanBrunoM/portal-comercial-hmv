from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import get_documentos, get_operadoras, get_planos


def _safe(row, col):
    value=row.get(col,""); return "" if pd.isna(value) else str(value).strip()


def render_documentos() -> None:
    render_hero(eyebrow="Orientações e arquivos", title="Documentos", description="Consulte documentos exigidos, formatos, validade e orientações por operadora e plano.")
    try: df=get_documentos(); ops=get_operadoras(); plans=get_planos()
    except Exception: st.error("Não foi possível carregar os documentos neste momento."); return
    if df.empty: st.info("Nenhum documento cadastrado até o momento."); return
    op_names={str(r['id']): (r.get('nome_curto') or r.get('nome') or '') for _,r in ops.iterrows()}
    plan_names={str(r['id']): (r.get('nome_padronizado') or r.get('nome') or '') for _,r in plans.iterrows()}
    query=st.text_input("Pesquisar documento", placeholder="Nome, operadora, plano ou orientação...")
    if query.strip():
        term=query.casefold(); df=df[df.apply(lambda r: term in " ".join([_safe(r,'nome'),_safe(r,'orientacao'),_safe(r,'observacoes'),op_names.get(_safe(r,'operadora_id'),''),plan_names.get(_safe(r,'plano_id'),'')]).casefold(),axis=1)]
    for _,row in df.iterrows():
        with st.container(border=True):
            st.markdown(f"### 📄 {_safe(row,'nome') or 'Documento sem nome'}")
            st.caption(" • ".join(v for v in [op_names.get(_safe(row,'operadora_id'),''), plan_names.get(_safe(row,'plano_id'),''), _safe(row,'formato')] if v))
            c1,c2=st.columns(2); c1.write(f"**Obrigatório:** {'Sim' if bool(row.get('obrigatorio',False)) else 'Não'}"); c2.write(f"**Validade:** {_safe(row,'validade_dias') + ' dias' if _safe(row,'validade_dias') else 'Não informada'}")
            if _safe(row,'orientacao'): st.write(_safe(row,'orientacao'))
            if _safe(row,'observacoes'): st.caption(_safe(row,'observacoes'))
            if _safe(row,'arquivo_url'): st.link_button("Abrir documento", _safe(row,'arquivo_url'))

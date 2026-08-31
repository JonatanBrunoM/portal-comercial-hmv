from __future__ import annotations

from datetime import datetime
import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import get_comunicados, get_operadoras


def _safe(row,col):
    value=row.get(col,""); return "" if pd.isna(value) else str(value).strip()

def _date(value):
    if value is None or pd.isna(value): return ""
    parsed=pd.to_datetime(value,errors='coerce'); return "" if pd.isna(parsed) else parsed.strftime('%d/%m/%Y')


def render_comunicados() -> None:
    render_hero(eyebrow="Atualizações do Portal", title="Comunicados", description="Acompanhe orientações, mudanças e avisos relevantes das operadoras.")
    try: df=get_comunicados(); ops=get_operadoras()
    except Exception: st.error("Não foi possível carregar os comunicados neste momento."); return
    if df.empty: st.info("Nenhum comunicado cadastrado até o momento."); return
    names={str(r['id']): (r.get('nome_curto') or r.get('nome') or '') for _,r in ops.iterrows()}
    query=st.text_input("Pesquisar comunicado", placeholder="Título, operadora, categoria ou conteúdo...")
    if query.strip():
        term=query.casefold(); df=df[df.apply(lambda r: term in " ".join([_safe(r,'titulo'),_safe(r,'resumo'),_safe(r,'conteudo'),_safe(r,'categoria'),names.get(_safe(r,'operadora_id'),'')]).casefold(),axis=1)]
    if 'inicio_em' in df.columns: df=df.sort_values('inicio_em',ascending=False,na_position='last')
    for _,row in df.iterrows():
        with st.container(border=True):
            st.markdown(f"### 📢 {_safe(row,'titulo') or 'Comunicado sem título'}")
            meta=[names.get(_safe(row,'operadora_id'),'Geral'),_safe(row,'categoria'),_safe(row,'prioridade'),_date(row.get('inicio_em'))]
            st.caption(" • ".join(v for v in meta if v))
            if _safe(row,'resumo'): st.write(_safe(row,'resumo'))
            with st.expander("Ver comunicado completo"):
                st.write(_safe(row,'conteudo') or 'Conteúdo não informado.')
                if _safe(row,'publico_alvo'): st.caption(f"Público-alvo: {_safe(row,'publico_alvo')}")
                if _safe(row,'responsavel'): st.caption(f"Responsável: {_safe(row,'responsavel')}")

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import get_contingencias, get_operadoras, get_planos


def _safe(row,col):
    value=row.get(col,""); return "" if pd.isna(value) else str(value).strip()

def _date(value):
    if value is None or pd.isna(value): return ""
    parsed=pd.to_datetime(value,errors='coerce'); return "" if pd.isna(parsed) else parsed.strftime('%d/%m/%Y')


def render_contingencias() -> None:
    render_hero(eyebrow="Continuidade operacional", title="Contingências", description="Consulte indisponibilidades e orientações alternativas para manter o atendimento.")
    try: df=get_contingencias(); ops=get_operadoras(); plans=get_planos()
    except Exception: st.error("Não foi possível carregar as contingências neste momento."); return
    if df.empty: st.info("Nenhuma contingência cadastrada no momento."); return
    op_names={str(r['id']): (r.get('nome_curto') or r.get('nome') or '') for _,r in ops.iterrows()}; plan_names={str(r['id']): (r.get('nome_padronizado') or r.get('nome') or '') for _,r in plans.iterrows()}
    query=st.text_input("Pesquisar contingência", placeholder="Operadora, evento ou orientação...")
    if query.strip():
        term=query.casefold(); df=df[df.apply(lambda r: term in " ".join([_safe(r,'titulo'),_safe(r,'descricao'),_safe(r,'orientacao_alternativa'),op_names.get(_safe(r,'operadora_id'),'')]).casefold(),axis=1)]
    if 'inicio_em' in df.columns: df=df.sort_values('inicio_em',ascending=False,na_position='last')
    for _,row in df.iterrows():
        priority=_safe(row,'prioridade') or 'Não informada'
        with st.container(border=True):
            st.markdown(f"### ⚠️ {_safe(row,'titulo') or 'Contingência sem título'}")
            st.caption(" • ".join(v for v in [op_names.get(_safe(row,'operadora_id'),'Geral'),plan_names.get(_safe(row,'plano_id'),''),f"Prioridade {priority}",_date(row.get('inicio_em'))] if v))
            if _safe(row,'descricao'): st.write(_safe(row,'descricao'))
            st.info(_safe(row,'orientacao_alternativa') or 'Orientação alternativa não informada.', icon='🧭')
            if _safe(row,'contato_alternativo'): st.write(f"**Contato alternativo:** {_safe(row,'contato_alternativo')}")
            if _safe(row,'fim_em'): st.caption(f"Previsão/fim: {_date(row.get('fim_em'))}")

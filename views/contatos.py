from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hero import render_hero
from core.data_service import get_contatos, get_operadoras, get_planos


def _safe(row,col):
    value=row.get(col,""); return "" if pd.isna(value) else str(value).strip()


def render_contatos() -> None:
    render_hero(eyebrow="Relacionamento", title="Contatos", description="Encontre rapidamente telefones, e-mails, setores e responsáveis das operadoras.")
    try: df=get_contatos(); ops=get_operadoras(); plans=get_planos()
    except Exception: st.error("Não foi possível carregar os contatos neste momento."); return
    if df.empty: st.info("Nenhum contato cadastrado até o momento."); return
    op_names={str(r['id']): (r.get('nome_curto') or r.get('nome') or '') for _,r in ops.iterrows()}
    plan_names={str(r['id']): (r.get('nome_padronizado') or r.get('nome') or '') for _,r in plans.iterrows()}
    query=st.text_input("Pesquisar contato", placeholder="Operadora, finalidade, setor, telefone ou e-mail...")
    if query.strip():
        term=query.casefold(); df=df[df.apply(lambda r: term in " ".join([_safe(r,'nome_setor'),_safe(r,'finalidade'),_safe(r,'tipo'),_safe(r,'contato'),_safe(r,'responsavel'),op_names.get(_safe(r,'operadora_id'),'')]).casefold(),axis=1)]
    for _,row in df.iterrows():
        with st.container(border=True):
            title=_safe(row,'nome_setor') or _safe(row,'finalidade') or 'Contato'
            st.markdown(f"### 📞 {title}")
            st.caption(" • ".join(v for v in [op_names.get(_safe(row,'operadora_id'),''),plan_names.get(_safe(row,'plano_id'),''),_safe(row,'finalidade')] if v))
            st.write(f"**{_safe(row,'tipo') or 'Contato'}:** {_safe(row,'contato')}")
            if _safe(row,'responsavel'): st.write(f"**Responsável:** {_safe(row,'responsavel')}")
            if _safe(row,'horario_atendimento'): st.write(f"**Horário:** {_safe(row,'horario_atendimento')}")
            if _safe(row,'observacoes'): st.caption(_safe(row,'observacoes'))

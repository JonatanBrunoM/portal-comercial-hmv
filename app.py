import streamlit as st

from components.hero import render_hero
from components.sidebar import render_sidebar
from config.constants import APP_CONFIG
from config.theme import apply_theme
from views.home import render_home
from views.pesquisa import render_pesquisa
from views.operadoras import render_operadoras
from views.portais import render_portais
from views.documentos import render_documentos
from views.contatos import render_contatos
from views.contingencias import render_contingencias
from views.comunicados import render_comunicados
from views.consultores import render_consultores
from views.forum import render_forum
from views.assistente import render_assistente
from views.particular import render_particular
from views.admin import render_admin

st.set_page_config(
    page_title=APP_CONFIG.APP_NAME,
    page_icon=APP_CONFIG.PAGE_ICON,
    layout=APP_CONFIG.LAYOUT,
    initial_sidebar_state="expanded",
)

apply_theme()


if "current_page" not in st.session_state:
    st.session_state.current_page = APP_CONFIG.DEFAULT_PAGE


def render_placeholder_page(
    title: str,
    description: str,
) -> None:
    """Renderiza temporariamente páginas ainda não implementadas."""

    render_hero(
        eyebrow=APP_CONFIG.ORGANIZATION_NAME,
        title=title,
        description=description,
    )

    st.info(
        "A estrutura desta página está pronta e será "
        "implementada nos próximos módulos."
    )


selected_page = render_sidebar()


PAGE_RENDERERS = {
    "Início": render_home,
    "Pesquisa": render_pesquisa,
    "Operadoras": render_operadoras,
    "Portais": render_portais,
    "Documentos": render_documentos,
    "Contatos": render_contatos,
    "Contingências": render_contingencias,
    "Comunicados": render_comunicados,
    "Consultores": render_consultores,
    "Particular": render_particular,
    "Fórum": render_forum,
    "Assistente": render_assistente,
    "Administração": render_admin,
}


page_renderer = PAGE_RENDERERS.get(
    selected_page,
    PAGE_RENDERERS["Início"],
)

page_renderer()

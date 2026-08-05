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

    "Contatos": lambda: render_placeholder_page(
        "Contatos",
        "Encontre centrais, telefones e e-mails.",
    ),

    "Consultores": lambda: render_placeholder_page(
        "Consultores",
        "Consulte os responsáveis por cada carteira.",
    ),

    "Comunicados": lambda: render_placeholder_page(
        "Comunicados",
        "Acompanhe atualizações importantes.",
    ),

    "Contingências": lambda: render_placeholder_page(
        "Contingências",
        "Consulte fluxos alternativos e alertas ativos.",
    ),

    "Fórum": lambda: render_placeholder_page(
        "Fórum",
        "Compartilhe informações com outros colaboradores.",
    ),

    "Assistente": lambda: render_placeholder_page(
        "Assistente Comercial",
        "Faça perguntas usando a base oficial do Comercial.",
    ),
}


page_renderer = PAGE_RENDERERS.get(
    selected_page,
    PAGE_RENDERERS["Início"],
)

page_renderer()

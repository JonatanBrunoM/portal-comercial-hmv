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

from core.auth_service import (
    get_current_profile,
    get_google_user,
    is_hmv_email,
    login,
    logout,
    sync_supabase_session,
)

st.set_page_config(
    page_title=APP_CONFIG.APP_NAME,
    page_icon=APP_CONFIG.PAGE_ICON,
    layout=APP_CONFIG.LAYOUT,
    initial_sidebar_state="expanded",
)

apply_theme()

google_user = get_google_user()


if not google_user:

    st.markdown(
        """
        <div style="
            max-width: 540px;
            margin: 8vh auto 0 auto;
            text-align: center;
        ">
            <div style="
                font-size: 0.85rem;
                font-weight: 700;
                letter-spacing: .08em;
                text-transform: uppercase;
                opacity: .65;
                margin-bottom: 10px;
            ">
                Hospital Moinhos de Vento
            </div>

            <h1 style="margin-bottom: 12px;">
                Portal Comercial
            </h1>

            <p style="
                font-size: 1.05rem;
                opacity: .75;
                margin-bottom: 32px;
            ">
                Base integrada de informações comerciais,
                operacionais e de relacionamento com operadoras.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, login_col, _ = st.columns([1, 1.3, 1])

    with login_col:
        if st.button(
            "Entrar com Google",
            type="primary",
            use_container_width=True,
        ):
            login()

    st.stop()

email = google_user.get("email")


if not is_hmv_email(email):

    st.error(
        "Este Portal Comercial é restrito a contas "
        "institucionais @hmv.org.br."
    )

    st.write(
        f"Conta autenticada: **{email or 'não identificada'}**"
    )

    if st.button("Entrar com outra conta"):
        logout()

    st.stop()

try:
    sync_supabase_session()

except Exception as exc:
    st.error(
        "Não foi possível concluir a autenticação "
        "com o banco de dados."
    )

    st.exception(exc)

    if st.button("Sair"):
        logout()

    st.stop()

profile = get_current_profile()


if not profile:

    st.error(
        "Seu usuário foi autenticado, mas o perfil "
        "do Portal Comercial não foi localizado."
    )

    if st.button("Sair"):
        logout()

    st.stop()


if profile.get("status") != "Ativo":

    st.warning(
        "Seu acesso ao Portal Comercial está inativo."
    )

    if st.button("Sair"):
        logout()

    st.stop()

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

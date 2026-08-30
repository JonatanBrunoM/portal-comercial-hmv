import streamlit as st

from components.hero import (
    render_hero,
)

from components.sidebar import (
    render_sidebar,
)

from config.constants import (
    APP_CONFIG,
)

from config.theme import (
    apply_theme,
)

from core.auth_service import (
    get_allowed_domain,
    get_current_profile,
    get_google_user,
    is_email_allowed,
    login,
    logout,
)

from views.home import (
    render_home,
)

from views.pesquisa import (
    render_pesquisa,
)

from views.operadoras import (
    render_operadoras,
)

from views.portais import (
    render_portais,
)

from views.documentos import (
    render_documentos,
)

from views.contatos import (
    render_contatos,
)

from views.contingencias import (
    render_contingencias,
)

from views.comunicados import (
    render_comunicados,
)

from views.consultores import (
    render_consultores,
)

from views.forum import (
    render_forum,
)

from views.assistente import (
    render_assistente,
)

from views.particular import (
    render_particular,
)

from views.admin import (
    render_admin,
)


# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title=APP_CONFIG.APP_NAME,
    page_icon=APP_CONFIG.PAGE_ICON,
    layout=APP_CONFIG.LAYOUT,
    initial_sidebar_state="expanded",
)

apply_theme()


# =========================================================
# USUÁRIO GOOGLE
# =========================================================

google_user = (
    get_google_user()
)


# =========================================================
# LOGIN
# =========================================================

if not google_user:
    st.write("")

    st.write("")

    col_left, col_content, col_right = (
        st.columns(
            [1, 1.35, 1]
        )
    )

    with col_content:
        st.caption(
            APP_CONFIG.ORGANIZATION_NAME.upper()
        )

        st.title(
            APP_CONFIG.APP_NAME
        )

        st.write(
            "Base integrada de informações "
            "comerciais, operacionais e de "
            "relacionamento com operadoras."
        )

        st.write("")

        if st.button(
            "Entrar com Google",
            type="primary",
            use_container_width=True,
        ):
            login()

    st.stop()


# =========================================================
# VALIDAÇÃO DE ACESSO
# =========================================================

email = google_user.get(
    "email"
)


if not is_email_allowed(
    email
):
    st.write("")

    st.write("")

    col_left, col_content, col_right = (
        st.columns(
            [1, 1.5, 1]
        )
    )

    with col_content:
        st.title(
            "🔒 Acesso restrito"
        )

        st.write(
            "O Portal Comercial é destinado "
            "exclusivamente a usuários "
            "autorizados do Hospital "
            "Moinhos de Vento."
        )

        st.error(
            "O acesso está restrito a "
            f"contas institucionais "
            f"{get_allowed_domain()} "
            "ou usuários previamente "
            "autorizados."
        )

        st.info(
            "Conta autenticada no Google: "
            f"{email or 'não identificada'}"
        )

        if st.button(
            "Entrar com outra conta",
            use_container_width=True,
        ):
            logout()

    st.stop()


# =========================================================
# PERFIL DO PORTAL
# =========================================================

profile = (
    get_current_profile()
)


if not profile:
    st.error(
        "Não foi possível carregar "
        "seu perfil no Portal Comercial."
    )

    if st.button(
        "Sair da conta",
    ):
        logout()

    st.stop()


if (
    profile.get(
        "status"
    )
    != "Ativo"
):
    st.warning(
        "Seu acesso ao Portal Comercial "
        "está inativo."
    )

    st.caption(
        "Entre em contato com a "
        "administração do Portal."
    )

    if st.button(
        "Sair da conta",
    ):
        logout()

    st.stop()


# =========================================================
# ESTADO DA NAVEGAÇÃO
# =========================================================

if (
    "current_page"
    not in st.session_state
):
    st.session_state[
        "current_page"
    ] = APP_CONFIG.DEFAULT_PAGE


# =========================================================
# PÁGINA PLACEHOLDER
# =========================================================

def render_placeholder_page(
    title: str,
    description: str,
) -> None:
    """
    Renderiza temporariamente páginas
    ainda não implementadas.
    """

    render_hero(
        eyebrow=(
            APP_CONFIG.ORGANIZATION_NAME
        ),
        title=title,
        description=description,
    )

    st.info(
        "A estrutura desta página "
        "está pronta e será implementada "
        "nos próximos módulos."
    )


# =========================================================
# SIDEBAR
# =========================================================

selected_page = (
    render_sidebar()
)


# =========================================================
# ROTAS
# =========================================================

PAGE_RENDERERS = {
    "Início": render_home,
    "Pesquisa": render_pesquisa,
    "Operadoras": render_operadoras,
    "Portais": render_portais,
    "Documentos": render_documentos,
    "Contatos": render_contatos,
    "Contingências": (
        render_contingencias
    ),
    "Comunicados": (
        render_comunicados
    ),
    "Consultores": (
        render_consultores
    ),
    "Particular": (
        render_particular
    ),
    "Fórum": render_forum,
    "Assistente": (
        render_assistente
    ),
    "Administração": (
        render_admin
    ),
}


# =========================================================
# PROTEÇÃO DA ADMINISTRAÇÃO
# =========================================================

if (
    selected_page
    == "Administração"
    and profile.get(
        "role"
    )
    != "admin"
):
    st.session_state[
        "current_page"
    ] = APP_CONFIG.DEFAULT_PAGE

    st.session_state.pop(
        "main_navigation",
        None,
    )

    st.warning(
        "Você não possui permissão "
        "para acessar a Administração."
    )

    st.stop()


# =========================================================
# RENDERIZAÇÃO
# =========================================================

page_renderer = (
    PAGE_RENDERERS.get(
        selected_page,
        PAGE_RENDERERS[
            "Início"
        ],
    )
)

page_renderer()

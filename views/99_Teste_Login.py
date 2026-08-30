import streamlit as st

from core.auth_service import (
    get_current_user,
    logout,
    process_oauth_callback,
    start_google_login,
)


st.set_page_config(
    page_title="Teste de Login",
    page_icon="🔐",
)

st.title("🔐 Teste Supabase Auth")


# =========================================================
# CALLBACK DO OAUTH
# =========================================================

try:
    if process_oauth_callback():
        st.success("Login processado com sucesso.")
        st.rerun()

except Exception as exc:
    st.error("Erro ao processar o retorno do Google.")
    st.exception(exc)
    st.stop()


# =========================================================
# USUÁRIO ATUAL
# =========================================================

user = get_current_user()


if user:

    st.success("✅ Usuário autenticado.")

    st.write("ID:")
    st.code(user.id)

    st.write("E-mail:")
    st.write(user.email)

    metadata = user.user_metadata or {}

    st.write("Nome:")
    st.write(
        metadata.get("full_name")
        or metadata.get("name")
        or "Não informado"
    )

    if st.button("Sair"):
        logout()
        st.rerun()

else:

    st.info("Nenhum usuário autenticado.")

    login_url = start_google_login()

    st.link_button(
        "Entrar com Google",
        login_url,
        use_container_width=True,
    )

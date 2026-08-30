from __future__ import annotations

import streamlit as st

from core.supabase_repository import get_supabase_client


ALLOWED_DOMAIN = "@hmv.org.br"


def is_streamlit_authenticated() -> bool:
    """
    Verifica se o usuário possui sessão OIDC válida
    mantida pelo próprio Streamlit.
    """

    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def get_google_user() -> dict | None:
    """
    Retorna os dados do usuário autenticado pelo Google.
    """

    if not is_streamlit_authenticated():
        return None

    return {
        "email": getattr(st.user, "email", None),
        "name": getattr(st.user, "name", None),
        "picture": getattr(st.user, "picture", None),
        "sub": getattr(st.user, "sub", None),
    }


def get_google_id_token() -> str | None:
    """
    Obtém o ID Token disponibilizado pelo Streamlit.
    """

    if not is_streamlit_authenticated():
        return None

    try:
        tokens = st.user.tokens

        if not tokens:
            return None

        return tokens.get("id")

    except Exception:
        return None


def is_hmv_email(email: str | None) -> bool:
    """
    Valida o domínio institucional.
    """

    if not email:
        return False

    return email.strip().lower().endswith(ALLOWED_DOMAIN)


def sync_supabase_session():
    """
    Usa o ID Token do Google para criar uma sessão
    autenticada no Supabase.

    Essa sessão é usada pelo PostgreSQL/RLS.
    """

    if not is_streamlit_authenticated():
        return None

    if st.session_state.get("supabase_auth_ready"):
        return get_supabase_client().auth.get_session()

    id_token = get_google_id_token()

    if not id_token:
        raise RuntimeError(
            "O Google autenticou o usuário, mas o ID Token "
            "não foi disponibilizado pelo Streamlit."
        )

    supabase = get_supabase_client()

    response = supabase.auth.sign_in_with_id_token(
        {
            "provider": "google",
            "token": id_token,
        }
    )

    if not response.session:
        raise RuntimeError(
            "O Supabase não conseguiu criar a sessão autenticada."
        )

    st.session_state["supabase_auth_ready"] = True

    return response.session


def get_current_user():
    """
    Obtém o usuário validado diretamente pelo Supabase.
    """

    if not st.session_state.get("supabase_auth_ready"):
        return None

    try:
        response = get_supabase_client().auth.get_user()

        return response.user if response else None

    except Exception:
        return None


def get_current_profile() -> dict | None:
    """
    Consulta o profile do usuário autenticado.
    """

    user = get_current_user()

    if not user:
        return None

    response = (
        get_supabase_client()
        .table("profiles")
        .select("*")
        .eq("id", user.id)
        .limit(1)
        .execute()
    )

    data = response.data or []

    return data[0] if data else None


def is_admin() -> bool:
    profile = get_current_profile()

    if not profile:
        return False

    return (
        profile.get("role") == "admin"
        and profile.get("status") == "Ativo"
    )


def login():
    """
    Inicia autenticação Google através do Streamlit.
    """

    st.login("google")


def logout():
    """
    Encerra Supabase e Google/Streamlit.
    """

    try:
        if st.session_state.get("supabase_client"):
            try:
                get_supabase_client().auth.sign_out()
            except Exception:
                pass

    finally:
        for key in [
            "supabase_client",
            "supabase_auth_ready",
            "auth_profile",
            "auth_user",
            "current_page",
            "main_navigation",
        ]:
            st.session_state.pop(key, None)

        st.logout()

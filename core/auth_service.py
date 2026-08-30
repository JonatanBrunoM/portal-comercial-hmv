from __future__ import annotations

import streamlit as st

from core.supabase_repository import get_supabase_client


PORTAL_URL = "https://comercial-hmv.streamlit.app/"


def get_auth_client():
    return get_supabase_client()


def get_current_session():
    """
    Retorna a sessão Supabase atual, quando existir.
    """

    try:
        supabase = get_auth_client()
        response = supabase.auth.get_session()

        return response

    except Exception:
        return None


def get_current_user():
    """
    Retorna o usuário autenticado no Supabase.
    """

    try:
        supabase = get_auth_client()
        response = supabase.auth.get_user()

        if response and response.user:
            return response.user

    except Exception:
        pass

    return None


def start_google_login():
    """
    Gera a URL de autenticação Google via Supabase.
    """

    supabase = get_auth_client()

    response = supabase.auth.sign_in_with_oauth(
        {
            "provider": "google",
            "options": {
                "redirect_to": PORTAL_URL,
            },
        }
    )

    return response.url


def process_oauth_callback():
    """
    Processa o ?code= retornado pelo Supabase no fluxo PKCE.
    """

    code = st.query_params.get("code")

    if not code:
        return False

    # Evita tentar trocar o mesmo código novamente.
    if st.session_state.get("oauth_code_processed") == code:
        return False

    supabase = get_auth_client()

    response = supabase.auth.exchange_code_for_session(
        {
            "auth_code": code,
        }
    )

    if response.session:
        st.session_state["oauth_code_processed"] = code

        # Remove o código da URL depois da troca.
        st.query_params.clear()

        return True

    return False


def logout():
    """
    Encerra a sessão Supabase e limpa o estado local.
    """

    try:
        supabase = get_auth_client()
        supabase.auth.sign_out()

    finally:
        keys_to_remove = [
            "supabase_client",
            "oauth_code_processed",
            "auth_user",
            "auth_profile",
        ]

        for key in keys_to_remove:
            st.session_state.pop(key, None)

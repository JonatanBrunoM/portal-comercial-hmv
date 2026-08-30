from __future__ import annotations

import streamlit as st

from core.supabase_repository import (
    get_supabase_client,
    reset_supabase_client,
)


ALLOWED_DOMAIN = "@hmv.org.br"


def is_streamlit_authenticated() -> bool:
    """
    Verifica se existe uma sessão OIDC válida
    mantida pelo Streamlit.
    """

    try:
        return bool(
            st.user.is_logged_in
        )

    except Exception:
        return False


def get_google_user() -> dict | None:
    """
    Retorna as principais informações do usuário
    autenticado pelo Google.
    """

    if not is_streamlit_authenticated():
        return None

    return {
        "email": getattr(
            st.user,
            "email",
            None,
        ),
        "name": getattr(
            st.user,
            "name",
            None,
        ),
        "picture": getattr(
            st.user,
            "picture",
            None,
        ),
        "sub": getattr(
            st.user,
            "sub",
            None,
        ),
    }


def get_google_id_token() -> str | None:
    """
    Obtém o ID Token disponibilizado pelo Streamlit.

    O token é usado somente no servidor para criar
    a sessão correspondente no Supabase.
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


def is_hmv_email(
    email: str | None,
) -> bool:
    """
    Valida se o e-mail pertence ao domínio
    institucional permitido.
    """

    if not email:
        return False

    email_normalizado = (
        email
        .strip()
        .lower()
    )

    return email_normalizado.endswith(
        ALLOWED_DOMAIN
    )


def login() -> None:
    """
    Inicia o fluxo de autenticação Google.
    """

    st.login("google")


def sync_supabase_session():
    """
    Cria a sessão autenticada no Supabase
    utilizando o ID Token recebido do Google.

    Essa autenticação fornece ao cliente Supabase
    o JWT necessário para aplicação das políticas RLS.
    """

    if not is_streamlit_authenticated():
        return None

    supabase = get_supabase_client()

    if st.session_state.get(
        "supabase_auth_ready"
    ):
        try:
            session = (
                supabase
                .auth
                .get_session()
            )

            if session:
                return session

        except Exception:
            st.session_state.pop(
                "supabase_auth_ready",
                None,
            )

    id_token = get_google_id_token()

    if not id_token:
        raise RuntimeError(
            "O usuário foi autenticado pelo Google, "
            "mas o ID Token não foi disponibilizado."
        )

    response = (
        supabase
        .auth
        .sign_in_with_id_token(
            {
                "provider": "google",
                "token": id_token,
            }
        )
    )

    if not response.session:
        raise RuntimeError(
            "O Supabase não conseguiu criar "
            "uma sessão autenticada."
        )

    st.session_state[
        "supabase_auth_ready"
    ] = True

    return response.session


def get_current_user():
    """
    Retorna o usuário autenticado no Supabase.
    """

    if not st.session_state.get(
        "supabase_auth_ready"
    ):
        return None

    try:
        response = (
            get_supabase_client()
            .auth
            .get_user()
        )

        if response:
            return response.user

    except Exception:
        return None

    return None


def get_current_profile(
    force_refresh: bool = False,
) -> dict | None:
    """
    Consulta o perfil do usuário autenticado.

    Mantém o perfil em session_state para evitar
    consultas repetidas ao Supabase a cada componente.
    """

    if (
        not force_refresh
        and "auth_profile" in st.session_state
    ):
        return st.session_state[
            "auth_profile"
        ]

    user = get_current_user()

    if not user:
        return None

    try:
        response = (
            get_supabase_client()
            .table("profiles")
            .select("*")
            .eq(
                "id",
                user.id,
            )
            .limit(1)
            .execute()
        )

        data = response.data or []

        profile = (
            data[0]
            if data
            else None
        )

        if profile:
            st.session_state[
                "auth_profile"
            ] = profile

        return profile

    except Exception:
        return None


def is_admin() -> bool:
    """
    Verifica se o usuário atual possui perfil admin.
    """

    profile = get_current_profile()

    if not profile:
        return False

    return (
        profile.get("role") == "admin"
        and profile.get("status") == "Ativo"
    )


def logout() -> None:
    """
    Encerra a sessão Supabase e a sessão OIDC
    mantida pelo Streamlit.
    """

    try:
        if st.session_state.get(
            "supabase_client"
        ):
            try:
                (
                    get_supabase_client()
                    .auth
                    .sign_out()
                )

            except Exception:
                pass

    finally:
        keys_to_remove = [
            "supabase_auth_ready",
            "auth_profile",
            "auth_user",
            "current_page",
            "pending_page",
            "main_navigation",
        ]

        for key in keys_to_remove:
            st.session_state.pop(
                key,
                None,
            )

        reset_supabase_client()

        st.logout()

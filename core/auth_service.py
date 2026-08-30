from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from core.supabase_repository import get_supabase_client


ALLOWED_DOMAIN = "@hmv.org.br"


# =========================================================
# UTILITÁRIOS
# =========================================================


def _normalize_email(
    email: str | None,
) -> str:
    """
    Normaliza um endereço de e-mail.
    """

    return (
        email or ""
    ).strip().lower()


def _utc_now_iso() -> str:
    """
    Retorna o horário atual em UTC
    no formato ISO.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# AUTENTICAÇÃO STREAMLIT / GOOGLE
# =========================================================


def is_streamlit_authenticated() -> bool:
    """
    Verifica se existe uma sessão
    Google/OIDC válida no Streamlit.
    """

    try:
        return bool(
            st.user.is_logged_in
        )

    except Exception:
        return False


def get_google_user() -> dict | None:
    """
    Retorna os principais dados
    disponibilizados pelo Google.
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


def is_hmv_email(
    email: str | None,
) -> bool:
    """
    Permite somente contas institucionais
    do Hospital Moinhos de Vento.
    """

    normalized = _normalize_email(
        email
    )

    return (
        bool(normalized)
        and normalized.endswith(
            ALLOWED_DOMAIN
        )
    )


def is_email_allowed(
    email: str | None,
) -> bool:
    """
    Mantido para compatibilidade
    com o app.py.

    Não há mais exceções.
    """

    return is_hmv_email(
        email
    )


def get_allowed_domain() -> str:
    """
    Retorna o domínio institucional.
    """

    return ALLOWED_DOMAIN


def login() -> None:
    """
    Inicia a autenticação Google
    pelo OIDC nativo do Streamlit.
    """

    st.login()


# =========================================================
# PERFIL DO PORTAL
# =========================================================


def _find_profile_by_email(
    email: str,
) -> dict | None:
    """
    Procura um perfil pelo e-mail.
    """

    response = (
        get_supabase_client()
        .table("profiles")
        .select("*")
        .ilike(
            "email",
            email,
        )
        .limit(1)
        .execute()
    )

    data = response.data or []

    return (
        data[0]
        if data
        else None
    )


def _create_profile(
    google_user: dict,
) -> dict:
    """
    Cria automaticamente o perfil
    do colaborador no primeiro acesso.
    """

    email = _normalize_email(
        google_user.get(
            "email"
        )
    )

    nome = (
        google_user.get(
            "name"
        )
        or email.split(
            "@",
            1,
        )[0]
    )

    now = _utc_now_iso()

    payload = {
        "nome": nome,
        "email": email,
        "foto_url": google_user.get(
            "picture"
        ),
        "google_sub": google_user.get(
            "sub"
        ),
        "auth_provider": "google",
        "role": "usuario",
        "status": "Ativo",
        "primeiro_acesso_em": now,
        "ultimo_acesso_em": now,
        "ultimo_login_em": now,
    }

    response = (
        get_supabase_client()
        .table("profiles")
        .insert(
            payload
        )
        .execute()
    )

    data = response.data or []

    if not data:
        raise RuntimeError(
            "O perfil institucional não pôde ser criado."
        )

    return data[0]


def _update_profile_from_google(
    profile: dict,
    google_user: dict,
) -> dict:
    """
    Atualiza informações básicas do perfil
    com os dados mais recentes do Google.

    Role e status não são alterados aqui.
    """

    profile_id = profile.get(
        "id"
    )

    if not profile_id:
        return profile

    nome_google = (
        google_user.get(
            "name"
        )
        or profile.get(
            "nome"
        )
    )

    foto_google = (
        google_user.get(
            "picture"
        )
        or profile.get(
            "foto_url"
        )
    )

    google_sub = (
        google_user.get(
            "sub"
        )
        or profile.get(
            "google_sub"
        )
    )

    now = _utc_now_iso()

    payload = {
        "nome": nome_google,
        "foto_url": foto_google,
        "google_sub": google_sub,
        "ultimo_acesso_em": now,
        "ultimo_login_em": now,
    }

    response = (
        get_supabase_client()
        .table("profiles")
        .update(
            payload
        )
        .eq(
            "id",
            profile_id,
        )
        .execute()
    )

    data = response.data or []

    if data:
        return data[0]

    updated_profile = (
        profile.copy()
    )

    updated_profile.update(
        payload
    )

    return updated_profile


def get_current_profile(
    force_refresh: bool = False,
) -> dict | None:
    """
    Retorna o perfil do usuário atual.

    Primeiro acesso:
        cria o perfil automaticamente.

    Próximos acessos:
        recupera e sincroniza nome,
        foto e último acesso.

    Role e status permanecem controlados
    pelo próprio Portal.
    """

    if (
        not force_refresh
        and "auth_profile"
        in st.session_state
    ):
        return st.session_state[
            "auth_profile"
        ]

    google_user = (
        get_google_user()
    )

    if not google_user:
        return None

    email = _normalize_email(
        google_user.get(
            "email"
        )
    )

    if not is_hmv_email(
        email
    ):
        return None

    try:
        profile = (
            _find_profile_by_email(
                email
            )
        )

        if not profile:
            profile = (
                _create_profile(
                    google_user
                )
            )

        else:
            profile = (
                _update_profile_from_google(
                    profile,
                    google_user,
                )
            )

        st.session_state[
            "auth_profile"
        ] = profile

        return profile

    except Exception as exc:
        raise RuntimeError(
            "Não foi possível carregar ou criar "
            "o perfil institucional do usuário."
        ) from exc


# =========================================================
# PERMISSÕES
# =========================================================


def is_admin() -> bool:
    """
    Retorna True somente para
    administradores ativos.
    """

    profile = (
        get_current_profile()
    )

    return bool(
        profile
        and profile.get(
            "status"
        ) == "Ativo"
        and profile.get(
            "role"
        ) == "admin"
    )


def require_admin() -> dict:
    """
    Garante que o usuário seja
    administrador.
    """

    profile = (
        get_current_profile()
    )

    if not profile:
        raise PermissionError(
            "Usuário não autenticado."
        )

    if profile.get(
        "status"
    ) != "Ativo":
        raise PermissionError(
            "Usuário inativo."
        )

    if profile.get(
        "role"
    ) != "admin":
        raise PermissionError(
            "Esta operação é restrita "
            "a administradores."
        )

    return profile


# =========================================================
# LOGOUT
# =========================================================


def logout() -> None:
    """
    Limpa os dados internos da sessão
    antes de encerrar o login Google.
    """

    keys_to_remove = [
        "auth_profile",
        "current_page",
        "pending_page",
        "main_navigation",
    ]

    for key in keys_to_remove:
        st.session_state.pop(
            key,
            None,
        )

    st.logout()

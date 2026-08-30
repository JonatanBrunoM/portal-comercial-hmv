from __future__ import annotations

import streamlit as st

from core.supabase_repository import get_supabase_client


DEFAULT_ALLOWED_DOMAIN = "@hmv.org.br"


def _get_authorization_setting(
    name: str,
    default=None,
):
    """
    Lê uma configuração opcional da seção
    [AUTHORIZATION] dos Secrets.
    """

    try:
        section = st.secrets.get(
            "AUTHORIZATION",
            {},
        )

        return section.get(
            name,
            default,
        )

    except Exception:
        return default


def _normalize_email(
    email: str | None,
) -> str:
    """
    Normaliza endereços de e-mail.
    """

    return (
        email or ""
    ).strip().lower()


def _normalize_email_list(
    values,
) -> set[str]:
    """
    Converte uma configuração de e-mails
    em um conjunto normalizado.
    """

    if not values:
        return set()

    if isinstance(
        values,
        str,
    ):
        values = [values]

    return {
        _normalize_email(value)
        for value in values
        if _normalize_email(value)
    }


def is_streamlit_authenticated() -> bool:
    """
    Verifica se existe uma sessão OIDC
    válida mantida pelo Streamlit.
    """

    try:
        return bool(
            st.user.is_logged_in
        )

    except Exception:
        return False


def get_google_user() -> dict | None:
    """
    Retorna os principais dados do usuário
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


def get_allowed_domain() -> str:
    """
    Retorna o domínio institucional autorizado.
    """

    domain = _get_authorization_setting(
        "ALLOWED_DOMAIN",
        DEFAULT_ALLOWED_DOMAIN,
    )

    domain = str(
        domain or DEFAULT_ALLOWED_DOMAIN
    ).strip().lower()

    if not domain.startswith("@"):
        domain = f"@{domain}"

    return domain


def is_hmv_email(
    email: str | None,
) -> bool:
    """
    Verifica se o e-mail pertence
    ao domínio institucional.
    """

    normalized = _normalize_email(
        email
    )

    return (
        bool(normalized)
        and normalized.endswith(
            get_allowed_domain()
        )
    )


def is_email_allowed(
    email: str | None,
) -> bool:
    """
    Autoriza:

    1. contas do domínio institucional;
    2. e-mails explicitamente cadastrados
       em TEST_EMAILS nos Secrets.

    TEST_EMAILS existe somente para
    desenvolvimento/apresentação.
    """

    normalized = _normalize_email(
        email
    )

    if not normalized:
        return False

    if is_hmv_email(
        normalized
    ):
        return True

    test_emails = _normalize_email_list(
        _get_authorization_setting(
            "TEST_EMAILS",
            [],
        )
    )

    return normalized in test_emails


def _is_configured_admin(
    email: str | None,
) -> bool:
    """
    Verifica administradores definidos
    temporariamente nos Secrets.
    """

    normalized = _normalize_email(
        email
    )

    admin_emails = _normalize_email_list(
        _get_authorization_setting(
            "ADMIN_EMAILS",
            [],
        )
    )

    return normalized in admin_emails


def login() -> None:
    """
    Inicia o login Google configurado
    pelo OIDC nativo do Streamlit.
    """

    st.login()


def get_current_profile(
    force_refresh: bool = False,
) -> dict | None:
    """
    Retorna o perfil atual da aplicação.

    A autenticação é realizada pelo Google/Streamlit.

    Caso exista um registro correspondente
    em public.profiles, seus dados são utilizados.

    Caso ainda não exista, um usuário autorizado
    recebe um perfil operacional padrão.
    """

    if (
        not force_refresh
        and "auth_profile"
        in st.session_state
    ):
        return st.session_state[
            "auth_profile"
        ]

    google_user = get_google_user()

    if not google_user:
        return None

    email = _normalize_email(
        google_user.get(
            "email"
        )
    )

    if not is_email_allowed(
        email
    ):
        return None

    profile = {
        "id": None,
        "nome": (
            google_user.get("name")
            or email.split(
                "@",
                1,
            )[0]
        ),
        "email": email,
        "foto_url": google_user.get(
            "picture"
        ),
        "role": "usuario",
        "status": "Ativo",
        "source": "streamlit_oidc",
    }

    # -----------------------------------------------------
    # PERFIL EXISTENTE NO SUPABASE
    # -----------------------------------------------------

    try:
        response = (
            get_supabase_client()
            .table("profiles")
            .select(
                "id,nome,email,"
                "foto_url,role,status"
            )
            .eq(
                "email",
                email,
            )
            .limit(1)
            .execute()
        )

        data = response.data or []

        if data:
            database_profile = (
                data[0]
            )

            for key in (
                "id",
                "nome",
                "email",
                "foto_url",
                "role",
                "status",
            ):
                if (
                    database_profile.get(
                        key
                    )
                    is not None
                ):
                    profile[key] = (
                        database_profile[
                            key
                        ]
                    )

            profile[
                "source"
            ] = "supabase_profiles"

    except Exception:
        # Usuários autorizados continuam
        # podendo acessar mesmo que ainda
        # não exista profile pré-cadastrado.
        pass

    # -----------------------------------------------------
    # ADMIN TEMPORÁRIO VIA SECRETS
    # -----------------------------------------------------

    if _is_configured_admin(
        email
    ):
        profile[
            "role"
        ] = "admin"

    st.session_state[
        "auth_profile"
    ] = profile

    return profile


def is_admin() -> bool:
    """
    Verifica se o usuário atual é
    administrador ativo.
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


def logout() -> None:
    """
    Limpa o estado da aplicação
    e encerra a sessão OIDC.
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

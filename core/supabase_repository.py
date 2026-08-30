from __future__ import annotations

import pandas as pd
import streamlit as st

from supabase import (
    Client,
    create_client,
)


@st.cache_resource
def get_supabase_client() -> Client:
    """
    Retorna o cliente server-side do Supabase.

    O cliente utiliza SERVICE_ROLE_KEY.

    IMPORTANTE:
    Essa chave existe somente no servidor Streamlit
    e nunca deve ser enviada ao navegador,
    exibida em logs ou adicionada ao GitHub.
    """

    url = st.secrets[
        "SUPABASE"
    ]["URL"]

    service_role_key = st.secrets[
        "SUPABASE"
    ]["SERVICE_ROLE_KEY"]

    return create_client(
        url,
        service_role_key,
    )


def _require_authenticated() -> dict:
    """
    Bloqueia consultas realizadas
    sem perfil autenticado e ativo.
    """

    profile = st.session_state.get(
        "auth_profile"
    )

    if (
        not profile
        or profile.get(
            "status"
        ) != "Ativo"
    ):
        raise PermissionError(
            "É necessário estar autenticado "
            "para acessar o Portal Comercial."
        )

    return profile


def _require_admin() -> dict:
    """
    Bloqueia alterações no banco para
    usuários que não sejam administradores.
    """

    profile = (
        _require_authenticated()
    )

    if profile.get(
        "role"
    ) != "admin":
        raise PermissionError(
            "Esta operação é restrita "
            "aos administradores "
            "do Portal Comercial."
        )

    return profile


def fetch_table(
    table_name: str,
    *,
    order_by: str | None = None,
    ascending: bool = True,
) -> pd.DataFrame:
    """
    Busca todos os registros
    de uma tabela.
    """

    _require_authenticated()

    query = (
        get_supabase_client()
        .table(
            table_name
        )
        .select("*")
    )

    if order_by:
        query = query.order(
            order_by,
            desc=not ascending,
        )

    response = (
        query.execute()
    )

    return pd.DataFrame(
        response.data or []
    )


def fetch_by_id(
    table_name: str,
    record_id: str,
) -> dict | None:
    """
    Busca um registro pelo UUID.
    """

    _require_authenticated()

    response = (
        get_supabase_client()
        .table(
            table_name
        )
        .select("*")
        .eq(
            "id",
            record_id,
        )
        .limit(1)
        .execute()
    )

    data = (
        response.data or []
    )

    return (
        data[0]
        if data
        else None
    )


def insert_record(
    table_name: str,
    payload: dict,
) -> dict | None:
    """
    Insere um novo registro.

    Restrito a administradores.
    """

    _require_admin()

    response = (
        get_supabase_client()
        .table(
            table_name
        )
        .insert(
            payload
        )
        .execute()
    )

    data = (
        response.data or []
    )

    return (
        data[0]
        if data
        else None
    )


def update_record(
    table_name: str,
    record_id: str,
    payload: dict,
) -> dict | None:
    """
    Atualiza um registro.

    Restrito a administradores.
    """

    _require_admin()

    response = (
        get_supabase_client()
        .table(
            table_name
        )
        .update(
            payload
        )
        .eq(
            "id",
            record_id,
        )
        .execute()
    )

    data = (
        response.data or []
    )

    return (
        data[0]
        if data
        else None
    )


def delete_record(
    table_name: str,
    record_id: str,
) -> None:
    """
    Remove um registro.

    Restrito a administradores.
    """

    _require_admin()

    (
        get_supabase_client()
        .table(
            table_name
        )
        .delete()
        .eq(
            "id",
            record_id,
        )
        .execute()
    )

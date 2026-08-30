from __future__ import annotations

import pandas as pd
import streamlit as st

from supabase import Client, create_client


def get_supabase_client() -> Client:
    """
    Retorna um cliente Supabase isolado para
    a sessão atual do usuário no Streamlit.

    O cliente não utiliza @st.cache_resource,
    pois mantém estado individual de autenticação.
    """

    if "supabase_client" not in st.session_state:
        url = st.secrets["SUPABASE"]["URL"]
        key = st.secrets["SUPABASE"]["ANON_KEY"]

        st.session_state["supabase_client"] = create_client(
            url,
            key,
        )

    return st.session_state["supabase_client"]


def reset_supabase_client() -> None:
    """
    Remove o cliente Supabase da sessão atual.
    """

    st.session_state.pop(
        "supabase_client",
        None,
    )


def fetch_table(
    table_name: str,
    *,
    order_by: str | None = None,
    ascending: bool = True,
) -> pd.DataFrame:
    """
    Busca todos os registros de uma tabela
    e retorna um DataFrame.

    O retorno em DataFrame é mantido para
    preservar compatibilidade com os services
    e views existentes durante a migração.
    """

    client = get_supabase_client()

    query = (
        client
        .table(table_name)
        .select("*")
    )

    if order_by:
        query = query.order(
            order_by,
            desc=not ascending,
        )

    response = query.execute()

    data = response.data or []

    return pd.DataFrame(data)


def fetch_by_id(
    table_name: str,
    record_id: str,
) -> dict | None:
    """
    Busca um registro pelo UUID.
    """

    client = get_supabase_client()

    response = (
        client
        .table(table_name)
        .select("*")
        .eq("id", record_id)
        .limit(1)
        .execute()
    )

    data = response.data or []

    return data[0] if data else None


def insert_record(
    table_name: str,
    payload: dict,
) -> dict | None:
    """
    Insere um novo registro.
    """

    client = get_supabase_client()

    response = (
        client
        .table(table_name)
        .insert(payload)
        .execute()
    )

    data = response.data or []

    return data[0] if data else None


def update_record(
    table_name: str,
    record_id: str,
    payload: dict,
) -> dict | None:
    """
    Atualiza um registro pelo UUID.
    """

    client = get_supabase_client()

    response = (
        client
        .table(table_name)
        .update(payload)
        .eq("id", record_id)
        .execute()
    )

    data = response.data or []

    return data[0] if data else None


def delete_record(
    table_name: str,
    record_id: str,
) -> None:
    """
    Remove um registro pelo UUID.

    Para os principais cadastros do Portal
    será priorizada a inativação lógica.
    """

    client = get_supabase_client()

    (
        client
        .table(table_name)
        .delete()
        .eq("id", record_id)
        .execute()
    )

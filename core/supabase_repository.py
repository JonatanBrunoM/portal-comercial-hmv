from __future__ import annotations

import pandas as pd
import streamlit as st
from supabase import Client, create_client


from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions


def get_supabase_client() -> Client:
    """
    Retorna um cliente Supabase isolado por sessão Streamlit.

    Não usamos @st.cache_resource porque o cliente mantém
    estado de autenticação.
    """

    if "supabase_client" not in st.session_state:

        url = st.secrets["SUPABASE"]["URL"]
        key = st.secrets["SUPABASE"]["ANON_KEY"]

        options = ClientOptions(
            flow_type="pkce",
            auto_refresh_token=True,
            persist_session=True,
        )

        st.session_state["supabase_client"] = create_client(
            url,
            key,
            options=options,
        )

    return st.session_state["supabase_client"]


def fetch_table(
    table_name: str,
    *,
    order_by: str | None = None,
    ascending: bool = True,
) -> pd.DataFrame:
    """
    Busca todos os registros de uma tabela e retorna DataFrame.

    Mantemos DataFrame nesta primeira fase para preservar
    compatibilidade com os services e views existentes.
    """

    client = get_supabase_client()

    query = client.table(table_name).select("*")

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
    Insere um registro.
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

    Para cadastros principais vamos preferir inativação.
    Este método ficará disponível para relacionamentos
    e casos administrativos específicos.
    """

    client = get_supabase_client()

    (
        client
        .table(table_name)
        .delete()
        .eq("id", record_id)
        .execute()
    )

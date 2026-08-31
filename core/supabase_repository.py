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



def check_supabase_connection() -> tuple[bool, str]:
    """Valida a conexão server-side sem expor detalhes sensíveis."""

    _require_authenticated()

    try:
        (
            get_supabase_client()
            .table("operadoras")
            .select("id")
            .limit(1)
            .execute()
        )

        return True, "Supabase conectado e operacional."

    except Exception:
        return (
            False,
            "Não foi possível validar a conexão com o Supabase. "
            "Verifique os Secrets e tente novamente.",
        )


def fetch_records(
    table_name: str,
    *,
    filters: dict[str, object] | None = None,
    columns: str = "*",
    order_by: str | None = None,
    ascending: bool = True,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Busca registros com filtros executados no Supabase.

    Esta função é a base para serviços que não precisam carregar
    uma tabela inteira antes de filtrar os dados em memória.
    """

    _require_authenticated()

    query = (
        get_supabase_client()
        .table(table_name)
        .select(columns)
    )

    for column, value in (filters or {}).items():
        if value is None:
            query = query.is_(column, "null")
        else:
            query = query.eq(column, value)

    if order_by:
        query = query.order(
            order_by,
            desc=not ascending,
        )

    if limit is not None:
        query = query.limit(limit)

    response = query.execute()

    return pd.DataFrame(response.data or [])

def fetch_table(
    table_name: str,
    *,
    order_by: str | None = None,
    ascending: bool = True,
) -> pd.DataFrame:
    """Busca todos os registros de uma tabela."""

    return fetch_records(
        table_name,
        order_by=order_by,
        ascending=ascending,
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

def append_audit_event(
    *,
    action: str,
    entity: str,
    entity_id: str | None = None,
    description: str | None = None,
    previous_data: dict | None = None,
    new_data: dict | None = None,
) -> dict | None:
    """
    Registra um evento de auditoria para qualquer usuário autenticado.

    Esta função é deliberadamente limitada à tabela audit_logs e não aceita
    payload arbitrário do chamador. Nunca use para registrar senha, token,
    cookie, chave de API ou conteúdo descriptografado.
    """
    profile = _require_authenticated()

    payload = {
        "usuario_id": profile.get("id"),
        "acao": action,
        "entidade": entity,
        "entidade_id": entity_id,
        "descricao": description,
        "dados_anteriores": previous_data,
        "dados_novos": new_data,
    }

    response = (
        get_supabase_client()
        .table("audit_logs")
        .insert(payload)
        .execute()
    )

    data = response.data or []
    return data[0] if data else None

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.supabase_repository import (
    get_supabase_client,
)


# =========================================================
# MODELO UTILIZADO PELA INTERFACE
# =========================================================


@dataclass
class OperadoraSummary:
    operator_id: str
    code: str
    name: str
    short_name: str
    status: str
    observations: str
    logo_url: str
    site_url: str
    plans_count: int
    consultant: str


# =========================================================
# UTILITÁRIOS
# =========================================================


def _safe_string(value) -> str:
    """
    Converte valores opcionais em texto seguro.
    """

    if value is None:
        return ""

    return str(value).strip()


def _build_operadora_summary(
    row: dict,
    plans_count: int = 0,
    consultant: str = "",
) -> OperadoraSummary:
    """
    Converte um registro do Supabase no formato
    esperado pelos componentes atuais do Portal.
    """

    nome = _safe_string(
        row.get("nome")
    )

    nome_curto = (
        _safe_string(
            row.get("nome_curto")
        )
        or nome
    )

    return OperadoraSummary(
        operator_id=_safe_string(
            row.get("id")
        ),
        code=_safe_string(
            row.get("codigo")
        ),
        name=nome,
        short_name=nome_curto,
        status=_safe_string(
            row.get("status")
        ),
        observations=_safe_string(
            row.get("observacoes")
        ),
        logo_url=_safe_string(
            row.get("logo_url")
        ),
        site_url=_safe_string(
            row.get("site_url")
        ),
        plans_count=int(
            plans_count or 0
        ),
        consultant=_safe_string(
            consultant
        ),
    )


# =========================================================
# OPERADORAS
# =========================================================


def search_operadoras(
    query: str = "",
) -> list[OperadoraSummary]:
    """
    Retorna as operadoras cadastradas no Supabase.

    A busca considera:
    - nome;
    - nome curto;
    - código.
    """

    client = get_supabase_client()

    response = (
        client
        .table("operadoras")
        .select(
            "id,"
            "codigo,"
            "nome,"
            "nome_curto,"
            "status,"
            "observacoes,"
            "logo_url,"
            "site_url"
        )
        .order(
            "nome",
            desc=False,
        )
        .execute()
    )

    rows = response.data or []

    search_term = (
        query or ""
    ).strip().lower()

    if search_term:
        filtered_rows = []

        for row in rows:
            searchable_values = [
                row.get("nome"),
                row.get("nome_curto"),
                row.get("codigo"),
            ]

            searchable_text = " ".join(
                _safe_string(value).lower()
                for value
                in searchable_values
            )

            if search_term in searchable_text:
                filtered_rows.append(
                    row
                )

        rows = filtered_rows

    results: list[
        OperadoraSummary
    ] = []

    for row in rows:
        operator_id = _safe_string(
            row.get("id")
        )

        plans_count = (
            _count_operadora_planos(
                operator_id
            )
        )

        consultant = (
            _get_operadora_consultant(
                operator_id
            )
        )

        results.append(
            _build_operadora_summary(
                row,
                plans_count=plans_count,
                consultant=consultant,
            )
        )

    return results


def get_operadora_by_id(
    operator_id: str,
) -> OperadoraSummary | None:
    """
    Retorna uma operadora pelo UUID.
    """

    if not operator_id:
        return None

    response = (
        get_supabase_client()
        .table("operadoras")
        .select(
            "id,"
            "codigo,"
            "nome,"
            "nome_curto,"
            "status,"
            "observacoes,"
            "logo_url,"
            "site_url"
        )
        .eq(
            "id",
            operator_id,
        )
        .limit(1)
        .execute()
    )

    rows = response.data or []

    if not rows:
        return None

    plans_count = (
        _count_operadora_planos(
            operator_id
        )
    )

    consultant = (
        _get_operadora_consultant(
            operator_id
        )
    )

    return _build_operadora_summary(
        rows[0],
        plans_count=plans_count,
        consultant=consultant,
    )


# =========================================================
# PLANOS DA OPERADORA
# =========================================================


def get_operadora_planos(
    operator_id: str,
) -> pd.DataFrame:
    """
    Retorna os planos vinculados à operadora.

    Mantemos aqui os nomes das colunas usados
    atualmente pela views/operadoras.py para
    evitar alterar a interface nesta etapa.
    """

    if not operator_id:
        return pd.DataFrame()

    response = (
        get_supabase_client()
        .table("planos")
        .select(
            "id,"
            "codigo,"
            "nome,"
            "nome_padronizado,"
            "tipo_plano,"
            "observacao_resumida,"
            "status"
        )
        .eq(
            "operadora_id",
            operator_id,
        )
        .order(
            "nome",
            desc=False,
        )
        .execute()
    )

    rows = response.data or []

    if not rows:
        return pd.DataFrame(
            columns=[
                "ID Plano",
                "Código",
                "Plano",
                "Nome padronizado",
                "Tipo do plano",
                "Unidade",
                "Observação resumida",
                "Status",
            ]
        )

    data = []

    for row in rows:
        data.append(
            {
                "ID Plano": (
                    row.get("id")
                ),
                "Código": (
                    row.get("codigo")
                ),
                "Plano": (
                    row.get("nome")
                ),
                "Nome padronizado": (
                    row.get(
                        "nome_padronizado"
                    )
                ),
                "Tipo do plano": (
                    row.get(
                        "tipo_plano"
                    )
                ),
                "Unidade": "",
                "Observação resumida": (
                    row.get(
                        "observacao_resumida"
                    )
                ),
                "Status": (
                    row.get("status")
                ),
            }
        )

    return pd.DataFrame(
        data
    )


# =========================================================
# MÉTRICAS
# =========================================================


def _count_operadora_planos(
    operator_id: str,
) -> int:
    """
    Conta quantos planos estão ligados
    à operadora.
    """

    if not operator_id:
        return 0

    response = (
        get_supabase_client()
        .table("planos")
        .select(
            "id"
        )
        .eq(
            "operadora_id",
            operator_id,
        )
        .execute()
    )

    return len(
        response.data or []
    )


def _get_operadora_consultant(
    operator_id: str,
) -> str:
    """
    Retorna o consultor principal da operadora,
    quando houver.

    Nesta fase a ausência de consultor não impede
    o funcionamento do módulo.
    """

    if not operator_id:
        return ""

    try:
        response = (
            get_supabase_client()
            .table("consultores")
            .select("*")
            .eq(
                "operadora_id",
                operator_id,
            )
            .limit(1)
            .execute()
        )

        rows = response.data or []

        if not rows:
            return ""

        row = rows[0]

        return (
            _safe_string(
                row.get("nome")
            )
            or _safe_string(
                row.get(
                    "nome_consultor"
                )
            )
        )

    except Exception:
        # Consultor ainda não é obrigatório
        # para esta etapa da migração.
        return ""

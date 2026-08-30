from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.supabase_repository import get_supabase_client


# =========================================================
# MODELO
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
    if value is None:
        return ""

    return str(value).strip()


def _empty_dataframe(
    columns: list[str],
) -> pd.DataFrame:
    return pd.DataFrame(
        columns=columns
    )


def _build_operadora_summary(
    row: dict,
    plans_count: int = 0,
    consultant: str = "",
) -> OperadoraSummary:

    name = _safe_string(
        row.get("nome")
    )

    short_name = (
        _safe_string(
            row.get("nome_curto")
        )
        or name
    )

    return OperadoraSummary(
        operator_id=_safe_string(
            row.get("id")
        ),
        code=_safe_string(
            row.get("codigo")
        ),
        name=name,
        short_name=short_name,
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
            searchable = " ".join(
                [
                    _safe_string(
                        row.get("codigo")
                    ),
                    _safe_string(
                        row.get("nome")
                    ),
                    _safe_string(
                        row.get("nome_curto")
                    ),
                ]
            ).lower()

            if search_term in searchable:
                filtered_rows.append(
                    row
                )

        rows = filtered_rows

    operadoras = []

    for row in rows:
        operator_id = _safe_string(
            row.get("id")
        )

        operadoras.append(
            _build_operadora_summary(
                row,
                plans_count=_count_operadora_planos(
                    operator_id
                ),
                consultant=_get_operadora_consultant(
                    operator_id
                ),
            )
        )

    return operadoras


def get_operadora_by_id(
    operator_id: str,
) -> OperadoraSummary | None:

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

    return _build_operadora_summary(
        rows[0],
        plans_count=_count_operadora_planos(
            operator_id
        ),
        consultant=_get_operadora_consultant(
            operator_id
        ),
    )


# =========================================================
# PLANOS
# =========================================================


def get_operadora_planos(
    operator_id: str,
) -> pd.DataFrame:

    if not operator_id:
        return _empty_dataframe(
            [
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

    data = []

    for row in rows:
        data.append(
            {
                "ID Plano": row.get(
                    "id"
                ),
                "Código": row.get(
                    "codigo"
                ),
                "Plano": row.get(
                    "nome"
                ),
                "Nome padronizado": row.get(
                    "nome_padronizado"
                ),
                "Tipo do plano": row.get(
                    "tipo_plano"
                ),
                "Unidade": "",
                "Observação resumida": row.get(
                    "observacao_resumida"
                ),
                "Status": row.get(
                    "status"
                ),
            }
        )

    return pd.DataFrame(
        data,
        columns=[
            "ID Plano",
            "Código",
            "Plano",
            "Nome padronizado",
            "Tipo do plano",
            "Unidade",
            "Observação resumida",
            "Status",
        ],
    )


# =========================================================
# PORTAIS
# =========================================================


def get_operadora_portais(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "ID Portal",
        "Nome do portal",
        "Tipo",
        "URL",
        "Unidade",
        "Exige login",
        "Instrução de acesso",
        "Status",
        "Observações",
    ]

    if not operator_id:
        return _empty_dataframe(
            columns
        )

    try:
        response = (
            get_supabase_client()
            .table("portais")
            .select(
                "id,"
                "nome,"
                "tipo,"
                "url,"
                "exige_login,"
                "instrucao_acesso,"
                "status,"
                "observacoes"
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

        data = []

        for row in (
            response.data or []
        ):
            data.append(
                {
                    "ID Portal": row.get(
                        "id"
                    ),
                    "Nome do portal": row.get(
                        "nome"
                    ),
                    "Tipo": row.get(
                        "tipo"
                    ),
                    "URL": row.get(
                        "url"
                    ),
                    "Unidade": "",
                    "Exige login": row.get(
                        "exige_login"
                    ),
                    "Instrução de acesso": row.get(
                        "instrucao_acesso"
                    ),
                    "Status": row.get(
                        "status"
                    ),
                    "Observações": row.get(
                        "observacoes"
                    ),
                }
            )

        return pd.DataFrame(
            data,
            columns=columns,
        )

    except Exception:
        return _empty_dataframe(
            columns
        )


# =========================================================
# ELEGIBILIDADE
# =========================================================


def get_operadora_elegibilidade(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "Tipo atendimento",
        "Unidade",
        "Elegível",
        "Documento necessário",
        "Como verificar",
        "Observações",
    ]

    # Migração deste módulo será feita
    # em uma etapa posterior.
    return _empty_dataframe(
        columns
    )


# =========================================================
# DOCUMENTOS
# =========================================================


def get_operadora_documentos(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "Documento",
        "Tipo atendimento",
        "Obrigatório",
        "Validade em dias",
        "Original/Cópia",
        "Observações",
    ]

    return _empty_dataframe(
        columns
    )


# =========================================================
# AUTORIZAÇÕES
# =========================================================


def get_operadora_autorizacoes(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "Tipo atendimento",
        "Necessita autorização",
        "Pré/Pós",
        "Quem solicita",
        "Meio de solicitação",
        "Prazo retorno horas",
        "Observações",
    ]

    return _empty_dataframe(
        columns
    )


# =========================================================
# COBERTURAS
# =========================================================


def get_operadora_coberturas(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "Tipo atendimento",
        "Coberto",
        "Unidade",
        "Acomodação",
        "Acompanhante",
        "Restrição",
        "Observações",
    ]

    return _empty_dataframe(
        columns
    )


# =========================================================
# CONTATOS
# =========================================================


def get_operadora_contatos(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "Finalidade",
        "Tipo",
        "Contato",
        "Responsável",
        "Horário atendimento",
        "Observações",
    ]

    return _empty_dataframe(
        columns
    )


# =========================================================
# CONTINGÊNCIAS
# =========================================================


def get_operadora_contingencias(
    operator_id: str,
) -> pd.DataFrame:

    columns = [
        "Evento",
        "Prioridade",
        "Orientação alternativa",
        "Observações",
    ]

    return _empty_dataframe(
        columns
    )


# =========================================================
# MÉTRICAS AUXILIARES
# =========================================================


def _count_operadora_planos(
    operator_id: str,
) -> int:

    if not operator_id:
        return 0

    try:
        response = (
            get_supabase_client()
            .table("planos")
            .select("id")
            .eq(
                "operadora_id",
                operator_id,
            )
            .execute()
        )

        return len(
            response.data or []
        )

    except Exception:
        return 0


def _get_operadora_consultant(
    operator_id: str,
) -> str:

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
        return ""

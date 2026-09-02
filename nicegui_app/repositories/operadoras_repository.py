from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


OPERADORA_FIELDS = (
    "id,codigo,nome,nome_curto,status,observacoes,logo_url,site_url"
)


def list_operadoras() -> list[dict[str, Any]]:
    return rest_select(
        "operadoras",
        select=OPERADORA_FIELDS,
        params={"order": "nome.asc"},
    )


def get_operadora(operator_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "operadoras",
        select=OPERADORA_FIELDS,
        params={"id": f"eq.{operator_id}", "limit": "1"},
    )
    return rows[0] if rows else None


def _list_by_operadora(
    table: str,
    operator_id: str,
    *,
    order: str | None = None,
) -> list[dict[str, Any]]:
    params = {"operadora_id": f"eq.{operator_id}"}
    if order:
        params["order"] = order
    return rest_select(table, select="*", params=params)


def list_planos_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("planos", operator_id, order="nome.asc")


def list_portais_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("portais", operator_id, order="nome.asc")


def list_elegibilidade_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("elegibilidade", operator_id)


def list_documentos_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("documentos", operator_id)


def list_autorizacoes_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("autorizacoes", operator_id)


def list_coberturas_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("coberturas", operator_id)


def list_contatos_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("contatos", operator_id)


def list_contingencias_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("contingencias", operator_id)


def list_dicas_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("dicas_operacionais", operator_id)


def list_comunicados_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("comunicados", operator_id)


def list_carteiras_by_operadora(operator_id: str) -> list[dict[str, Any]]:
    return _list_by_operadora("carteiras", operator_id)

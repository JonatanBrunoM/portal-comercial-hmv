"""Resumo financeiro mensal e evolução semanal, sem dados de pacientes."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from nicegui_app.data.supabase_client import rest_select
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


def _check_access(access: ParticularAccess) -> None:
    if not access.can_read or not access.profile_id:
        raise ParticularAccessDenied("Sem autorização para consultar o Particular.")


def list_monthly_validation(access: ParticularAccess) -> list[dict[str, Any]]:
    """Consulta a view agregada somente após validar o acesso institucional."""
    _check_access(access)
    rows = rest_select(
        "particular_monthly_validation_summary",
        select=(
            "mes_referencia,orcamentos_importados,valor_bruto_importado,"
            "orcamentos_liberados,valor_liberado_duplicidade,"
            "orcamentos_aguardando_analise,valor_aguardando_analise,"
            "orcamentos_excluidos,valor_excluido_duplicidade,"
            "orcamentos_decisao_incompleta,valor_decisao_incompleta,"
            "orcamentos_transcricao,valor_transcricao,orcamentos_valor_nao_validado"
        ),
        params={"order": "mes_referencia.desc", "limit": "120"},
    )
    return [row for row in rows if isinstance(row, dict)]


def list_weekly_validation(access: ParticularAccess, month: str) -> list[dict[str, Any]]:
    """Consulta as faixas 1–7, 8–14, 15–21, 22–28 e 29–fim do mês."""
    _check_access(access)
    reference = date.fromisoformat(month[:10])
    if reference.day != 1:
        raise ValueError("Mês de referência inválido.")
    rows = rest_select(
        "particular_weekly_validation_summary",
        select=(
            "mes_referencia,semana_mes,orcamentos_importados,valor_bruto_importado,"
            "orcamentos_liberados,valor_liberado_duplicidade,"
            "orcamentos_aguardando_analise,valor_aguardando_analise,"
            "orcamentos_excluidos,valor_excluido_duplicidade,"
            "orcamentos_decisao_incompleta,valor_decisao_incompleta,"
            "orcamentos_transcricao,valor_transcricao,orcamentos_valor_nao_validado"
        ),
        params={"mes_referencia": f"eq.{reference.isoformat()}", "order": "semana_mes.asc", "limit": "5"},
    )
    return [row for row in rows if isinstance(row, dict)]


def format_brl(value: Any) -> str:
    amount = Decimal(str(value if value is not None else "0"))
    formatted = f"{amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def month_label(value: str) -> str:
    month = date.fromisoformat(value[:10])
    names = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    return f"{names[month.month - 1].capitalize()}/{month.year}"

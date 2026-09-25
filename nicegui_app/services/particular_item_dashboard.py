"""Consulta agregada da composição mensal por itens, sem dados de pacientes."""
from __future__ import annotations

from datetime import date
from typing import Any

from nicegui_app.data.supabase_client import rest_select
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


def list_item_monthly(access: ParticularAccess, month: str) -> list[dict[str, Any]]:
    if not access.can_read or not access.profile_id:
        raise ParticularAccessDenied("Sem autorização para consultar o Particular.")

    reference = date.fromisoformat(month[:10])
    if reference.day != 1:
        raise ValueError("Mês de referência inválido.")

    rows = rest_select(
        "particular_item_monthly_summary",
        select=(
            "mes_referencia,codigo,descricao,orcamentos,registros_item,"
            "quantidade,valor_itens,participacao_itens_percentual"
        ),
        params={
            "mes_referencia": f"eq.{reference.isoformat()}",
            "order": "valor_itens.desc",
            "limit": "10000",
        },
    )
    return [row for row in rows if isinstance(row, dict)]

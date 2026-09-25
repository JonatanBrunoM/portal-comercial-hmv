"""Consulta da composição financeira mensal dos orçamentos liberados."""
from __future__ import annotations

from datetime import date
from typing import Any

from nicegui_app.data.supabase_client import rest_select
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


def list_financial_composition(access: ParticularAccess, month: str) -> list[dict[str, Any]]:
    if not access.can_read or not access.profile_id:
        raise ParticularAccessDenied("Sem autorização para consultar o Particular.")

    reference = date.fromisoformat(month[:10])
    if reference.day != 1:
        raise ValueError("Mês de referência inválido.")

    rows = rest_select(
        "particular_financial_composition_monthly",
        select=(
            "mes_referencia,orcamentos_liberados,orcamentos_com_itens,orcamentos_sem_itens,"
            "valor_procedimentos,valor_materiais,valor_total_liberado,valor_itens_detalhados,"
            "participacao_procedimentos_percentual,participacao_materiais_percentual,"
            "cobertura_orcamentos_itens_percentual,cobertura_financeira_itens_percentual"
        ),
        params={"mes_referencia": f"eq.{reference.isoformat()}", "limit": "1"},
    )
    return [row for row in rows if isinstance(row, dict)]

"""Consulta da composição financeira mensal por médico dos orçamentos liberados."""
from __future__ import annotations

from datetime import date
from typing import Any

from nicegui_app.data.supabase_client import rest_select
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


def list_doctor_financial_composition(access: ParticularAccess, month: str) -> list[dict[str, Any]]:
    if not access.can_read or not access.profile_id:
        raise ParticularAccessDenied("Sem autorização para consultar o Particular.")

    reference = date.fromisoformat(month[:10])
    if reference.day != 1:
        raise ValueError("Mês de referência inválido.")

    rows = rest_select(
        "particular_doctor_financial_composition_monthly",
        select=(
            "mes_referencia,medico,orcamentos_liberados,valor_procedimentos,"
            "valor_materiais,valor_total_liberado,participacao_procedimentos_percentual,"
            "participacao_materiais_percentual"
        ),
        params={
            "mes_referencia": f"eq.{reference.isoformat()}",
            "order": "valor_total_liberado.desc",
        },
    )
    return [row for row in rows if isinstance(row, dict)]

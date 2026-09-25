"""Consulta agregada por medico, sem registros individuais de pacientes."""
from __future__ import annotations

from datetime import date
from typing import Any

from nicegui_app.data.supabase_client import rest_select
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


def list_doctor_monthly(access: ParticularAccess, month: str) -> list[dict[str, Any]]:
    if not access.can_read or not access.profile_id:
        raise ParticularAccessDenied('Sem autorização para consultar o Particular.')
    reference = date.fromisoformat(month[:10])
    if reference.day != 1:
        raise ValueError('Mês de referência inválido.')
    rows = rest_select(
        'particular_doctor_monthly_summary',
        select=(
            'mes_referencia,medico,orcamentos_importados,valor_bruto_importado,'
            'orcamentos_liberados,valor_liberado_duplicidade,'
            'orcamentos_aguardando_analise,valor_aguardando_analise,'
            'orcamentos_excluidos,valor_excluido_duplicidade,'
            'orcamentos_decisao_incompleta,valor_decisao_incompleta,'
            'orcamentos_transcricao,valor_transcricao,orcamentos_valor_nao_validado'
        ),
        params={'mes_referencia': f'eq.{reference.isoformat()}', 'order': 'valor_bruto_importado.desc', 'limit': '10000'},
    )
    return [row for row in rows if isinstance(row, dict)]

from __future__ import annotations

from uuid import UUID
from nicegui_app.data.supabase_client import rest_rpc
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied

_ALLOWED = {'PENDING', 'REALIZED', 'NOT_PERFORMED', 'CANCELLED'}


def get_particular_mv_status_batch(*, access: ParticularAccess, budget_ids: list[str]) -> dict[str, str | None]:
    if not access.can_read:
        raise ParticularAccessDenied('Sem autorização para consultar o Particular.')
    if not isinstance(budget_ids, list) or len(budget_ids) > 50:
        raise ValueError('Limite de consulta excedido.')
    ids = [str(UUID(str(value))) for value in budget_ids]
    if len(ids) != len(set(ids)):
        raise ValueError('Orçamentos repetidos.')
    if not ids:
        return {}
    result = rest_rpc('particular_get_mv_status_batch', {'p_profile_id': access.profile_id, 'p_budget_ids': ids}, timeout=30.0)
    if not isinstance(result, dict) or set(result) != set(ids):
        raise RuntimeError('Resposta incompleta da consulta MV.')
    if any(value is not None and value not in _ALLOWED for value in result.values()):
        raise RuntimeError('Resultado MV desconhecido.')
    return result

from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_select


def list_particular_work_queue() -> list[dict[str, Any]]:
    """Carrega a fila inteligente consolidada do Particular.

    A view já concentra as regras de interpretação. Esta camada não reclassifica
    eventos nem infere desfechos: apenas entrega a fotografia para a interface.
    """
    rows = rest_select(
        "particular_work_queue_v1",
        select=(
            "budget_id,budget_number,budget_date,doctor_name,original_requester,"
            "original_value,currency_code,portfolio_origin,has_operational_evidence,"
            "operational_state,current_location,last_observed_operational_date,"
            "first_operational_date,trajectory_event,trajectory_requires_review,"
            "trajectory_review_title,trajectory_review_description,occurrence_count,"
            "operational_date_count,attendance_number,account_status,closure_mode,"
            "account_automation_status,account_review_reason,reference_budget_value,"
            "confirmed_final_value,mv_outcome,mv_account_value,mv_checked_at,"
            "annulment_status,work_group,work_priority,work_action,work_reason"
        ),
        params={"order": "work_priority.asc,budget_date.asc,budget_number.asc"},
        timeout=30.0,
    )
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise RuntimeError("A fila inteligente do Particular retornou formato inválido.")
    return rows

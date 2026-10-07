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



def get_particular_case_dossier(*, budget_id: str) -> dict[str, Any]:
    """Monta o dossiê factual de um orçamento sem inferir novos desfechos."""
    queue = rest_select(
        "particular_work_queue_v1",
        select="*",
        params={"budget_id": f"eq.{budget_id}", "limit": "1"},
        timeout=20.0,
    )
    if not queue:
        raise LookupError("Orçamento não encontrado na fila inteligente.")
    row = queue[0]

    occurrences = rest_select(
        "particular_occurrences",
        select=(
            "id,budget_id,notice_number,procedure_date,location,operational_value,"
            "contact_status,patient_confirmation,evolution_status,notes_original,"
            "occurrence_status,source_row_number,source_row_key,patient_name,doctor_name,"
            "differential,negative_type_value"
        ),
        params={"budget_id": f"eq.{budget_id}", "order": "procedure_date.asc"},
        timeout=20.0,
    )

    events = rest_select(
        "particular_account_events",
        select=(
            "id,evidence_id,attendance_number,event_type,closure_mode,event_at,"
            "confidence,requires_review,review_reason,interpretation_details,created_at"
        ),
        params={"budget_id": f"eq.{budget_id}", "order": "event_at.asc"},
        timeout=20.0,
    )

    attendance = row.get("attendance_number")
    evolutions: list[dict[str, Any]] = []
    if attendance:
        evolutions = rest_select(
            "particular_admin_evolution_evidences",
            select=(
                "id,source_row_number,patient_name_raw,attendance_number,attendance_date,"
                "admin_evolution_code,evolution_recorded_at,user_name,evolution_type,description_raw"
            ),
            params={
                "attendance_number": f"eq.{attendance}",
                "order": "evolution_recorded_at.asc",
            },
            timeout=20.0,
        )

    return {
        "queue": row,
        "occurrences": occurrences,
        "events": events,
        "evolutions": evolutions,
    }

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

    investigation_candidates: list[dict[str, Any]] = []
    if not occurrences and str(row.get("work_group") or "") in {"GRADE_SEM_OPERACAO", "NEGATIVA_SEM_OPERACAO"}:
        identity = rest_select(
            "particular_budget_identity",
            select="patient_name,patient_name_normalized",
            params={"budget_id": f"eq.{budget_id}", "limit": "1"},
            timeout=20.0,
        )
        patient_name = str((identity[0] if identity else {}).get("patient_name") or "").strip()
        if patient_name:
            budget_date = str(row.get("budget_date") or "").strip()
            budget_year = budget_date[:4] if len(budget_date) >= 4 and budget_date[:4].isdigit() else None
            investigation_candidates = rest_select(
                "particular_occurrences",
                select=(
                    "id,budget_id,notice_number,procedure_date,location,operational_value,"
                    "contact_status,patient_confirmation,evolution_status,notes_original,"
                    "occurrence_status,source_row_number,source_row_key,patient_name,doctor_name,"
                    "differential,negative_type_value,budget_reference_raw,budget_reference_status"
                ),
                params={
                    "patient_name": f"ilike.{patient_name}",
                    "order": "procedure_date.asc",
                    "limit": "50",
                },
                timeout=20.0,
            )
            if budget_year:
                investigation_candidates = [
                    item for item in investigation_candidates
                    if str(item.get("procedure_date") or "").startswith(f"{budget_year}-")
                ]

    candidate_budget_cache: dict[str, dict[str, Any]] = {}
    for item in investigation_candidates:
        candidate_budget_id = str(item.get("budget_id") or "").strip()
        if not candidate_budget_id or candidate_budget_id == str(budget_id):
            continue
        if candidate_budget_id not in candidate_budget_cache:
            related_rows = rest_select(
                "particular_work_queue_v1",
                select=(
                    "budget_id,budget_number,budget_date,doctor_name,original_value,"
                    "portfolio_origin,operational_state,attendance_number"
                ),
                params={"budget_id": f"eq.{candidate_budget_id}", "limit": "1"},
                timeout=20.0,
            )
            candidate_budget_cache[candidate_budget_id] = related_rows[0] if related_rows else {}
        related = candidate_budget_cache.get(candidate_budget_id)
        if related:
            item["related_budget"] = related

    # Algumas linhas de grade preservam o número do orçamento na referência bruta
    # mesmo quando o vínculo por budget_id não pôde ser materializado.
    for item in investigation_candidates:
        if item.get("related_budget"):
            continue
        raw_reference = str(item.get("budget_reference_raw") or "").strip()
        digits = "".join(ch for ch in raw_reference if ch.isdigit())
        if not digits:
            continue
        related_rows = rest_select(
            "particular_work_queue_v1",
            select=(
                "budget_id,budget_number,budget_date,doctor_name,original_value,"
                "portfolio_origin,operational_state,attendance_number"
            ),
            params={"budget_number": f"eq.{int(digits)}", "limit": "1"},
            timeout=20.0,
        )
        if related_rows:
            item["related_budget"] = related_rows[0]
        else:
            # A referência da grade é o número do orçamento. Mesmo quando ele não
            # aparece na fila inteligente, recuperamos o UUID canônico para que a
            # investigação possa persistir uma relação auditável.
            budget_rows = rest_select(
                "particular_budgets",
                select="id,budget_number,budget_date,doctor_name,original_requester",
                params={"budget_number": f"eq.{int(digits)}", "limit": "1"},
                timeout=20.0,
            )
            if budget_rows:
                budget_row = budget_rows[0]
                item["related_budget"] = {
                    "budget_id": budget_row.get("id"),
                    "budget_number": budget_row.get("budget_number"),
                    "budget_date": budget_row.get("budget_date"),
                    "doctor_name": budget_row.get("doctor_name"),
                    "original_requester": budget_row.get("original_requester"),
                }
            else:
                item["related_budget"] = {"budget_number": int(digits)}

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
        "investigation_candidates": investigation_candidates,
    }

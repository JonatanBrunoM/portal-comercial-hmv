from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_rpc, rest_select

from dataclasses import dataclass


def _require_uuid(value: str, *, field: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise ValueError(f"{field} é obrigatório.")

    return normalized

@dataclass(frozen=True)
class ParticularBudgetImportResult:
    budget_id: str
    operation: str


def decide_annulment(
    *,
    actor_profile_id: str,
    budget_number: int,
    decision: str,
    reason: str,
) -> dict[str, Any]:
    """Registra a decisão humana sobre uma possível anulação."""

    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    normalized_decision = str(decision or "").strip().upper()
    normalized_reason = str(reason or "").strip()

    if int(budget_number) <= 0:
        raise ValueError("budget_number inválido.")
    if normalized_decision not in {"NORMAL", "CONFIRMED"}:
        raise ValueError("Decisão de anulação inválida.")
    if not normalized_reason:
        raise ValueError("A justificativa da decisão é obrigatória.")
    if len(normalized_reason) > 1000:
        raise ValueError("A justificativa deve possuir no máximo 1000 caracteres.")

    result = rest_rpc(
        "particular_decide_annulment",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_number": int(budget_number),
            "p_decision": normalized_decision,
            "p_reason": normalized_reason,
        },
        timeout=30.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("particular_decide_annulment retornou formato inesperado.")
        result = result[0]

    if not isinstance(result, dict):
        raise RuntimeError("particular_decide_annulment retornou resposta inválida.")

    return result


def annulment_preflight(
    *,
    actor_profile_id: str,
    budget_numbers: list[int],
) -> list[dict[str, Any]]:
    """Consulta o estado persistido de anulação dos orçamentos."""

    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    normalized = sorted({int(value) for value in budget_numbers if int(value) > 0})
    if not normalized:
        return []

    result = rest_rpc(
        "particular_annulment_preflight",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_numbers": normalized,
        },
        timeout=30.0,
    )

    if result is None:
        return []
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        raise RuntimeError("particular_annulment_preflight retornou formato inesperado.")
    return result

def import_preflight(
    *,
    actor_profile_id: str,
    budget_numbers: list[int],
) -> list[dict[str, Any]]:
    """Consulta em lote os orçamentos já existentes antes da importação."""

    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    normalized = sorted({int(value) for value in budget_numbers if int(value) > 0})
    if not normalized:
        return []

    result = rest_rpc(
        "particular_import_preflight",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_numbers": normalized,
        },
        timeout=30.0,
    )

    if result is None:
        return []
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        raise RuntimeError("particular_import_preflight retornou formato inesperado.")
    return result


def import_items_preflight(
    *,
    actor_profile_id: str,
    budget_numbers: list[int],
) -> list[dict[str, Any]]:
    """Consulta em lote os itens ativos dos orçamentos para comparação pré-importação."""

    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    normalized = sorted({int(value) for value in budget_numbers if int(value) > 0})
    if not normalized:
        return []

    result = rest_rpc(
        "particular_import_items_preflight",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_numbers": normalized,
        },
        timeout=30.0,
    )
    if result is None:
        return []
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        raise RuntimeError("particular_import_items_preflight retornou formato inesperado.")
    return result


def start_xml_import(
    *,
    actor_profile_id: str,
    source_filename: str | None,
    file_sha256: str | None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Abre um lote controlado de importação XML do Particular."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )

    result = rest_rpc(
        "particular_start_import",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_source_type": "XML",
            "p_source_filename": (
                str(source_filename).strip()
                if source_filename
                else None
            ),
            "p_file_sha256": (
                str(file_sha256).strip()
                if file_sha256
                else None
            ),
            "p_metadata": metadata or {},
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_start_import não retornou o UUID do lote."
        )

    return result.strip()


def import_xml_budget(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    budget_number: int,
    budget_date: str,
    doctor_name: str | None,
    original_requester: str | None,
    patient_name: str | None,
    patient_name_normalized: str | None = None,
    is_liminar: bool = False,
    is_international: bool = False,
    is_transcription: bool = False,
) -> str:
    """Persiste o núcleo e a identidade protegida de um orçamento XML."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )

    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )

    if int(budget_number) <= 0:
        raise ValueError("budget_number inválido.")

    normalized_date = str(budget_date or "").strip()

    if not normalized_date:
        raise ValueError("budget_date é obrigatório.")

    result = rest_rpc(
        "particular_import_xml_budget",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_budget_number": int(budget_number),
            "p_budget_date": normalized_date,
            "p_doctor_name": doctor_name,
            "p_original_requester": original_requester,
            "p_patient_name": patient_name,
            "p_patient_name_normalized": patient_name_normalized,
            "p_is_liminar": bool(is_liminar),
            "p_is_international": bool(is_international),
            "p_is_transcription": bool(is_transcription),
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_import_xml_budget não retornou o UUID do orçamento."
        )

    return result.strip()

def import_xml_budget_result(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    budget_number: int,
    budget_date: str,
    doctor_name: str | None,
    original_requester: str | None,
    patient_name: str | None,
    patient_name_normalized: str | None = None,
    is_liminar: bool = False,
    is_international: bool = False,
    is_transcription: bool = False,
) -> ParticularBudgetImportResult:
    """Persiste orçamento e informa atomicamente CREATED ou UPDATED."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )

    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )

    if int(budget_number) <= 0:
        raise ValueError("budget_number inválido.")

    normalized_date = str(budget_date or "").strip()

    if not normalized_date:
        raise ValueError("budget_date é obrigatório.")

    result = rest_rpc(
        "particular_import_xml_budget_result",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_budget_number": int(budget_number),
            "p_budget_date": normalized_date,
            "p_doctor_name": doctor_name,
            "p_original_requester": original_requester,
            "p_patient_name": patient_name,
            "p_patient_name_normalized": patient_name_normalized,
            "p_is_liminar": bool(is_liminar),
            "p_is_international": bool(is_international),
            "p_is_transcription": bool(is_transcription),
        },
        timeout=30.0,
    )

    if not isinstance(result, list) or len(result) != 1:
        raise RuntimeError(
            "particular_import_xml_budget_result "
            "retornou formato inesperado."
        )

    row = result[0]

    if not isinstance(row, dict):
        raise RuntimeError(
            "particular_import_xml_budget_result "
            "não retornou um registro válido."
        )

    budget_id = str(row.get("budget_id") or "").strip()
    operation = str(row.get("operation") or "").strip().upper()

    if not budget_id:
        raise RuntimeError(
            "RPC não retornou o UUID do orçamento."
        )

    if operation not in {"CREATED", "UPDATED"}:
        raise RuntimeError(
            "RPC retornou operação de orçamento inválida."
        )

    return ParticularBudgetImportResult(
        budget_id=budget_id,
        operation=operation,
    )

def import_xml_budget_item(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    budget_id: str,
    source_sequence_original: int,
    source_position: int,
    item_code: str,
    description_original: str | None,
    description_normalized: str | None = None,
    quantity: str | None = None,
    unit_value: str | None = None,
    total_value: str | None = None,
    unit: str | None = None,
    item_category: str | None = None,
    technology: str | None = None,
) -> str:
    """Persiste um item do orçamento XML."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )
    budget_id = _require_uuid(
        budget_id,
        field="budget_id",
    )

    item_code = str(item_code or "").strip()

    if not item_code:
        raise ValueError("item_code é obrigatório.")

    if int(source_position) <= 0:
        raise ValueError("source_position inválido.")

    result = rest_rpc(
        "particular_import_xml_budget_item",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_budget_id": budget_id,
            "p_source_sequence_original": int(source_sequence_original),
            "p_source_position": int(source_position),
            "p_item_code": item_code,
            "p_description_original": description_original,
            "p_description_normalized": description_normalized,
            "p_quantity": quantity,
            "p_unit_value": unit_value,
            "p_total_value": total_value,
            "p_unit": unit,
            "p_item_category": item_category,
            "p_technology": technology,
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_import_xml_budget_item não retornou UUID."
        )

    return result.strip()


def finalize_xml_budget_items(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    budget_id: str,
    expected_item_count: int,
) -> int:
    """Finaliza os itens do orçamento e retorna quantos foram desativados."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )
    budget_id = _require_uuid(
        budget_id,
        field="budget_id",
    )

    if int(expected_item_count) < 0:
        raise ValueError("expected_item_count inválido.")

    result = rest_rpc(
        "particular_finalize_xml_budget_items",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_budget_id": budget_id,
            "p_expected_item_count": int(expected_item_count),
        },
        timeout=30.0,
    )

    if isinstance(result, bool) or not isinstance(result, int):
        raise RuntimeError(
            "particular_finalize_xml_budget_items "
            "não retornou a quantidade de itens desativados."
        )

    if result < 0:
        raise RuntimeError(
            "Quantidade inválida de itens desativados."
        )

    return result


def import_xml_original_value(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    budget_id: str,
    procedure_value: str | None,
    material_value: str | None,
    total_value: str | None,
) -> str:
    """Registra o valor ORIGINAL observado no XML."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )
    budget_id = _require_uuid(
        budget_id,
        field="budget_id",
    )

    result = rest_rpc(
        "particular_import_xml_original_value",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_budget_id": budget_id,
            "p_procedure_value": procedure_value,
            "p_material_value": material_value,
            "p_total_value": total_value,
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_import_xml_original_value não retornou UUID."
        )

    return result.strip()


def import_xml_classification(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    budget_id: str,
    dimension: str,
    new_value: str,
    rule_code: str | None = None,
    confidence: str | None = None,
    reason: str | None = None,
) -> str:
    """Registra uma classificação derivada do XML."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )
    budget_id = _require_uuid(
        budget_id,
        field="budget_id",
    )

    dimension = str(dimension or "").strip()
    new_value = str(new_value or "").strip()

    if not dimension:
        raise ValueError("dimension é obrigatória.")

    if not new_value:
        raise ValueError("new_value é obrigatório.")

    result = rest_rpc(
        "particular_import_xml_classification",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_budget_id": budget_id,
            "p_dimension": dimension,
            "p_new_value": new_value,
            "p_rule_code": rule_code,
            "p_confidence": confidence,
            "p_reason": reason,
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_import_xml_classification não retornou UUID."
        )

    return result.strip()


def finish_import(
    *,
    actor_profile_id: str,
    import_batch_id: str,
    status: str,
    records_total: int,
    records_processed: int,
    records_created: int,
    records_updated: int,
    records_error: int,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Finaliza formalmente um lote de importação."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    import_batch_id = _require_uuid(
        import_batch_id,
        field="import_batch_id",
    )

    normalized_status = str(status or "").strip().upper()

    allowed_statuses = {
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
    }

    if normalized_status not in allowed_statuses:
        raise ValueError("status final inválido.")

    counters = {
        "records_total": int(records_total),
        "records_processed": int(records_processed),
        "records_created": int(records_created),
        "records_updated": int(records_updated),
        "records_error": int(records_error),
    }

    if any(value < 0 for value in counters.values()):
        raise ValueError(
            "Contadores da importação não podem ser negativos."
        )

    result = rest_rpc(
        "particular_finish_import",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_import_batch_id": import_batch_id,
            "p_status": normalized_status,
            "p_records_total": counters["records_total"],
            "p_records_processed": counters["records_processed"],
            "p_records_created": counters["records_created"],
            "p_records_updated": counters["records_updated"],
            "p_records_error": counters["records_error"],
            "p_metadata": metadata or {},
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_finish_import não retornou o UUID do lote."
        )

    return result.strip()

def commit_xml_import(
    *,
    actor_profile_id: str,
    source_filename: str,
    file_sha256: str,
    records: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Executa a gravação XML atômica por meio da RPC orquestradora."""

    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    normalized_filename = str(source_filename or "").strip()
    normalized_hash = str(file_sha256 or "").strip().lower()

    if not normalized_filename:
        raise ValueError("source_filename é obrigatório.")
    if len(normalized_hash) != 64:
        raise ValueError("file_sha256 inválido.")
    if not records:
        raise ValueError("Nenhum orçamento foi informado para gravação.")

    result = rest_rpc(
        "particular_commit_xml_import",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_source_filename": normalized_filename,
            "p_file_sha256": normalized_hash,
            "p_records": records,
            "p_metadata": metadata or {},
        },
        timeout=180.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("particular_commit_xml_import retornou formato inesperado.")
        result = result[0]

    if not isinstance(result, dict):
        raise RuntimeError("particular_commit_xml_import retornou resposta inválida.")

    status = str(result.get("status") or "").strip().upper()
    if status not in {"COMPLETED", "FAILED"}:
        raise RuntimeError("particular_commit_xml_import retornou status inválido.")

    return result


def list_relation_reviews(
    *,
    actor_profile_id: str,
) -> list[dict[str, Any]]:
    """Lista a fila segura de revisão de possíveis relações entre orçamentos."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )

    result = rest_rpc(
        "particular_list_relation_reviews",
        {
            "p_profile_id": actor_profile_id,
        },
        timeout=30.0,
    )

    if result is None:
        return []

    if not isinstance(result, list):
        raise RuntimeError(
            "particular_list_relation_reviews retornou formato inesperado."
        )

    if any(not isinstance(row, dict) for row in result):
        raise RuntimeError(
            "particular_list_relation_reviews retornou registro inválido."
        )

    return result


def get_relation_detail(
    *,
    actor_profile_id: str,
    relation_id: str,
) -> dict[str, Any]:
    """Obtém o detalhe autorizado de uma relação específica entre orçamentos."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    relation_id = _require_uuid(
        relation_id,
        field="relation_id",
    )

    result = rest_rpc(
        "particular_get_relation_detail",
        {
            "p_profile_id": actor_profile_id,
            "p_relation_id": relation_id,
        },
        timeout=30.0,
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "particular_get_relation_detail retornou formato inesperado."
        )

    relation = result.get("relation")
    budget_a = result.get("budget_a")
    budget_b = result.get("budget_b")

    if not isinstance(relation, dict):
        raise RuntimeError(
            "Detalhe da relação não contém o bloco relation."
        )

    if not isinstance(budget_a, dict) or not isinstance(budget_b, dict):
        raise RuntimeError(
            "Detalhe da relação não contém os dois orçamentos."
        )

    if str(relation.get("id") or "").strip() != relation_id:
        raise RuntimeError(
            "A RPC retornou uma relação diferente da solicitada."
        )

    if not isinstance(budget_a.get("items"), list):
        raise RuntimeError(
            "Itens do orçamento A retornaram em formato inválido."
        )

    if not isinstance(budget_b.get("items"), list):
        raise RuntimeError(
            "Itens do orçamento B retornaram em formato inválido."
        )

    return result

def get_access_context(
    *,
    actor_profile_id: str,
) -> dict[str, Any]:
    """Retorna o contexto de acesso do perfil ao módulo Particular."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )

    result = rest_rpc(
        "particular_access_context",
        {
            "p_profile_id": actor_profile_id,
        },
        timeout=30.0,
    )

    if result is None:
        raise RuntimeError(
            "O Supabase não retornou o contexto de acesso ao Particular."
        )

    # RPCs RETURNS TABLE normalmente retornam uma lista com uma linha.
    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError(
                "Resposta inesperada ao consultar o acesso ao Particular."
            )
        result = result[0]

    if not isinstance(result, dict):
        raise RuntimeError(
            "Resposta inválida ao consultar o acesso ao Particular."
        )

    return result

def decide_budget_relation(
    *,
    actor_profile_id: str,
    relation_id: str,
    decision: str,
    review_reason: str,
    retained_budget_id: str | None = None,
) -> str:
    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    relation_id = _require_uuid(
        relation_id,
        field="relation_id",
    )

    normalized_decision = str(decision or "").strip().upper()
    normalized_reason = str(review_reason or "").strip()
    normalized_retained_budget_id = (
        _require_uuid(retained_budget_id, field="retained_budget_id")
        if retained_budget_id else None
    )

    if normalized_decision not in {
        "CONFIRMED_DUPLICATE",
        "REBUDGET",
        "DISTINCT",
    }:
        raise ValueError("Decisão de relação inválida.")

    if not normalized_reason:
        raise ValueError("O motivo da decisão é obrigatório.")

    if len(normalized_reason) > 1000:
        raise ValueError(
            "O motivo da decisão deve possuir no máximo 1000 caracteres."
        )

    result = rest_rpc(
        "particular_decide_budget_relation",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_relation_id": relation_id,
            "p_decision": normalized_decision,
            "p_review_reason": normalized_reason,
            "p_retained_budget_id": normalized_retained_budget_id,
        },
        timeout=30.0,
    )

    if result is None:
        raise RuntimeError(
            "A decisão da relação não retornou um identificador."
        )

    return str(result).strip()

def rectify_budget_relation(
    *,
    actor_profile_id: str,
    relation_id: str,
    new_decision: str,
    new_reason: str,
    retained_budget_id: str | None = None,
) -> str:
    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    relation_id = _require_uuid(relation_id, field="relation_id")
    normalized_decision = str(new_decision or "").strip().upper()
    normalized_reason = str(new_reason or "").strip()
    normalized_retained_budget_id = (
        _require_uuid(retained_budget_id, field="retained_budget_id")
        if retained_budget_id else None
    )

    if normalized_decision not in {"CONFIRMED_DUPLICATE", "REBUDGET", "DISTINCT"}:
        raise ValueError("Nova decisão inválida.")
    if not normalized_reason:
        raise ValueError("A justificativa da retificação é obrigatória.")
    if len(normalized_reason) > 1000:
        raise ValueError("A justificativa deve possuir no máximo 1000 caracteres.")

    result = rest_rpc(
        "particular_rectify_budget_relation",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_relation_id": relation_id,
            "p_new_decision": normalized_decision,
            "p_new_reason": normalized_reason,
            "p_retained_budget_id": normalized_retained_budget_id,
        },
        timeout=30.0,
    )
    if not isinstance(result, str) or not result.strip():
        raise RuntimeError("A retificação não retornou um identificador válido.")
    return result.strip()

def register_mv_check(
    *,
    actor_profile_id: str,
    budget_id: str,
    outcome: str,
    occurrence_id: str | None = None,
    notice_number: str | None = None,
    attendance_number: str | None = None,
    account_value: str | None = None,
    notes: str | None = None,
) -> str:
    """Registra uma nova conferência manual no MV."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    budget_id = _require_uuid(
        budget_id,
        field="budget_id",
    )

    normalized_occurrence_id = (
        _require_uuid(occurrence_id, field="occurrence_id")
        if occurrence_id
        else None
    )

    normalized_outcome = str(outcome or "").strip().upper()

    if normalized_outcome not in {
        "PENDING",
        "REALIZED",
        "NOT_PERFORMED",
        "CANCELLED",
    }:
        raise ValueError("Resultado da conferência no MV inválido.")

    normalized_notes = str(notes or "").strip() or None

    if normalized_notes and len(normalized_notes) > 2000:
        raise ValueError(
            "As observações devem possuir no máximo 2000 caracteres."
        )

    result = rest_rpc(
        "particular_register_mv_check",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_id": budget_id,
            "p_occurrence_id": normalized_occurrence_id,
            "p_outcome": normalized_outcome,
            "p_notice_number": (
                str(notice_number).strip() or None
                if notice_number is not None
                else None
            ),
            "p_attendance_number": (
                str(attendance_number).strip() or None
                if attendance_number is not None
                else None
            ),
            "p_account_value": account_value,
            "p_notes": normalized_notes,
        },
        timeout=30.0,
    )

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "O registro da conferência no MV não retornou um identificador válido."
        )

    return result.strip()

def get_mv_check_context(
    *,
    actor_profile_id: str,
    budget_id: str,
) -> dict[str, Any]:
    """Consulta um orçamento e sua última conferência registrada no MV."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )
    budget_id = _require_uuid(
        budget_id,
        field="budget_id",
    )

    result = rest_rpc(
        "particular_get_mv_check_context",
        {
            "p_profile_id": actor_profile_id,
            "p_budget_id": budget_id,
        },
        timeout=30.0,
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "O Supabase retornou dados inválidos para a conferência no MV."
        )

    if not isinstance(result.get("budget"), dict):
        raise RuntimeError(
            "O orçamento não foi retornado na consulta de conferência no MV."
        )

    latest_check = result.get("latest_mv_check")

    if latest_check is not None and not isinstance(latest_check, dict):
        raise RuntimeError(
            "A última conferência no MV possui um formato inválido."
        )

    return result

def list_operational_budgets(
    *,
    actor_profile_id: str,
    budget_number: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Lista orçamentos para a área operacional do Particular."""

    actor_profile_id = _require_uuid(
        actor_profile_id,
        field="actor_profile_id",
    )

    normalized_number = str(budget_number or "").strip() or None

    if normalized_number is not None and not normalized_number.isascii():
        raise ValueError("Informe somente números na busca por orçamento.")

    if normalized_number is not None and not normalized_number.isdecimal():
        raise ValueError("Informe somente números na busca por orçamento.")

    if not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("O limite deve estar entre 1 e 50.")

    if not isinstance(offset, int) or offset < 0:
        raise ValueError("A posição inicial da consulta é inválida.")

    result = rest_rpc(
        "particular_list_operational_budgets",
        {
            "p_profile_id": actor_profile_id,
            "p_budget_number": normalized_number,
            "p_limit": limit,
            "p_offset": offset,
        },
        timeout=30.0,
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "O Supabase retornou uma resposta inválida para a listagem operacional."
        )

    rows = result.get("rows")
    total = result.get("total")

    if not isinstance(rows, list):
        raise RuntimeError(
            "A listagem operacional não retornou uma lista válida de orçamentos."
        )

    if not isinstance(total, int) or total < 0:
        raise RuntimeError(
            "A listagem operacional retornou uma quantidade total inválida."
        )

    return result



def find_resumable_sheet_sync_v3(
    *,
    spreadsheet_id: str,
    preview_sha256: str,
) -> dict[str, Any] | None:
    """Localiza um V3 PROCESSING somente quando pertence à mesma fotografia."""
    normalized_spreadsheet_id = str(spreadsheet_id or "").strip()
    normalized_sha = str(preview_sha256 or "").strip().lower()
    if not normalized_spreadsheet_id:
        raise ValueError("spreadsheet_id é obrigatório.")
    if len(normalized_sha) != 64:
        raise ValueError("preview_sha256 inválido.")

    rows = rest_select(
        "particular_sheet_syncs",
        select="id,spreadsheet_id,status,metadata,created_at",
        params={
            "spreadsheet_id": f"eq.{normalized_spreadsheet_id}",
            "status": "eq.PROCESSING",
            "order": "created_at.desc",
            "limit": "10",
        },
        timeout=30.0,
    )

    matches = []
    for row in rows:
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if str(metadata.get("protocol") or "").strip() != "GRADE_SYNC_V3":
            continue
        if str(metadata.get("preview_sha256") or "").strip().lower() != normalized_sha:
            continue
        matches.append(row)

    if len(matches) > 1:
        raise RuntimeError(
            "Há mais de uma sincronização V3 aberta para a mesma fotografia; revisão manual obrigatória."
        )
    return matches[0] if matches else None


def list_completed_sheet_sync_batches_v3(*, sync_id: str) -> set[int]:
    """Retorna os lotes já confirmados de uma sincronização V3 aberta."""
    sync_id = _require_uuid(sync_id, field="sync_id")
    rows = rest_select(
        "particular_sheet_sync_batches",
        select="batch_number,status",
        params={
            "sync_id": f"eq.{sync_id}",
            "order": "batch_number.asc",
        },
        timeout=30.0,
    )

    failed = [
        int(row["batch_number"])
        for row in rows
        if str(row.get("status") or "").strip().upper() == "FAILED"
    ]
    processing = [
        int(row["batch_number"])
        for row in rows
        if str(row.get("status") or "").strip().upper() == "PROCESSING"
    ]
    if failed or processing:
        raise RuntimeError(
            "A sincronização V3 possui lote incompleto/fracassado; revisão manual obrigatória antes da retomada."
        )

    completed = {
        int(row["batch_number"])
        for row in rows
        if str(row.get("status") or "").strip().upper() == "COMPLETED"
    }
    return completed


def open_sheet_sync_v3(
    *,
    spreadsheet_id: str,
    expected_source_rows: int,
    expected_occurrences: int,
    expected_batches: int,
    sync_mode: str = "MANUAL",
    triggered_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Abre uma sincronização V3 controlada e declara os totais esperados."""
    normalized_spreadsheet_id = str(spreadsheet_id or "").strip()
    normalized_mode = str(sync_mode or "MANUAL").strip().upper()

    if not normalized_spreadsheet_id:
        raise ValueError("spreadsheet_id é obrigatório.")
    if normalized_mode not in {"MANUAL", "ON_OPEN", "SCHEDULED"}:
        raise ValueError("sync_mode inválido.")
    if int(expected_source_rows) <= 0:
        raise ValueError("expected_source_rows deve ser maior que zero.")
    if int(expected_occurrences) <= 0:
        raise ValueError("expected_occurrences deve ser maior que zero.")
    if int(expected_batches) <= 0:
        raise ValueError("expected_batches deve ser maior que zero.")
    if triggered_by is not None:
        triggered_by = _require_uuid(triggered_by, field="triggered_by")

    result = rest_rpc(
        "particular_open_sheet_sync_v3",
        {
            "p_spreadsheet_id": normalized_spreadsheet_id,
            "p_sync_mode": normalized_mode,
            "p_triggered_by": triggered_by,
            "p_expected_source_rows": int(expected_source_rows),
            "p_expected_occurrences": int(expected_occurrences),
            "p_expected_batches": int(expected_batches),
            "p_metadata": metadata or {},
        },
        timeout=30.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("particular_open_sheet_sync_v3 retornou formato inesperado.")
        result = result[0]
    if not isinstance(result, dict) or not str(result.get("sync_id") or "").strip():
        raise RuntimeError("particular_open_sheet_sync_v3 retornou resposta inválida.")
    return result


def commit_sheet_sync_batch_v3(
    *,
    sync_id: str,
    batch_number: int,
    occurrences: list[dict[str, Any]],
    evidences: list[dict[str, Any]],
) -> dict[str, Any]:
    """Grava um lote V3 mantendo ocorrência consolidada e suas evidências juntas."""
    sync_id = _require_uuid(sync_id, field="sync_id")

    if int(batch_number) <= 0:
        raise ValueError("batch_number deve ser maior que zero.")
    if not occurrences:
        raise ValueError("O lote V3 não contém ocorrências.")
    if not evidences:
        raise ValueError("O lote V3 não contém evidências.")

    result = rest_rpc(
        "particular_commit_sheet_sync_batch_v3",
        {
            "p_sync_id": sync_id,
            "p_batch_number": int(batch_number),
            "p_occurrences": occurrences,
            "p_evidences": evidences,
        },
        timeout=120.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError(
                "particular_commit_sheet_sync_batch_v3 retornou formato inesperado."
            )
        result = result[0]
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise RuntimeError(
            "particular_commit_sheet_sync_batch_v3 retornou resposta inválida."
        )
    return result


def finalize_sheet_sync_v3(*, sync_id: str) -> dict[str, Any]:
    """Finaliza o protocolo V3 somente após todos os lotes terem sido confirmados."""
    sync_id = _require_uuid(sync_id, field="sync_id")

    result = rest_rpc(
        "particular_finalize_sheet_sync_v3",
        {"p_sync_id": sync_id},
        timeout=120.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError(
                "particular_finalize_sheet_sync_v3 retornou formato inesperado."
            )
        result = result[0]
    if not isinstance(result, dict):
        raise RuntimeError("particular_finalize_sheet_sync_v3 retornou resposta inválida.")
    if str(result.get("status") or "").strip().upper() != "COMPLETED":
        raise RuntimeError("A sincronização V3 não foi finalizada como COMPLETED.")
    return result


def commit_sheet_sync_v2(
    *,
    spreadsheet_id: str,
    occurrences: list[dict[str, Any]],
    evidences: list[dict[str, Any]],
    sync_mode: str = "MANUAL",
    triggered_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persiste atomicamente ocorrências consolidadas e suas evidências-fonte."""
    normalized_spreadsheet_id = str(spreadsheet_id or "").strip()
    normalized_mode = str(sync_mode or "MANUAL").strip().upper()
    if not normalized_spreadsheet_id:
        raise ValueError("spreadsheet_id é obrigatório.")
    if normalized_mode not in {"MANUAL", "ON_OPEN", "SCHEDULED"}:
        raise ValueError("sync_mode inválido.")
    if not occurrences:
        raise ValueError("Nenhuma ocorrência consolidada foi informada.")
    if not evidences:
        raise ValueError("Nenhuma evidência-fonte foi informada.")
    if triggered_by is not None:
        triggered_by = _require_uuid(triggered_by, field="triggered_by")

    scoped_keys = [
        f'{row.get("source_sheet")}|{str(row.get("source_row_key") or "").strip()}'
        for row in occurrences
    ]
    if any(key.endswith("|") for key in scoped_keys):
        raise ValueError("Há ocorrência consolidada sem source_row_key.")
    if len(scoped_keys) != len(set(scoped_keys)):
        raise ValueError(
            "O payload consolidado ainda contém identidades duplicadas; sincronização bloqueada."
        )

    evidence_positions = [
        (
            str(row.get("source_sheet") or "").strip(),
            row.get("source_row_number"),
        )
        for row in evidences
    ]
    if any(not sheet or row_number in (None, "") for sheet, row_number in evidence_positions):
        raise ValueError("Há evidência sem grade ou número da linha-fonte.")
    if len(evidence_positions) != len(set(evidence_positions)):
        raise ValueError(
            "Há duas evidências ocupando a mesma linha da mesma grade; sincronização bloqueada."
        )

    result = rest_rpc(
        "particular_commit_sheet_sync_v2",
        {
            "p_spreadsheet_id": normalized_spreadsheet_id,
            "p_occurrences": occurrences,
            "p_evidences": evidences,
            "p_sync_mode": normalized_mode,
            "p_triggered_by": triggered_by,
            "p_metadata": metadata or {},
        },
        timeout=300.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("particular_commit_sheet_sync_v2 retornou formato inesperado.")
        result = result[0]
    if not isinstance(result, dict) or not str(result.get("sync_id") or "").strip():
        raise RuntimeError("particular_commit_sheet_sync_v2 retornou resposta inválida.")
    return result


def commit_sheet_sync(
    *,
    spreadsheet_id: str,
    occurrences: list[dict[str, Any]],
    sync_mode: str = "MANUAL",
    triggered_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persiste atomicamente uma fotografia normalizada das três grades."""
    normalized_spreadsheet_id = str(spreadsheet_id or "").strip()
    normalized_mode = str(sync_mode or "MANUAL").strip().upper()
    if not normalized_spreadsheet_id:
        raise ValueError("spreadsheet_id é obrigatório.")
    if normalized_mode not in {"MANUAL", "ON_OPEN", "SCHEDULED"}:
        raise ValueError("sync_mode inválido.")
    if not occurrences:
        raise ValueError("Nenhuma ocorrência foi informada para sincronização.")
    if triggered_by is not None:
        triggered_by = _require_uuid(triggered_by, field="triggered_by")

    scoped_keys = [
        f'{row.get("source_sheet")}|{str(row.get("source_row_key") or "").strip()}'
        for row in occurrences
    ]
    if any(key.endswith("|") for key in scoped_keys):
        raise ValueError("Há ocorrência sem source_row_key.")
    if len(scoped_keys) != len(set(scoped_keys)):
        raise ValueError(
            "A fotografia contém identidades operacionais duplicadas; sincronização bloqueada."
        )

    result = rest_rpc(
        "particular_commit_sheet_sync",
        {
            "p_spreadsheet_id": normalized_spreadsheet_id,
            "p_occurrences": occurrences,
            "p_sync_mode": normalized_mode,
            "p_triggered_by": triggered_by,
            "p_metadata": metadata or {},
        },
        timeout=180.0,
    )

    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("particular_commit_sheet_sync retornou formato inesperado.")
        result = result[0]
    if not isinstance(result, dict) or not str(result.get("sync_id") or "").strip():
        raise RuntimeError("particular_commit_sheet_sync retornou resposta inválida.")
    return result



def commit_admin_evolution_import(*, actor_profile_id: str, source_filename: str, file_sha256: str, reference_month: str | None, records: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Persiste atomicamente as evidencias do relatorio administrativo."""
    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    filename = str(source_filename or "").strip()
    digest = str(file_sha256 or "").strip().lower()
    if not filename:
        raise ValueError("source_filename e obrigatorio.")
    if len(digest) != 64:
        raise ValueError("file_sha256 invalido.")
    if not records:
        raise ValueError("Nenhuma evolucao administrativa foi informada.")
    result = rest_rpc("particular_commit_admin_evolution_import", {"p_actor_profile_id": actor_profile_id, "p_source_filename": filename, "p_file_sha256": digest, "p_reference_month": reference_month, "p_records": records, "p_metadata": metadata or {}}, timeout=180.0)
    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("RPC de evolucao administrativa retornou formato inesperado.")
        result = result[0]
    if not isinstance(result, dict) or result.get("ok") is not True or str(result.get("status") or "").upper() != "COMPLETED":
        raise RuntimeError("A importacao administrativa nao foi concluida corretamente.")
    return result



def resolve_investigation(*, actor_profile_id: str, budget_id: str, related_budget_id: str | None, related_budget_number: int | None, outcome: str, change_dimensions: list[str] | None, resolution_notes: str, evidence: dict[str, Any] | None = None) -> str:
    """Persiste a conclusão operacional, inclusive com referência ainda não importada."""
    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    budget_id = _require_uuid(budget_id, field="budget_id")
    result = rest_rpc("particular_resolve_investigation", {"p_actor_profile_id": actor_profile_id, "p_budget_id": budget_id, "p_related_budget_id": str(related_budget_id).strip() if related_budget_id else None, "p_related_budget_number": int(related_budget_number) if related_budget_number is not None else None, "p_outcome": str(outcome or "").strip().upper(), "p_change_dimensions": change_dimensions or [], "p_resolution_notes": str(resolution_notes or "").strip(), "p_evidence": evidence or {}}, timeout=30.0)
    if not isinstance(result, str) or not result.strip():
        raise RuntimeError("particular_resolve_investigation não retornou um identificador válido.")
    return result.strip()

def register_investigation_relation(
    *,
    actor_profile_id: str,
    budget_id: str,
    related_budget_id: str,
    evidence: dict[str, Any] | None = None,
) -> str:
    """Registra ou recupera uma relação descoberta durante investigação operacional."""
    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    budget_id = _require_uuid(budget_id, field="budget_id")
    related_budget_id = _require_uuid(related_budget_id, field="related_budget_id")

    if budget_id == related_budget_id:
        raise ValueError("O orçamento relacionado deve ser diferente do orçamento investigado.")

    result = rest_rpc(
        "particular_register_investigation_relation",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_id": budget_id,
            "p_related_budget_id": related_budget_id,
            "p_evidence": evidence or {},
        },
        timeout=30.0,
    )
    if not isinstance(result, str) or not result.strip():
        raise RuntimeError(
            "particular_register_investigation_relation não retornou um identificador válido."
        )
    return result.strip()

def resolve_account_review(
    *,
    actor_profile_id: str,
    budget_id: str,
    account_status: str,
    closure_mode: str | None = None,
    confirmed_final_value: str | None = None,
    resolution_notes: str,
) -> dict[str, Any]:
    """Persiste uma resolução humana auditada para uma revisão de conta."""
    actor_profile_id = _require_uuid(actor_profile_id, field="actor_profile_id")
    budget_id = _require_uuid(budget_id, field="budget_id")

    result = rest_rpc(
        "particular_resolve_account_review",
        {
            "p_actor_profile_id": actor_profile_id,
            "p_budget_id": budget_id,
            "p_account_status": account_status,
            "p_closure_mode": closure_mode,
            "p_confirmed_final_value": confirmed_final_value,
            "p_resolution_notes": resolution_notes,
        },
        timeout=30.0,
    )
    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            raise RuntimeError("particular_resolve_account_review retornou formato inesperado.")
        result = result[0]
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise RuntimeError("A revisão da conta não foi concluída corretamente.")
    return result

def commit_mv_account_import(*, source_filename: str, file_sha256: str, records: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Grava um lote MV completo via RPC atomica, sem alterar estados de contas."""
    result = rest_rpc(
        "particular_commit_mv_account_import",
        {
            "p_source_filename": source_filename,
            "p_file_sha256": file_sha256,
            "p_records": records,
            "p_metadata": metadata or {},
        },
        timeout=180.0,
    )
    if not isinstance(result, dict):
        raise RuntimeError("Resposta inesperada da importacao MV.")
    return result


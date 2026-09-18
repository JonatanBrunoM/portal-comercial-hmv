from __future__ import annotations

from typing import Any

from nicegui_app.data.supabase_client import rest_rpc

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
        },
        timeout=30.0,
    )

    if result is None:
        raise RuntimeError(
            "A decisão da relação não retornou um identificador."
        )

    return str(result).strip()
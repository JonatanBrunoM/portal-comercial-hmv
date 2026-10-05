from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.particular_repository import (
    decide_budget_relation,
    get_access_context,
    get_relation_detail,
    list_relation_reviews,
    rectify_budget_relation,
    register_mv_check,
    get_mv_check_context,
    list_operational_budgets,
    import_preflight,
    import_items_preflight,
    annulment_preflight,
    decide_annulment,
    commit_xml_import,
    commit_admin_evolution_import,
    resolve_account_review,
)

class ParticularAccessDenied(PermissionError):
    """Usuário autenticado, porém sem autorização para o módulo Particular."""


@dataclass(frozen=True, slots=True)
class ParticularAccess:
    profile_id: str
    profile_name: str
    profile_email: str
    module_role: str
    can_read: bool
    can_write: bool
    can_manage_access: bool


@dataclass(frozen=True, slots=True)
class ParticularContext:
    access: ParticularAccess
    relation_reviews: tuple[dict[str, Any], ...]


def _session_text(user: dict[str, Any], key: str) -> str:
    value = user.get(key)
    return str(value or "").strip()


def resolve_particular_access(user: dict[str, Any]) -> ParticularAccess:
    """
    Resolve o acesso ao módulo Particular a partir do profile_id
    previamente validado e armazenado na sessão institucional.

    O profile_id é definido pelo backend durante o login Google e não
    é recebido da interface como fonte de confiança.
    """
    profile_id = _session_text(user, "profile_id")

    if not profile_id:
        raise ParticularAccessDenied(
            "A sessão autenticada não possui perfil institucional válido."
        )

    context = get_access_context(
        actor_profile_id=profile_id,
    )

    if context.get("profile_active") is not True:
        raise ParticularAccessDenied(
            "O perfil institucional não está ativo."
        )

    can_read = context.get("can_read") is True
    can_write = context.get("can_write") is True

    if not can_read:
        raise ParticularAccessDenied(
            "Seu perfil não possui acesso ao módulo Particular."
        )

    return ParticularAccess(
        profile_id=profile_id,
        profile_name=str(
            context.get("profile_name")
            or _session_text(user, "name")
        ).strip(),
        profile_email=str(
            context.get("profile_email")
            or _session_text(user, "email")
        ).strip(),
        module_role=str(
            context.get("particular_role") or ""
        ).strip(),
        can_read=True,
        can_write=can_write,
        can_manage_access=context.get("can_manage_access") is True,
    )


def get_particular_context(
    *,
    access: ParticularAccess,
) -> ParticularContext:
    """Carrega a fila operacional usando um acesso previamente validado."""

    if not access.can_read:
        raise ParticularAccessDenied(
            "Seu perfil não possui acesso de leitura ao módulo Particular."
        )

    rows = list_relation_reviews(
        actor_profile_id=access.profile_id,
    )

    return ParticularContext(
        access=access,
        relation_reviews=tuple(rows),
    )


def get_particular_relation_detail(
    *,
    access: ParticularAccess,
    relation_id: str,
) -> dict[str, Any]:
    """Abre uma relação específica para comparação dos dois orçamentos."""

    if not access.can_read:
        raise ParticularAccessDenied(
            "Seu perfil não possui acesso de leitura ao módulo Particular."
        )

    return get_relation_detail(
        actor_profile_id=access.profile_id,
        relation_id=relation_id,
    )

def decide_particular_relation(
    *,
    access: ParticularAccess,
    relation_id: str,
    decision: str,
    review_reason: str,
    retained_budget_id: str | None = None,
) -> str:
    """Registra a decisão humana sobre uma possível relação entre orçamentos."""

    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil não possui permissão para decidir relações no módulo Particular."
        )

    normalized_relation_id = str(relation_id or "").strip()
    normalized_decision = str(decision or "").strip().upper()
    normalized_reason = str(review_reason or "").strip()
    normalized_retained_budget_id = str(retained_budget_id or "").strip() or None

    if not normalized_relation_id:
        raise ValueError("A relação é obrigatória.")

    if normalized_decision not in {
        "CONFIRMED_DUPLICATE",
        "REBUDGET",
        "DISTINCT",
    }:
        raise ValueError("Decisão inválida.")

    if not normalized_reason:
        raise ValueError("A justificativa da decisão é obrigatória.")

    if len(normalized_reason) > 1000:
        raise ValueError(
            "A justificativa deve possuir no máximo 1000 caracteres."
        )

    return decide_budget_relation(
        actor_profile_id=access.profile_id,
        relation_id=normalized_relation_id,
        decision=normalized_decision,
        review_reason=normalized_reason,
        retained_budget_id=normalized_retained_budget_id,
    )

def rectify_particular_relation(
    *,
    access: ParticularAccess,
    relation_id: str,
    new_decision: str,
    new_reason: str,
    retained_budget_id: str | None = None,
) -> str:
    """Retifica uma decisão final por meio da RPC auditada e restrita."""
    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil não possui permissão para retificar relações no módulo Particular."
        )

    normalized_relation_id = str(relation_id or "").strip()
    normalized_decision = str(new_decision or "").strip().upper()
    normalized_reason = str(new_reason or "").strip()
    normalized_retained_budget_id = str(retained_budget_id or "").strip() or None

    if not normalized_relation_id:
        raise ValueError("A relação é obrigatória.")
    if normalized_decision not in {"CONFIRMED_DUPLICATE", "REBUDGET", "DISTINCT"}:
        raise ValueError("Nova decisão inválida.")
    if not normalized_reason:
        raise ValueError("A justificativa da retificação é obrigatória.")
    if len(normalized_reason) > 1000:
        raise ValueError("A justificativa deve possuir no máximo 1000 caracteres.")

    return rectify_budget_relation(
        actor_profile_id=access.profile_id,
        relation_id=normalized_relation_id,
        new_decision=normalized_decision,
        new_reason=normalized_reason,
        retained_budget_id=normalized_retained_budget_id,
    )

def register_particular_mv_check(
    *,
    access: ParticularAccess,
    budget_id: str,
    outcome: str,
    occurrence_id: str | None = None,
    notice_number: str | None = None,
    attendance_number: str | None = None,
    account_value: str | None = None,
    notes: str | None = None,
) -> str:
    """Registra uma nova conferência manual no MV."""

    if not access.can_write or access.module_role.upper() != "MANAGER":
        raise ParticularAccessDenied(
            "Somente gestores do Particular podem registrar conferências no MV."
        )

    normalized_budget_id = str(budget_id or "").strip()

    if not normalized_budget_id:
        raise ValueError("O orçamento é obrigatório.")

    normalized_outcome = str(outcome or "").strip().upper()

    if normalized_outcome not in {
        "PENDING",
        "REALIZED",
        "NOT_PERFORMED",
        "CANCELLED",
    }:
        raise ValueError("Resultado da conferência no MV inválido.")

    return register_mv_check(
        actor_profile_id=access.profile_id,
        budget_id=normalized_budget_id,
        occurrence_id=occurrence_id,
        outcome=normalized_outcome,
        notice_number=notice_number,
        attendance_number=attendance_number,
        account_value=account_value,
        notes=notes,
    )

def get_particular_mv_check_context(
    *,
    access: ParticularAccess,
    budget_id: str,
) -> dict[str, Any]:
    """Consulta o orçamento e sua última conferência registrada no MV."""

    if not access.can_read:
        raise ParticularAccessDenied(
            "Seu perfil não possui autorização para consultar o módulo Particular."
        )

    normalized_budget_id = str(budget_id or "").strip()

    if not normalized_budget_id:
        raise ValueError("O orçamento é obrigatório.")

    return get_mv_check_context(
        actor_profile_id=access.profile_id,
        budget_id=normalized_budget_id,
    )

def list_particular_operational_budgets(
    *,
    access: ParticularAccess,
    budget_number: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Lista os orçamentos disponíveis na área operacional."""

    if not access.can_read:
        raise ParticularAccessDenied(
            "Seu perfil não possui autorização para consultar o módulo Particular."
        )

    return list_operational_budgets(
        actor_profile_id=access.profile_id,
        budget_number=budget_number,
        limit=limit,
        offset=offset,
    )



def decide_particular_annulment(
    *,
    access: ParticularAccess,
    budget_number: int,
    decision: str,
    reason: str,
) -> dict[str, Any]:
    """Resolve humanamente um candidato de possível anulação."""

    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil não possui permissão para decidir anulações no módulo Particular."
        )

    normalized_decision = str(decision or "").strip().upper()
    normalized_reason = str(reason or "").strip()

    if int(budget_number) <= 0:
        raise ValueError("O orçamento é obrigatório.")
    if normalized_decision not in {"NORMAL", "CONFIRMED"}:
        raise ValueError("Decisão de anulação inválida.")
    if not normalized_reason:
        raise ValueError("A justificativa da decisão é obrigatória.")
    if len(normalized_reason) > 1000:
        raise ValueError("A justificativa deve possuir no máximo 1000 caracteres.")

    return decide_annulment(
        actor_profile_id=access.profile_id,
        budget_number=int(budget_number),
        decision=normalized_decision,
        reason=normalized_reason,
    )

def commit_particular_xml_import(
    *,
    access: ParticularAccess,
    validated_report: dict[str, Any],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    """Grava um HMV2670 validado por uma única transação no Supabase."""

    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil não possui permissão para importar dados no módulo Particular."
        )
    if validated_report.get("source_format") != "XML":
        raise ValueError("A gravação real está habilitada somente para o HMV2670 original em XML.")
    if not validated_report.get("valid_for_import"):
        raise ValueError("O arquivo não passou pela pré-validação.")
    if not preflight.get("safe_to_import"):
        raise ValueError("A gravação está bloqueada por conflitos com a base atual.")
    if int(preflight.get("annulment_pending_count") or 0) > 0:
        raise ValueError("Existem possíveis anulações pendentes de decisão operacional.")

    records = validated_report.get("budget_records")
    if not isinstance(records, list) or not records:
        raise ValueError("Nenhum orçamento válido foi encontrado no arquivo.")

    from datetime import datetime
    from decimal import Decimal, InvalidOperation
    import unicodedata

    def normalized_text(value: Any) -> str | None:
        raw = " ".join(str(value or "").strip().split())
        if not raw:
            return None
        decomposed = unicodedata.normalize("NFKD", raw.upper())
        return "".join(ch for ch in decomposed if not unicodedata.combining(ch))

    def iso_date(value: Any) -> str:
        raw = str(value or "").strip()
        for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw[:10], fmt).date().isoformat()
            except ValueError:
                continue
        raise ValueError(f"Data inválida na preparação da gravação: {value!r}")

    def numeric_source(value: Any) -> str | None:
        # Para persistência, vazio continua NULL. Zero só é gravado quando o
        # próprio HMV2670 efetivamente informa zero.
        if value is None or str(value).strip() == "":
            return None
        raw = str(value).strip()
        if "," in raw:
            raw = raw.replace(".", "").replace(",", ".")
        try:
            return str(Decimal(raw))
        except InvalidOperation as exc:
            raise ValueError(f"Valor numérico inválido na preparação da gravação: {value!r}") from exc

    payload: list[dict[str, Any]] = []
    for record in records:
        budget_number = int(str(record.get("SEQ_ORCAMENTO") or "").strip())
        doctor_name = str(record.get("NOME_MEDICO") or "").strip() or None
        patient_name = str(record.get("NOME_PACIENTE") or "").strip() or None
        requester = str(record.get("SOLICITANTE") or "").strip() or None
        doctor_marker = normalized_text(doctor_name) or ""

        items_payload: list[dict[str, Any]] = []
        for fallback_position, item in enumerate(record.get("ITEMS") or [], start=1):
            source_sequence = str(item.get("source_sequence_original") or "").strip()
            item_code = str(item.get("item_code") or "").strip()
            description = str(item.get("description") or "").strip()
            if not source_sequence or not item_code or not description:
                raise ValueError(
                    f"Orçamento {budget_number} possui item sem identidade completa."
                )

            items_payload.append({
                "source_sequence_original": int(source_sequence),
                "source_position": int(item.get("source_position") or fallback_position),
                "item_code": item_code,
                "description_original": description,
                "description_normalized": normalized_text(description),
                "quantity": numeric_source(item.get("quantity")),
                "unit_value": numeric_source(item.get("unit_value")),
                "total_value": numeric_source(item.get("total_value")),
                "unit": str(item.get("unit") or "").strip() or None,
            })

        payload.append({
            "budget_number": budget_number,
            "budget_date": iso_date(record.get("DATA")),
            "doctor_name": doctor_name,
            "original_requester": requester,
            "patient_name": patient_name,
            "patient_name_normalized": normalized_text(patient_name),
            "is_liminar": False,
            "is_international": False,
            "is_transcription": "CONSULTORIO" in doctor_marker,
            "procedure_value": numeric_source(record.get("VALOR")),
            "material_value": numeric_source(record.get("VALOR_MATERIAL_ESPECIAL")),
            "total_value": numeric_source(record.get("VALOR_TOTAL")),
            "items": items_payload,
        })

    metadata = {
        "portal_import_version": "HMV2670_ATOMIC_V1",
        "competence": validated_report.get("competence"),
        "start_date": validated_report.get("start_date"),
        "end_date": validated_report.get("end_date"),
        "coverage_type": validated_report.get("coverage_type"),
        "source_label": validated_report.get("source_label"),
        "preflight_new_count": int(preflight.get("new_count") or 0),
        "preflight_identical_count": int(preflight.get("identical_count") or 0),
        "preflight_changed_count": int(preflight.get("changed_count") or 0),
        "preflight_conflict_count": int(preflight.get("conflict_count") or 0),
        "annulled_confirmed_count": int(preflight.get("annulled_count") or 0),
        "raw_total_value": preflight.get("raw_total_value"),
        "effective_total_value": preflight.get("effective_total_value"),
    }

    result = commit_xml_import(
        actor_profile_id=access.profile_id,
        source_filename=str(validated_report.get("filename") or "HMV2670.xml"),
        file_sha256=str(validated_report.get("sha256") or ""),
        records=payload,
        metadata=metadata,
    )

    if str(result.get("status") or "").upper() == "FAILED":
        raise RuntimeError(
            str(result.get("error") or "A transação de importação foi revertida pelo banco.")
        )

    return result


def preflight_particular_import(
    *,
    access: ParticularAccess,
    validated_report: dict[str, Any],
) -> dict[str, Any]:
    """Compara deterministicamente o arquivo validado com a base atual."""

    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil não possui permissão para importar dados no módulo Particular."
        )

    records = validated_report.get("budget_records")
    if not validated_report.get("valid_for_import") or not isinstance(records, list):
        raise ValueError("O relatório precisa passar pela pré-validação antes do preflight.")

    from decimal import Decimal, InvalidOperation

    def dec(value: Any) -> Decimal:
        """Converte valores financeiros do XML/Banco sem perder formato pt-BR.

        Oracle Reports entrega números como 6053,6 e ,01; o Supabase devolve
        representação decimal com ponto. Ambos precisam resultar no mesmo Decimal.
        """
        if value is None or str(value).strip() == "":
            return Decimal("0")

        raw = str(value).strip()
        if "," in raw:
            raw = raw.replace(".", "").replace(",", ".")

        try:
            return Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError(f"Valor financeiro inválido no preflight: {value!r}") from exc

    def norm_marker(value: Any) -> str:
        import unicodedata

        raw = unicodedata.normalize("NFKD", str(value or "").strip().upper())
        return "".join(ch for ch in raw if not unicodedata.combining(ch))

    def row_is_annulled(row: dict[str, Any] | None) -> bool:
        if not row:
            return False
        if row.get("IS_ANNULLED") is True or row.get("is_annulled") is True:
            return True
        for key in ("status", "budget_status", "operational_status", "status_operacional", "classification"):
            if norm_marker(row.get(key)) == "ANULADO":
                return True
        return False

    def date_text(value: Any) -> str:
        """Normaliza datas do XML (DD/MM/YY ou DD/MM/YYYY) e do banco (YYYY-MM-DD)."""
        from datetime import date as date_type, datetime as datetime_type

        if isinstance(value, datetime_type):
            return value.date().isoformat()
        if isinstance(value, date_type):
            return value.isoformat()

        raw = str(value or "").strip()
        if not raw:
            return ""

        for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime_type.strptime(raw[:10], fmt).date().isoformat()
            except ValueError:
                continue

        return raw[:10]

    file_by_number: dict[int, dict[str, Any]] = {}
    for row in records:
        number = int(str(row.get("SEQ_ORCAMENTO") or "").strip())
        file_by_number[number] = row

    existing_rows = import_preflight(
        actor_profile_id=access.profile_id,
        budget_numbers=list(file_by_number),
    )
    existing_by_number = {
        int(row["budget_number"]): row
        for row in existing_rows
        if row.get("budget_number") is not None
    }

    candidate_numbers = [
        int(candidate.get("budget_number"))
        for candidate in validated_report.get("annulment_candidates", [])
        if candidate.get("budget_number") is not None
    ]
    # O estado persistido precisa ser consultado para TODOS os orçamentos do
    # arquivo, não apenas para os que o XML atual voltou a sinalizar. Assim uma
    # anulação já confirmada continua valendo em reimportações futuras.
    annulment_rows = annulment_preflight(
        actor_profile_id=access.profile_id,
        budget_numbers=list(file_by_number),
    )
    annulment_by_number = {
        int(row["budget_number"]): row
        for row in annulment_rows
        if row.get("budget_number") is not None
    }

    annulment_reviews: dict[int, dict[str, Any]] = {}
    for number in candidate_numbers:
        persisted = annulment_by_number.get(number)
        status = str((persisted or {}).get("annulment_status") or "").strip().upper()
        reason = str((persisted or {}).get("annulment_reason") or "").strip()

        if status == "CONFIRMED":
            review_state = "CONFIRMED"
        elif status == "NORMAL" and reason:
            review_state = "NORMAL_REVIEWED"
        else:
            review_state = "PENDING"

        annulment_reviews[number] = {
            "review_state": review_state,
            "annulment_status": status or "NORMAL",
            "reason": reason or None,
            "confirmed_at": (persisted or {}).get("annulment_confirmed_at"),
            "confirmed_by": (persisted or {}).get("annulment_confirmed_by"),
        }

    new_numbers: list[int] = []
    identical_numbers: list[int] = []
    changed_numbers: list[int] = []
    conflict_numbers: list[int] = []
    annulled_numbers: list[int] = []
    annulled_sources: dict[int, str] = {}
    new_value = Decimal("0")
    changed_value = Decimal("0")
    raw_procedure_value = Decimal("0")
    raw_material_value = Decimal("0")
    raw_total_value = Decimal("0")
    annulled_procedure_value = Decimal("0")
    annulled_material_value = Decimal("0")
    annulled_value = Decimal("0")

    for number, incoming in file_by_number.items():
        current = existing_by_number.get(number)
        incoming_procedure = dec(incoming.get("VALOR"))
        incoming_material = dec(incoming.get("VALOR_MATERIAL_ESPECIAL"))
        incoming_total = dec(incoming.get("VALOR_TOTAL"))

        raw_procedure_value += incoming_procedure
        raw_material_value += incoming_material
        raw_total_value += incoming_total

        # O HMV2670 não possui um status ANULADO confiável. Sinais do arquivo
        # nunca excluem valor automaticamente; somente a decisão humana
        # persistida como CONFIRMED pode zerar a contribuição gerencial.
        persisted_annulment = annulment_by_number.get(number) or {}
        database_annulled = (
            str(persisted_annulment.get("annulment_status") or "").strip().upper()
            == "CONFIRMED"
        )
        if database_annulled:
            annulled_numbers.append(number)
            annulled_sources[number] = "BASE_CONFIRMADA"
            annulled_procedure_value += incoming_procedure
            annulled_material_value += incoming_material
            annulled_value += incoming_total
        if current is None:
            new_numbers.append(number)
            new_value += incoming_total
            continue

        current_total = dec(current.get("total_value"))
        same_date = date_text(incoming.get("DATA")) == date_text(current.get("budget_date"))
        same_values = (
            dec(incoming.get("VALOR")) == dec(current.get("procedure_value"))
            and dec(incoming.get("VALOR_MATERIAL_ESPECIAL")) == dec(current.get("material_value"))
            and incoming_total == current_total
        )

        if same_date and same_values:
            identical_numbers.append(number)
        elif same_date:
            changed_numbers.append(number)
            changed_value += incoming_total - current_total
        else:
            conflict_numbers.append(number)

    changed_details: list[dict[str, Any]] = []
    for number in changed_numbers:
        incoming = file_by_number[number]
        current = existing_by_number[number]
        old_procedure = dec(current.get("procedure_value"))
        old_material = dec(current.get("material_value"))
        old_total = dec(current.get("total_value"))
        new_procedure = dec(incoming.get("VALOR"))
        new_material = dec(incoming.get("VALOR_MATERIAL_ESPECIAL"))
        new_total = dec(incoming.get("VALOR_TOTAL"))
        changed_details.append({
            "budget_number": number,
            "budget_date": date_text(incoming.get("DATA")),
            "old_procedure": str(old_procedure),
            "new_procedure": str(new_procedure),
            "diff_procedure": str(new_procedure - old_procedure),
            "old_material": str(old_material),
            "new_material": str(new_material),
            "diff_material": str(new_material - old_material),
            "old_total": str(old_total),
            "new_total": str(new_total),
            "diff_total": str(new_total - old_total),
        })

    item_comparison: dict[int, dict[str, Any]] = {}
    if changed_numbers:
        db_item_rows = import_items_preflight(
            actor_profile_id=access.profile_id,
            budget_numbers=changed_numbers,
        )
        db_items_by_budget: dict[int, list[dict[str, Any]]] = {}
        for row in db_item_rows:
            db_items_by_budget.setdefault(int(row["budget_number"]), []).append(row)

        def norm_text(value: Any) -> str:
            import unicodedata
            raw = unicodedata.normalize("NFKD", str(value or "").strip().upper())
            return "".join(ch for ch in raw if not unicodedata.combining(ch))

        def item_key(row: dict[str, Any]) -> tuple[str, str]:
            code = str(row.get("item_code") or row.get("CD_ITEM") or "").strip()
            desc = norm_text(row.get("description_original") or row.get("description") or row.get("DS_ITEM"))
            return code, desc

        for number in changed_numbers:
            incoming_items = file_by_number[number].get("ITEMS") or []
            current_items = db_items_by_budget.get(number, [])
            incoming_map = {item_key(row): row for row in incoming_items}
            current_map = {item_key(row): row for row in current_items}
            added: list[dict[str, Any]] = []
            removed: list[dict[str, Any]] = []
            modified: list[dict[str, Any]] = []

            for key in sorted(incoming_map.keys() - current_map.keys()):
                row = incoming_map[key]
                added.append({
                    "item_code": key[0],
                    "description": row.get("description") or "",
                    "quantity": str(dec(row.get("quantity"))),
                    "unit_value": str(dec(row.get("unit_value"))),
                    "total_value": str(dec(row.get("total_value"))),
                })

            for key in sorted(current_map.keys() - incoming_map.keys()):
                row = current_map[key]
                removed.append({
                    "item_code": key[0],
                    "description": row.get("description_original") or "",
                    "quantity": str(dec(row.get("quantity"))),
                    "unit_value": str(dec(row.get("unit_value"))),
                    "total_value": str(dec(row.get("total_value"))),
                })

            for key in sorted(incoming_map.keys() & current_map.keys()):
                new = incoming_map[key]
                old = current_map[key]
                changes: list[str] = []
                if dec(new.get("quantity")) != dec(old.get("quantity")):
                    changes.append("QUANTIDADE")
                if dec(new.get("unit_value")) != dec(old.get("unit_value")):
                    changes.append("VALOR_UNITARIO")
                if dec(new.get("total_value")) != dec(old.get("total_value")):
                    changes.append("VALOR_TOTAL")
                if changes:
                    modified.append({
                        "item_code": key[0],
                        "description": new.get("description") or old.get("description_original") or "",
                        "changes": changes,
                        "old_quantity": str(dec(old.get("quantity"))),
                        "new_quantity": str(dec(new.get("quantity"))),
                        "old_unit_value": str(dec(old.get("unit_value"))),
                        "new_unit_value": str(dec(new.get("unit_value"))),
                        "old_total_value": str(dec(old.get("total_value"))),
                        "new_total_value": str(dec(new.get("total_value"))),
                    })

            item_delta = sum(
                (dec(row.get("total_value")) for row in added),
                Decimal("0"),
            ) - sum(
                (dec(row.get("total_value")) for row in removed),
                Decimal("0"),
            )
            for row in modified:
                item_delta += dec(row.get("new_total_value")) - dec(row.get("old_total_value"))

            financial_detail = next(
                (row for row in changed_details if int(row["budget_number"]) == number),
                None,
            )
            procedure_delta = dec(financial_detail.get("diff_procedure")) if financial_detail else Decimal("0")
            material_delta = dec(financial_detail.get("diff_material")) if financial_detail else Decimal("0")
            total_delta = dec(financial_detail.get("diff_total")) if financial_detail else Decimal("0")
            residual_delta = total_delta - item_delta

            explanation_parts: list[dict[str, str]] = []
            if item_delta != 0:
                explanation_parts.append({
                    "origin": "ITENS",
                    "label": "Variação líquida dos itens detalhados",
                    "value": str(item_delta),
                })
            if residual_delta != 0:
                explanation_parts.append({
                    "origin": "CABECALHO",
                    "label": "Variação financeira fora dos itens detalhados",
                    "value": str(residual_delta),
                })

            item_comparison[number] = {
                "added": added,
                "removed": removed,
                "modified": modified,
                "unchanged": not added and not removed and not modified,
                "item_delta": str(item_delta),
                "procedure_delta": str(procedure_delta),
                "material_delta": str(material_delta),
                "total_delta": str(total_delta),
                "residual_delta": str(residual_delta),
                "reconciled": item_delta + residual_delta == total_delta,
                "explanation_parts": explanation_parts,
            }

    effective_procedure_value = raw_procedure_value - annulled_procedure_value
    effective_material_value = raw_material_value - annulled_material_value
    effective_total_value = raw_total_value - annulled_value

    safe = len(conflict_numbers) == 0
    return {
        "safe_to_import": safe,
        "total_file": len(file_by_number),
        "new_count": len(new_numbers),
        "identical_count": len(identical_numbers),
        "changed_count": len(changed_numbers),
        "conflict_count": len(conflict_numbers),
        "annulled_count": len(annulled_numbers),
        "effective_count": len(file_by_number) - len(annulled_numbers),
        "annulled_numbers": annulled_numbers,
        "annulled_sources": annulled_sources,
        "annulled_value": str(annulled_value),
        "raw_procedure_value": str(raw_procedure_value),
        "raw_material_value": str(raw_material_value),
        "raw_total_value": str(raw_total_value),
        "effective_procedure_value": str(effective_procedure_value),
        "effective_material_value": str(effective_material_value),
        "effective_total_value": str(effective_total_value),
        "new_value": str(new_value),
        "changed_value": str(changed_value),
        "new_numbers": new_numbers,
        "identical_numbers": identical_numbers,
        "changed_numbers": changed_numbers,
        "conflict_numbers": conflict_numbers,
        "changed_details": changed_details,
        "item_comparison": item_comparison,
        "annulment_reviews": annulment_reviews,
        "annulment_signal_count": len(candidate_numbers),
        "annulment_reviewed_count": sum(
            1 for row in annulment_reviews.values()
            if row["review_state"] in {"CONFIRMED", "NORMAL_REVIEWED"}
        ),
        "annulment_pending_count": sum(
            1 for row in annulment_reviews.values()
            if row["review_state"] == "PENDING"
        ),
    }


def commit_particular_admin_evolution_import(
    *,
    access: ParticularAccess,
    preview: dict[str, Any],
) -> dict[str, Any]:
    """Grava apenas as evidencias administrativas previamente validadas."""
    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil nao possui permissao para importar dados no modulo Particular."
        )
    if preview.get("valid_for_import") is not True:
        raise ValueError("O relatorio administrativo nao passou pela pre-validacao.")
    records = preview.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Nenhuma evolucao administrativa valida foi encontrada.")
    return commit_admin_evolution_import(
        actor_profile_id=access.profile_id,
        source_filename=str(preview.get("source_filename") or ""),
        file_sha256=str(preview.get("file_sha256") or ""),
        reference_month=preview.get("reference_month"),
        records=records,
        metadata={
            "protocol": "ADMIN_EVOLUTION_IMPORT_V1",
            "distinct_attendances": int(preview.get("distinct_attendances") or 0),
            "months_found": preview.get("months_found") or [],
            "embedded_tab_rows": int(preview.get("embedded_tab_rows") or 0),
        },
    )


def resolve_particular_account_review(
    *,
    access: ParticularAccess,
    budget_id: str,
    account_status: str,
    closure_mode: str | None,
    confirmed_final_value: str | None,
    resolution_notes: str,
) -> dict[str, Any]:
    """Valida e registra a conclusão humana de uma revisão de conta."""
    if not access.can_write:
        raise ParticularAccessDenied(
            "Seu perfil não possui permissão para resolver revisões do Particular."
        )

    normalized_budget_id = str(budget_id or "").strip()
    normalized_status = str(account_status or "").strip().upper()
    normalized_mode = str(closure_mode or "").strip().upper() or None
    normalized_notes = str(resolution_notes or "").strip()
    normalized_value = str(confirmed_final_value or "").strip() or None

    if not normalized_budget_id:
        raise ValueError("O orçamento é obrigatório.")
    if normalized_status not in {"CLOSED", "REOPENED", "SPECIAL_OUTCOME", "INCONCLUSIVE"}:
        raise ValueError("Situação final da conta inválida.")
    if normalized_mode is not None and normalized_mode not in {
        "ACCORDING_TO_BUDGET", "HIGHER", "LOWER", "WITH_ADJUSTMENT", "OTHER"
    }:
        raise ValueError("Modo de fechamento inválido.")
    if not normalized_notes:
        raise ValueError("A observação da resolução é obrigatória.")
    if len(normalized_notes) > 2000:
        raise ValueError("A observação deve possuir no máximo 2000 caracteres.")
    if normalized_mode in {"HIGHER", "LOWER"} and normalized_value is None:
        raise ValueError("Fechamentos a maior ou a menor exigem o valor final confirmado.")

    return resolve_account_review(
        actor_profile_id=access.profile_id,
        budget_id=normalized_budget_id,
        account_status=normalized_status,
        closure_mode=normalized_mode,
        confirmed_final_value=normalized_value,
        resolution_notes=normalized_notes,
    )

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
        try:
            return Decimal(str(value if value is not None else "0"))
        except InvalidOperation:
            return Decimal("0")

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

    new_numbers: list[int] = []
    identical_numbers: list[int] = []
    changed_numbers: list[int] = []
    conflict_numbers: list[int] = []
    new_value = Decimal("0")
    changed_value = Decimal("0")

    for number, incoming in file_by_number.items():
        current = existing_by_number.get(number)
        incoming_total = dec(incoming.get("VALOR_TOTAL"))
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

    safe = len(conflict_numbers) == 0
    return {
        "safe_to_import": safe,
        "total_file": len(file_by_number),
        "new_count": len(new_numbers),
        "identical_count": len(identical_numbers),
        "changed_count": len(changed_numbers),
        "conflict_count": len(conflict_numbers),
        "new_value": str(new_value),
        "changed_value": str(changed_value),
        "new_numbers": new_numbers,
        "identical_numbers": identical_numbers,
        "changed_numbers": changed_numbers,
        "conflict_numbers": conflict_numbers,
    }

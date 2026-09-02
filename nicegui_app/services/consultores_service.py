from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.consultores_repository import (
    get_consultor,
    list_carteiras,
    list_consultores,
    list_operadoras_for_consultores,
    list_planos_for_consultores,
)


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@dataclass(frozen=True, slots=True)
class CarteiraPreview:
    wallet_id: str
    consultant_id: str
    operator_id: str
    operator_name: str
    plan_id: str
    plan_name: str
    role: str
    observations: str
    status: str


@dataclass(frozen=True, slots=True)
class ConsultorPreview:
    consultant_id: str
    code: str
    name: str
    job_title: str
    email: str
    phone: str
    observations: str
    status: str
    wallets: tuple[CarteiraPreview, ...]

    @property
    def operators_count(self) -> int:
        return len({
            wallet.operator_id
            for wallet in self.wallets
            if wallet.operator_id
        })

    @property
    def plans_count(self) -> int:
        return len({
            wallet.plan_id
            for wallet in self.wallets
            if wallet.plan_id
        })


def _maps() -> tuple[dict[str, str], dict[str, str]]:
    operators = {
        _text(row, "id"): _text(row, "nome_curto", "nome")
        for row in list_operadoras_for_consultores()
        if _text(row, "id")
    }
    plans = {
        _text(row, "id"): _text(row, "nome_padronizado", "nome")
        for row in list_planos_for_consultores()
        if _text(row, "id")
    }
    return operators, plans


def _wallets_by_consultant() -> dict[str, list[CarteiraPreview]]:
    operators, plans = _maps()
    grouped: dict[str, list[CarteiraPreview]] = {}

    for row in list_carteiras():
        consultant_id = _text(row, "consultor_id")
        if not consultant_id:
            continue

        operator_id = _text(row, "operadora_id")
        plan_id = _text(row, "plano_id")

        wallet = CarteiraPreview(
            wallet_id=_text(row, "id"),
            consultant_id=consultant_id,
            operator_id=operator_id,
            operator_name=operators.get(operator_id, "Operadora não informada"),
            plan_id=plan_id,
            plan_name=plans.get(plan_id, ""),
            role=_text(row, "papel"),
            observations=_text(row, "observacoes"),
            status=_text(row, "status") or "Não informado",
        )
        grouped.setdefault(consultant_id, []).append(wallet)

    return grouped


def _from_record(
    row: dict[str, Any],
    wallets_by_consultant: dict[str, list[CarteiraPreview]],
) -> ConsultorPreview:
    consultant_id = _text(row, "id")

    return ConsultorPreview(
        consultant_id=consultant_id,
        code=_text(row, "codigo"),
        name=_text(row, "nome") or "Consultor sem nome",
        job_title=_text(row, "cargo"),
        email=_text(row, "email"),
        phone=_text(row, "telefone"),
        observations=_text(row, "observacoes"),
        status=_text(row, "status") or "Não informado",
        wallets=tuple(wallets_by_consultant.get(consultant_id, [])),
    )


def get_consultores_preview() -> list[ConsultorPreview]:
    wallets = _wallets_by_consultant()
    return [
        _from_record(row, wallets)
        for row in list_consultores()
    ]


def get_consultor_detail(consultant_id: str) -> ConsultorPreview | None:
    record = get_consultor(consultant_id)
    if record is None:
        return None

    wallets = _wallets_by_consultant()
    return _from_record(record, wallets)

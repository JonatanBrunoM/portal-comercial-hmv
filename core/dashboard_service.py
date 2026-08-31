from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd
import streamlit as st

from core.data_service import get_comunicados, get_contingencias, get_operadoras, get_planos
from utils.formatting import normalize_text


@dataclass(frozen=True)
class DashboardNotice:
    notice_id: str
    title: str
    summary: str
    priority: str
    category: str
    operator_name: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class DashboardContingency:
    contingency_id: str
    event: str
    operator_name: str
    priority: str
    status: str
    guidance: str
    unit: str


@dataclass(frozen=True)
class DashboardSummary:
    operadoras: int
    planos: int
    comunicados: int
    contingencias: int
    notices: tuple[DashboardNotice, ...]
    contingency_items: tuple[DashboardContingency, ...]


def _safe(row: pd.Series, column: str) -> str:
    if column not in row.index or pd.isna(row[column]):
        return ""
    return str(row[column]).strip()


def _parse_date(value: object) -> pd.Timestamp | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (date, datetime)):
        return pd.Timestamp(value).normalize()
    parsed = pd.to_datetime(str(value).strip(), errors="coerce")
    return None if pd.isna(parsed) else pd.Timestamp(parsed).normalize()


def _format_date(value: object) -> str:
    parsed = _parse_date(value)
    return parsed.strftime("%d/%m/%Y") if parsed is not None else ""


def _operator_map(operadoras: pd.DataFrame) -> dict[str, str]:
    if operadoras.empty:
        return {}
    return {
        _safe(row, "id"): (_safe(row, "nome_curto") or _safe(row, "nome"))
        for _, row in operadoras.iterrows() if _safe(row, "id")
    }


def _period_active(row: pd.Series) -> bool:
    today = pd.Timestamp.today().normalize()
    start = _parse_date(row.get("inicio_em"))
    end = _parse_date(row.get("fim_em"))
    return not ((start is not None and today < start) or (end is not None and today > end))


def _published_notice(row: pd.Series) -> bool:
    return normalize_text(row.get("status")) in {"ativo", "publicado", "publicada"} and _period_active(row)


def _active_contingency(row: pd.Series) -> bool:
    status = normalize_text(row.get("status"))
    return status not in {"inativo", "inativa", "encerrado", "encerrada", "cancelado", "cancelada"} and _period_active(row)


def _priority(value: object) -> int:
    return {"alta": 0, "media": 1, "normal": 2, "baixa": 3}.get(normalize_text(value), 4)


@st.cache_data(ttl=600, show_spinner=False)
def get_dashboard_summary() -> DashboardSummary:
    operadoras = get_operadoras()
    planos = get_planos()
    comunicados = get_comunicados()
    contingencias = get_contingencias()
    names = _operator_map(operadoras)

    notices: list[DashboardNotice] = []
    if not comunicados.empty:
        active = comunicados[comunicados.apply(_published_notice, axis=1)].copy()
        if not active.empty:
            active["_priority"] = active["prioridade"].apply(_priority) if "prioridade" in active else 4
            active = active.sort_values(["_priority", "inicio_em"], ascending=[True, False], na_position="last")
            for _, row in active.head(3).iterrows():
                notices.append(DashboardNotice(
                    notice_id=_safe(row, "id"), title=_safe(row, "titulo") or "Comunicado sem título",
                    summary=_safe(row, "resumo") or _safe(row, "conteudo"),
                    priority=_safe(row, "prioridade") or "Normal", category=_safe(row, "categoria") or "Geral",
                    operator_name=names.get(_safe(row, "operadora_id"), "Comunicado geral"),
                    start_date=_format_date(row.get("inicio_em")), end_date=_format_date(row.get("fim_em")),
                ))

    contingency_items: list[DashboardContingency] = []
    if not contingencias.empty:
        active = contingencias[contingencias.apply(_active_contingency, axis=1)].copy()
        if not active.empty:
            active["_priority"] = active["prioridade"].apply(_priority) if "prioridade" in active else 4
            active = active.sort_values("_priority", ascending=True)
            for _, row in active.head(3).iterrows():
                contingency_items.append(DashboardContingency(
                    contingency_id=_safe(row, "id"), event=_safe(row, "titulo") or "Contingência sem título",
                    operator_name=names.get(_safe(row, "operadora_id"), "Todas as operadoras"),
                    priority=_safe(row, "prioridade") or "Não informada",
                    status=_safe(row, "status") or "Vigente",
                    guidance=_safe(row, "orientacao_alternativa"), unit="Todos os locais",
                ))

    return DashboardSummary(
        operadoras=len(operadoras), planos=len(planos), comunicados=len(notices),
        contingencias=len(contingency_items), notices=tuple(notices),
        contingency_items=tuple(contingency_items),
    )

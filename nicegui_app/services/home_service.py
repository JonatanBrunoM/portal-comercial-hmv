from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from nicegui_app.repositories.home_repository import load_home_snapshot


def _text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    return str(value).strip() if value is not None else ""


def _is_active(row: dict[str, Any]) -> bool:
    return _text(row, "status").casefold() == "ativo"


def _date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def _in_window(start: date | None, end: date | None) -> bool:
    today = date.today()
    if start and today < start:
        return False
    if end and today > end:
        return False
    return True


@dataclass(frozen=True, slots=True)
class HomeMetric:
    label: str
    value: int
    detail: str
    icon: str
    route: str


@dataclass(frozen=True, slots=True)
class HomeCommunication:
    item_id: str
    operator_name: str
    title: str
    summary: str
    category: str
    priority: str
    featured: bool

    @property
    def route(self) -> str:
        return f"/comunicados/{self.item_id}"


@dataclass(frozen=True, slots=True)
class HomeContingency:
    item_id: str
    operator_name: str
    title: str
    description: str
    alternative_guidance: str
    priority: str
    status: str

    @property
    def route(self) -> str:
        return f"/contingencias/{self.item_id}"


@dataclass(frozen=True, slots=True)
class HomeData:
    metrics: tuple[HomeMetric, ...]
    communications: tuple[HomeCommunication, ...]
    contingencies: tuple[HomeContingency, ...]


def _operator_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in rows:
        operator_id = _text(row, "id")
        if not operator_id:
            continue
        mapping[operator_id] = (
            _text(row, "nome_curto")
            or _text(row, "nome")
            or "Operadora"
        )
    return mapping


def _communication_priority(row: dict[str, Any]) -> tuple[int, int, date]:
    featured = bool(row.get("destaque"))
    priority = _text(row, "prioridade").casefold()
    priority_score = {
        "urgente": 4,
        "alta": 3,
        "importante": 3,
        "normal": 2,
        "baixa": 1,
    }.get(priority, 2)
    start = _date(row.get("inicio_em")) or date.min
    return (1 if featured else 0, priority_score, start)


def _contingency_priority(row: dict[str, Any]) -> tuple[int, int, date]:
    status = _text(row, "status").casefold()
    priority = _text(row, "prioridade").casefold()
    priority_score = {
        "crítica": 5,
        "critica": 5,
        "urgente": 4,
        "alta": 3,
        "normal": 2,
        "baixa": 1,
    }.get(priority, 2)
    start = _date(row.get("inicio_em")) or date.min
    return (1 if status == "ativa" else 0, priority_score, start)


def get_home_data() -> HomeData:
    snapshot = load_home_snapshot()

    operadoras = [
        row for row in snapshot["operadoras"]
        if _is_active(row)
    ]
    portais = [
        row for row in snapshot["portais"]
        if _is_active(row)
    ]
    documentos = [
        row for row in snapshot["documentos"]
        if _is_active(row)
    ]

    operators = _operator_map(operadoras)

    communication_rows = [
        row for row in snapshot["comunicados"]
        if _text(row, "status").casefold() == "publicado"
        and _in_window(_date(row.get("inicio_em")), _date(row.get("fim_em")))
    ]
    communication_rows.sort(key=_communication_priority, reverse=True)

    communications = tuple(
        HomeCommunication(
            item_id=_text(row, "id"),
            operator_name=operators.get(
                _text(row, "operadora_id"),
                "Institucional",
            ),
            title=_text(row, "titulo") or "Comunicado",
            summary=_text(row, "resumo"),
            category=_text(row, "categoria") or "Informação",
            priority=_text(row, "prioridade") or "Normal",
            featured=bool(row.get("destaque")),
        )
        for row in communication_rows[:3]
        if _text(row, "id")
    )

    contingency_rows = [
        row for row in snapshot["contingencias"]
        if _text(row, "status").casefold() in {"programada", "ativa"}
        and _in_window(_date(row.get("inicio_em")), _date(row.get("fim_em")))
    ]
    contingency_rows.sort(key=_contingency_priority, reverse=True)

    contingencies = tuple(
        HomeContingency(
            item_id=_text(row, "id"),
            operator_name=operators.get(
                _text(row, "operadora_id"),
                "Operadora",
            ),
            title=_text(row, "titulo") or "Contingência",
            description=_text(row, "descricao"),
            alternative_guidance=_text(row, "orientacao_alternativa"),
            priority=_text(row, "prioridade") or "Normal",
            status=_text(row, "status") or "Não informado",
        )
        for row in contingency_rows[:3]
        if _text(row, "id")
    )

    metrics = (
        HomeMetric(
            "Operadoras",
            len(operadoras),
            "disponíveis para consulta",
            "domain",
            "/operadoras",
        ),
        HomeMetric(
            "Portais",
            len(portais),
            "acessos cadastrados",
            "vpn_key",
            "/portais",
        ),
        HomeMetric(
            "Documentos",
            len(documentos),
            "referências disponíveis",
            "description",
            "/documentos",
        ),
        HomeMetric(
            "Alertas",
            len(contingency_rows),
            "contingências vigentes",
            "warning_amber",
            "/contingencias",
        ),
    )

    return HomeData(
        metrics=metrics,
        communications=communications,
        contingencies=contingencies,
    )

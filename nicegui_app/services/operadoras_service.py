from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from nicegui_app.repositories.operadoras_repository import (
    get_operadora,
    list_autorizacoes_by_operadora,
    list_carteiras_by_operadora,
    list_coberturas_by_operadora,
    list_comunicados_by_operadora,
    list_consultores_for_operadora_hub,
    list_contatos_by_operadora,
    list_contingencias_by_operadora,
    list_dicas_by_operadora,
    list_documentos_by_operadora,
    list_elegibilidade_by_operadora,
    list_operadoras,
    list_planos_by_operadora,
    list_portais_by_operadora,
    list_portais_for_operadora_cards,
    list_documentos_for_operadora_cards,
    list_contatos_for_operadora_cards,
)


def _text(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _active_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(row for row in rows if not _text(row,"status") or _text(row,"status").lower() == "ativo")

def _published_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(row for row in rows if _text(row,"status").lower() == "publicado")

def _visible_contingencies(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(row for row in rows if _text(row,"status").lower() in {"programada", "ativa"})

def _carteiras(operator_id: str) -> tuple[dict[str, Any], ...]:
    consultants={_text(r,"id"):r for r in list_consultores_for_operadora_hub() if _text(r,"id") and _text(r,"status").lower()=="ativo"}
    result=[]
    for row in list_carteiras_by_operadora(operator_id):
        if _text(row,"status") and _text(row,"status").lower() != "ativo": continue
        item=dict(row); consultant=consultants.get(_text(row,"consultor_id"))
        if consultant:
            item.update(consultor_nome=_text(consultant,"nome"), consultor_cargo=_text(consultant,"cargo"), consultor_email=_text(consultant,"email"), consultor_telefone=_text(consultant,"telefone"))
        result.append(item)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class OperadoraPreview:
    operator_id: str
    code: str
    name: str
    short_name: str
    status: str
    observations: str
    logo_url: str
    site_url: str
    portal_name: str = ""
    portal_detail: str = ""
    document_name: str = ""
    document_detail: str = ""
    contact_name: str = ""
    contact_value: str = ""


@dataclass(frozen=True, slots=True)
class OperadoraDetail:
    operator: OperadoraPreview
    planos: tuple[dict[str, Any], ...]
    portais: tuple[dict[str, Any], ...]
    elegibilidade: tuple[dict[str, Any], ...]
    documentos: tuple[dict[str, Any], ...]
    autorizacoes: tuple[dict[str, Any], ...]
    coberturas: tuple[dict[str, Any], ...]
    contatos: tuple[dict[str, Any], ...]
    contingencias: tuple[dict[str, Any], ...]
    dicas: tuple[dict[str, Any], ...]
    comunicados: tuple[dict[str, Any], ...]
    carteiras: tuple[dict[str, Any], ...]


def _operator_from_record(record: dict[str, Any]) -> OperadoraPreview:
    name = _text(record, "nome") or "Operadora sem nome"
    return OperadoraPreview(
        operator_id=_text(record, "id"),
        code=_text(record, "codigo"),
        name=name,
        short_name=_text(record, "nome_curto") or name,
        status=_text(record, "status") or "Não informado",
        observations=_text(record, "observacoes"),
        logo_url=_text(record, "logo_url"),
        site_url=_text(record, "site_url"),
    )


def _first_active_by_operator(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    first: dict[str, dict[str, Any]] = {}
    for row in rows:
        operator_id = _text(row, "operadora_id")
        if not operator_id:
            continue
        status = _text(row, "status").lower()
        if status and status != "ativo":
            continue
        first.setdefault(operator_id, row)
    return first


def get_operadoras_preview() -> list[OperadoraPreview]:
    # A landing de Operadoras precisa mostrar informação útil dentro de cada
    # card. Carregamos três conjuntos públicos em lote, em paralelo, evitando
    # abrir o hub completo de cada operadora (11 consultas por operadora).
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="portal-operator-cards") as pool:
        operators_future = pool.submit(list_operadoras)
        portals_future = pool.submit(list_portais_for_operadora_cards)
        documents_future = pool.submit(list_documentos_for_operadora_cards)
        contacts_future = pool.submit(list_contatos_for_operadora_cards)

        operator_rows = operators_future.result()
        portals = _first_active_by_operator(portals_future.result())
        documents = _first_active_by_operator(documents_future.result())
        contacts = _first_active_by_operator(contacts_future.result())

    result: list[OperadoraPreview] = []
    for row in operator_rows:
        base = _operator_from_record(row)
        portal = portals.get(base.operator_id, {})
        document = documents.get(base.operator_id, {})
        contact = contacts.get(base.operator_id, {})

        portal_type = _text(portal, "tipo")
        requires_login = portal.get("exige_login")
        portal_detail_parts = [
            portal_type,
            "Exige login" if requires_login is True else "",
        ]

        document_detail_parts = [
            "Obrigatório" if document.get("obrigatorio") is True else "",
            _text(document, "formato"),
        ]

        contact_name = (
            _text(contact, "finalidade")
            or _text(contact, "nome_setor")
            or "Canal de atendimento"
        )

        result.append(
            OperadoraPreview(
                operator_id=base.operator_id,
                code=base.code,
                name=base.name,
                short_name=base.short_name,
                status=base.status,
                observations=base.observations,
                logo_url=base.logo_url,
                site_url=base.site_url,
                portal_name=_text(portal, "nome"),
                portal_detail=" · ".join(
                    item for item in portal_detail_parts if item
                ),
                document_name=_text(document, "nome"),
                document_detail=" · ".join(
                    item for item in document_detail_parts if item
                ),
                contact_name=contact_name if contact else "",
                contact_value=_text(contact, "contato"),
            )
        )

    return result


def get_operadora_detail(operator_id: str) -> OperadoraDetail | None:
    record = get_operadora(operator_id)
    if record is None:
        return None

    loaders = {
        "planos": list_planos_by_operadora,
        "portais": list_portais_by_operadora,
        "elegibilidade": list_elegibilidade_by_operadora,
        "documentos": list_documentos_by_operadora,
        "autorizacoes": list_autorizacoes_by_operadora,
        "coberturas": list_coberturas_by_operadora,
        "contatos": list_contatos_by_operadora,
        "contingencias": list_contingencias_by_operadora,
        "dicas": list_dicas_by_operadora,
        "comunicados": list_comunicados_by_operadora,
        "carteiras": _carteiras,
    }

    # O hub da operadora reúne muitos conjuntos independentes. Antes eles eram
    # carregados um após o outro; agora aguardamos apenas o grupo mais lento.
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="portal-operator") as pool:
        futures = {
            name: pool.submit(loader, operator_id)
            for name, loader in loaders.items()
        }
        data = {name: future.result() for name, future in futures.items()}

    return OperadoraDetail(
        operator=_operator_from_record(record),
        planos=_active_rows(data["planos"]),
        portais=_active_rows(data["portais"]),
        elegibilidade=_active_rows(data["elegibilidade"]),
        documentos=_active_rows(data["documentos"]),
        autorizacoes=_active_rows(data["autorizacoes"]),
        coberturas=_active_rows(data["coberturas"]),
        contatos=_active_rows(data["contatos"]),
        contingencias=_visible_contingencies(data["contingencias"]),
        dicas=_active_rows(data["dicas"]),
        comunicados=_published_rows(data["comunicados"]),
        carteiras=tuple(data["carteiras"]),
    )

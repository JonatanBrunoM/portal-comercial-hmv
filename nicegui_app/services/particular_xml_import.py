from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET


class ParticularXmlError(ValueError):
    """XML de orçamento Particular inválido ou incompatível."""


@dataclass(frozen=True)
class ParticularXmlItem:
    source_sequence_original: int
    source_position: int
    item_code: str
    description: str | None
    quantity: Decimal | None
    unit_value: Decimal | None
    total_value: Decimal | None


@dataclass(frozen=True)
class ParticularXmlBudget:
    budget_number: int
    budget_date: date

    attendance_code: str | None
    doctor_name: str | None
    patient_name: str | None
    requester: str | None

    cti_days: Decimal | None
    recovery_time: str | None

    base_value: Decimal
    special_material_value: Decimal | None
    total_value: Decimal

    items: tuple[ParticularXmlItem, ...]


@dataclass(frozen=True)
class ParticularXmlDocument:
    encoding: str
    budgets: tuple[ParticularXmlBudget, ...]

    @property
    def budget_count(self) -> int:
        return len(self.budgets)

    @property
    def item_count(self) -> int:
        return sum(len(budget.items) for budget in self.budgets)


def _text(node: ET.Element, tag: str) -> str | None:
    child = node.find(tag)

    if child is None or child.text is None:
        return None

    value = child.text.strip()
    return value or None


def _required_text(node: ET.Element, tag: str) -> str:
    value = _text(node, tag)

    if value is None:
        raise ParticularXmlError(
            f"Campo obrigatório ausente ou vazio: {tag}"
        )

    return value


def _decimal(
    value: str | None,
    *,
    field: str,
    required: bool = False,
) -> Decimal | None:

    if value is None:
        if required:
            raise ParticularXmlError(
                f"Campo financeiro obrigatório ausente: {field}"
            )
        return None

    normalized = (
        value
        .strip()
        .replace("R$", "")
        .replace(" ", "")
    )

    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ParticularXmlError(
            f"Valor inválido no campo {field}."
        ) from exc


def _integer(value: str, *, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ParticularXmlError(
            f"Valor inteiro inválido no campo {field}."
        ) from exc


def _date_ddmmyy(value: str) -> date:
    try:
        return datetime.strptime(value, "%d/%m/%y").date()
    except ValueError as exc:
        raise ParticularXmlError(
            "Formato inválido no campo DATA. Esperado dd/mm/yy."
        ) from exc


def _decode_xml(raw: bytes) -> tuple[str, str]:
    # O XML HMV2670 validado não possui BOM nem declaração de encoding
    # e utiliza caracteres compatíveis com Windows-1252.
    #
    # Tentamos UTF-8 primeiro para aceitar futuros arquivos corretamente
    # exportados nesse formato. Caso não seja UTF-8, usamos CP1252.
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        try:
            return raw.decode("cp1252"), "cp1252"
        except UnicodeDecodeError as exc:
            raise ParticularXmlError(
                "Não foi possível identificar uma codificação XML suportada."
            ) from exc


def _parse_item(
    item_node: ET.Element,
    *,
    parent_budget_number: int,
    position: int,
) -> ParticularXmlItem:

    sequence_raw = _required_text(
        item_node,
        "SEQ_ORCAMENTO_ITEM",
    )

    source_sequence = _integer(
        sequence_raw,
        field="SEQ_ORCAMENTO_ITEM",
    )

    if source_sequence != parent_budget_number:
        raise ParticularXmlError(
            "SEQ_ORCAMENTO_ITEM incompatível com o orçamento pai."
        )

    item_code = _required_text(item_node, "CD_PRO_FAT")

    return ParticularXmlItem(
        source_sequence_original=source_sequence,
        source_position=position,
        item_code=item_code,
        description=_text(item_node, "DESCRICAO_PRO_FAT"),
        quantity=_decimal(
            _text(item_node, "QUANTIDADE"),
            field="QUANTIDADE",
        ),
        unit_value=_decimal(
            _text(item_node, "VALOR_UNITARIO"),
            field="VALOR_UNITARIO",
        ),
        total_value=_decimal(
            _text(item_node, "VALOR_TOTAL1"),
            field="VALOR_TOTAL1",
        ),
    )


def _parse_budget(
    budget_node: ET.Element,
) -> ParticularXmlBudget:

    budget_number = _integer(
        _required_text(budget_node, "SEQ_ORCAMENTO"),
        field="SEQ_ORCAMENTO",
    )

    budget_date = _date_ddmmyy(
        _required_text(budget_node, "DATA")
    )

    base_value = _decimal(
        _required_text(budget_node, "VALOR"),
        field="VALOR",
        required=True,
    )

    total_value = _decimal(
        _required_text(budget_node, "VALOR_TOTAL"),
        field="VALOR_TOTAL",
        required=True,
    )

    material_value = _decimal(
        _text(budget_node, "VALOR_MATERIAL_ESPECIAL"),
        field="VALOR_MATERIAL_ESPECIAL",
    )

    item_nodes = budget_node.findall(
        ".//G_SEQ_ORCAMENTO_ITEM"
    )

    items: list[ParticularXmlItem] = []
    seen_codes: set[str] = set()

    for position, item_node in enumerate(item_nodes, start=1):

        item = _parse_item(
            item_node,
            parent_budget_number=budget_number,
            position=position,
        )

        if item.item_code in seen_codes:
            raise ParticularXmlError(
                "CD_PRO_FAT repetido dentro do mesmo orçamento."
            )

        seen_codes.add(item.item_code)
        items.append(item)

    # VALOR_TOTAL é sempre preservado como valor oficial.
    #
    # A composição abaixo é uma validação de consistência, não um
    # recálculo do valor oficial.
    if total_value != base_value:
        if (
            material_value is None
            or total_value != base_value + material_value
        ):
            raise ParticularXmlError(
                "Composição financeira inconsistente no orçamento."
            )

    return ParticularXmlBudget(
        budget_number=budget_number,
        budget_date=budget_date,
        attendance_code=_text(budget_node, "CD_ATENDIMENTO"),
        doctor_name=_text(budget_node, "NOME_MEDICO"),
        patient_name=_text(budget_node, "NOME_PACIENTE"),
        requester=_text(budget_node, "SOLICITANTE"),
        cti_days=_decimal(
            _text(budget_node, "DIAS_CTI"),
            field="DIAS_CTI",
        ),
        recovery_time=_text(
            budget_node,
            "TEMPO_RECUPERACAO",
        ),
        base_value=base_value,
        special_material_value=material_value,
        total_value=total_value,
        items=tuple(items),
    )


def parse_particular_xml(
    path: str | Path,
) -> ParticularXmlDocument:
    """Lê e valida um XML Particular sem realizar qualquer persistência."""

    xml_path = Path(path)

    if not xml_path.is_file():
        raise ParticularXmlError("Arquivo XML não encontrado.")

    raw = xml_path.read_bytes()

    if not raw:
        raise ParticularXmlError("Arquivo XML vazio.")

    xml_text, encoding = _decode_xml(raw)

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ParticularXmlError(
            "Estrutura XML inválida."
        ) from exc

    budget_nodes = root.findall(".//G_SEQ_ORCAMENTO")

    if not budget_nodes:
        raise ParticularXmlError(
            "Nenhum orçamento encontrado no XML."
        )

    budgets: list[ParticularXmlBudget] = []
    seen_budget_numbers: set[int] = set()

    for budget_node in budget_nodes:

        budget = _parse_budget(budget_node)

        if budget.budget_number in seen_budget_numbers:
            raise ParticularXmlError(
                "SEQ_ORCAMENTO duplicado no XML."
            )

        seen_budget_numbers.add(budget.budget_number)
        budgets.append(budget)

    return ParticularXmlDocument(
        encoding=encoding,
        budgets=tuple(budgets),
    )
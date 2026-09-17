from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from nicegui_app.repositories.particular_repository import (
    ParticularBudgetImportResult,
    finalize_xml_budget_items,
    finish_import,
    import_xml_budget_result,
    import_xml_budget_item,
    import_xml_original_value,
    start_xml_import,
)
from nicegui_app.services.particular_xml_import import (
    ParticularXmlBudget,
    ParticularXmlDocument,
    parse_particular_xml,
)


@dataclass(frozen=True)
class ParticularImportResult:
    batch_id: str
    records_total: int
    records_processed: int
    records_created: int
    records_updated: int
    records_error: int


def _decimal_text(value) -> str | None:
    """Converte Decimal para texto exato, sem passar por float."""

    if value is None:
        return None

    return str(value)


def _file_sha256(path: Path) -> str:
    """Calcula SHA-256 do arquivo sem registrar seu conteúdo."""

    digest = sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _persist_budget(
    *,
    actor_profile_id: str,
    batch_id: str,
    budget: ParticularXmlBudget,
) -> ParticularBudgetImportResult:
    """
    Persiste um orçamento já validado pelo parser.

    Retorna o UUID do orçamento e a operação realizada
    pelo PostgreSQL: CREATED ou UPDATED.

    Não realiza classificação comercial nesta etapa.
    """

    budget_result = import_xml_budget_result(
        actor_profile_id=actor_profile_id,
        import_batch_id=batch_id,
        budget_number=budget.budget_number,
        budget_date=budget.budget_date.isoformat(),
        doctor_name=budget.doctor_name,
        original_requester=budget.requester,
        patient_name=budget.patient_name,
        patient_name_normalized=None,

        # Classificações especiais ainda não serão inferidas
        # automaticamente nesta etapa.
        is_liminar=False,
        is_international=False,
        is_transcription=False,
    )

    # A nova RPC retorna:
    # ParticularBudgetImportResult(
    #     budget_id="...",
    #     operation="CREATED" ou "UPDATED",
    # )
    budget_id = budget_result.budget_id

    for item in budget.items:
        import_xml_budget_item(
            actor_profile_id=actor_profile_id,
            import_batch_id=batch_id,
            budget_id=budget_id,
            source_sequence_original=item.source_sequence_original,
            source_position=item.source_position,
            item_code=item.item_code,
            description_original=item.description,
            description_normalized=None,
            quantity=_decimal_text(item.quantity),
            unit_value=_decimal_text(item.unit_value),
            total_value=_decimal_text(item.total_value),
            unit=None,
            item_category=None,
            technology=None,
        )

    # A própria RPC valida:
    #
    # observed_count == expected_item_count
    #
    # O inteiro retornado representa a quantidade de itens antigos
    # desativados, e NÃO a quantidade de itens processados.
    finalize_xml_budget_items(
        actor_profile_id=actor_profile_id,
        import_batch_id=batch_id,
        budget_id=budget_id,
        expected_item_count=len(budget.items),
    )

    import_xml_original_value(
        actor_profile_id=actor_profile_id,
        import_batch_id=batch_id,
        budget_id=budget_id,
        procedure_value=_decimal_text(budget.base_value),
        material_value=_decimal_text(
            budget.special_material_value
        ),
        total_value=_decimal_text(budget.total_value),
    )

    return budget_result

def run_particular_xml_import(
    *,
    actor_profile_id: str,
    xml_path: str | Path,
) -> ParticularImportResult:
    """
    Executa uma importação XML completa do módulo Particular.

    Estratégia:
    1. valida integralmente o XML antes de abrir o lote;
    2. calcula o SHA-256 do arquivo;
    3. abre um batch PROCESSING;
    4. persiste cada orçamento;
    5. contabiliza CREATED / UPDATED;
    6. finaliza como COMPLETED;
    7. em falha após abertura do batch, tenta formalizar FAILED.

    Dados já persistidos antes de uma eventual falha são preservados.
    Uma nova tentativa deverá ocorrer em um novo batch.
    """

    path = Path(xml_path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"Arquivo XML não localizado: {path}"
        )

    # --------------------------------------------------------
    # 1. PARSE COMPLETO ANTES DE QUALQUER GRAVAÇÃO
    # --------------------------------------------------------

    document = parse_particular_xml(path)

    records_total = len(document.budgets)

    if records_total == 0:
        raise ValueError(
            "O XML não contém orçamentos para importação."
        )

    # --------------------------------------------------------
    # 2. IDENTIFICAÇÃO SEGURA DO ARQUIVO
    # --------------------------------------------------------

    file_hash = _file_sha256(path)

    # Somente basename. Nunca persistimos o caminho local completo.
    source_filename = path.name

    # --------------------------------------------------------
    # 3. ABRE O LOTE
    # --------------------------------------------------------

    batch_id = start_xml_import(
        actor_profile_id=actor_profile_id,
        source_filename=source_filename,
        file_sha256=file_hash,
        metadata={
            "parser": "particular_xml_import",
            "encoding": document.encoding,
        },
    )

    records_processed = 0
    records_created = 0
    records_updated = 0
    records_error = 0

    try:

        # ----------------------------------------------------
        # 4. PERSISTÊNCIA DOS ORÇAMENTOS
        # ----------------------------------------------------

        for budget in document.budgets:

            budget_result = _persist_budget(
                actor_profile_id=actor_profile_id,
                batch_id=batch_id,
                budget=budget,
            )

            if budget_result.operation == "CREATED":
                records_created += 1

            elif budget_result.operation == "UPDATED":
                records_updated += 1

            else:
                # Defesa adicional.
                # O repository já bloqueia operações diferentes.
                raise RuntimeError(
                    "Operação de orçamento inesperada."
                )

            records_processed += 1

        # ----------------------------------------------------
        # 5. FINALIZAÇÃO COM SUCESSO
        # ----------------------------------------------------

        finish_import(
            actor_profile_id=actor_profile_id,
            import_batch_id=batch_id,
            status="COMPLETED",
            records_total=records_total,
            records_processed=records_processed,
            records_created=records_created,
            records_updated=records_updated,
            records_error=records_error,
            metadata={
                "parser": "particular_xml_import",
                "encoding": document.encoding,
            },
        )

    except Exception:

        # ----------------------------------------------------
        # 6. FINALIZAÇÃO CONTROLADA EM CASO DE FALHA
        # ----------------------------------------------------
        #
        # O orçamento que provocou a exceção NÃO entra em
        # records_processed, pois não concluiu todo o pipeline.
        #
        # records_error = 1 representa o registro no qual a
        # execução foi interrompida.
        #
        # Nenhuma informação de paciente, item ou conteúdo
        # sensível é colocada no metadata.
        # ----------------------------------------------------

        records_error = 1

        try:
            finish_import(
                actor_profile_id=actor_profile_id,
                import_batch_id=batch_id,
                status="FAILED",
                records_total=records_total,
                records_processed=records_processed,
                records_created=records_created,
                records_updated=records_updated,
                records_error=records_error,
                metadata={
                    "parser": "particular_xml_import",
                    "encoding": document.encoding,
                    "failure": "IMPORT_INTERRUPTED",
                },
            )

        except Exception:
            # Não substituímos a exceção original por uma eventual
            # falha secundária ao tentar finalizar o batch.
            pass

        raise

    # --------------------------------------------------------
    # 7. RESULTADO FINAL
    # --------------------------------------------------------

    return ParticularImportResult(
        batch_id=batch_id,
        records_total=records_total,
        records_processed=records_processed,
        records_created=records_created,
        records_updated=records_updated,
        records_error=records_error,
    )
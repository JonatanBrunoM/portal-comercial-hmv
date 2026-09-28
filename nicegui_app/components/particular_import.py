"""Tela de pré-validação para importação dos relatórios do Particular."""
from __future__ import annotations

from datetime import date

from nicegui import run, ui

from nicegui_app.services.particular_import_validation import inspect_hmv2670
from nicegui_app.services.particular_service import ParticularAccess, preflight_particular_import


def _date_br(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return date.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        return value


def render_particular_import(access: ParticularAccess) -> None:
    with ui.column().classes("w-full gap-5"):
        with ui.column().classes("gap-1"):
            ui.label("IMPORTAÇÃO INTELIGENTE").classes("text-caption text-weight-bold text-primary")
            ui.label("Importar relatórios").classes("text-h4 text-weight-bold")
            ui.label(
                "O arquivo é analisado antes de qualquer gravação. Nesta primeira etapa, "
                "nenhum dado enviado nesta tela é incorporado ao Supabase."
            ).classes("text-body1 text-grey-7")

        with ui.card().classes("w-full p-5 gap-4"):
            with ui.row().classes("w-full items-center justify-between gap-4 flex-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("Relatório de orçamentos confeccionados · HMV2670").classes("text-h6 text-weight-bold")
                    ui.label(
                        "Envie o relatório original .XML ou a versão .XLSX. O Portal identificará automaticamente período, competência, "
                        "quantidade de orçamentos e fechamento financeiro."
                    ).classes("text-body2 text-grey-7")
                ui.badge("PRÉ-VALIDAÇÃO · NÃO GRAVA DADOS", color="primary").props("outline")

            result_area = ui.column().classes("w-full gap-4")

            async def handle_upload(event) -> None:
                result_area.clear()
                try:
                    content = await event.file.read()
                    filename = event.file.name
                    with result_area:
                        ui.label("Analisando estrutura e integridade do relatório...").classes("text-body2 text-grey-7")
                    result = await run.io_bound(inspect_hmv2670, content, filename)
                    preflight = None
                    if result.get("valid_for_import"):
                        preflight = await run.io_bound(preflight_particular_import, access=access, validated_report=result)
                except Exception as exc:
                    result_area.clear()
                    with result_area:
                        ui.label(f"Arquivo rejeitado: {exc}").classes("text-negative text-weight-bold")
                    return

                result_area.clear()
                with result_area:
                    if result["valid_for_import"]:
                        ui.label("Arquivo aprovado na pré-validação").classes("text-h6 text-positive text-weight-bold")
                    else:
                        ui.label("Arquivo bloqueado pela pré-validação").classes("text-h6 text-negative text-weight-bold")

                    if result.get("competence_label"):
                        with ui.card().classes("w-full p-4"):
                            ui.label(f'Competência identificada: {result["competence_label"]}').classes("text-h5 text-weight-bold")
                            ui.label(
                                f'Período do arquivo: {_date_br(result.get("start_date"))} a '
                                f'{_date_br(result.get("end_date"))} · {result.get("coverage_type", "—")}'
                            ).classes("text-body2")
                            ui.label(
                                "Os indicadores devem ser consultados pelo mês de referência. "
                                "Ao selecionar outro mês no dashboard, o Portal exibirá somente a competência escolhida."
                            ).classes("text-caption text-grey-7")

                    if result.get("budgets") is not None:
                        with ui.row().classes("w-full gap-3 flex-wrap"):
                            for label, value, icon in (
                                ("Orçamentos únicos", f'{result["budgets"]:,}'.replace(",", "."), "receipt_long"),
                                ("Linhas de itens", f'{result["item_rows"]:,}'.replace(",", "."), "format_list_numbered"),
                                ("Registros de orçamento", f'{result["physical_rows"]:,}'.replace(",", "."), "table_rows"),
                                ("Diferença financeira", result["financial_difference_label"], "balance"),
                            ):
                                with ui.card().classes("flex-1 min-w-[190px] p-4 gap-1"):
                                    ui.icon(icon, size="24px").classes("text-primary")
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(value).classes("text-h6 text-weight-bold")

                        with ui.row().classes("w-full gap-3 flex-wrap"):
                            for label, value in (
                                ("Procedimentos", result["procedure_value_label"]),
                                ("Materiais", result["material_value_label"]),
                                ("Total do relatório", result["total_value_label"]),
                            ):
                                with ui.card().classes("flex-1 min-w-[220px] p-4 gap-1"):
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(value).classes("text-h5 text-weight-bold")

                    ui.label("Validações").classes("text-subtitle1 text-weight-bold")
                    for issue in result.get("issues", []):
                        severity = issue.get("severity")
                        icon = "check_circle" if severity == "OK" else ("warning" if severity == "WARNING" else "error")
                        css = "text-positive" if severity == "OK" else ("text-warning" if severity == "WARNING" else "text-negative")
                        with ui.row().classes("w-full items-start gap-2"):
                            ui.icon(icon, size="20px").classes(css)
                            ui.label(issue.get("message", "")).classes("text-body2")

                    ui.separator()
                    ui.label(
                        f'Assinatura SHA-256 do arquivo: {result["sha256"][:16]}…'
                    ).classes("text-caption text-grey-7")
                    ui.label(
                        "A assinatura será usada na etapa de processamento para impedir importações acidentais "
                        "do mesmo arquivo. Identificadores de pacientes não são exibidos nesta tela."
                    ).classes("text-caption text-grey-7")

                    if result["valid_for_import"] and preflight is not None:
                        ui.separator()
                        ui.label("Verificação contra a base").classes("text-h6 text-weight-bold")
                        with ui.row().classes("w-full gap-3 flex-wrap"):
                            for label, value, icon in (
                                ("Novos", preflight["new_count"], "add_circle"),
                                ("Já existentes idênticos", preflight["identical_count"], "verified"),
                                ("Com alteração", preflight["changed_count"], "sync"),
                                ("Conflitos", preflight["conflict_count"], "report_problem"),
                            ):
                                with ui.card().classes("flex-1 min-w-[190px] p-4 gap-1"):
                                    ui.icon(icon, size="24px").classes("text-primary")
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(str(value)).classes("text-h6 text-weight-bold")

                        if preflight["safe_to_import"]:
                            ui.label(
                                "Preflight concluído: nenhum conflito estrutural foi encontrado. "
                                "A gravação continua desabilitada nesta etapa de teste."
                            ).classes("text-positive text-weight-bold")
                        else:
                            ui.label(
                                "Importação bloqueada: existem orçamentos cujo número já está na base "
                                "com data diferente. Esses conflitos precisam ser revisados antes da gravação."
                            ).classes("text-negative text-weight-bold")

                        if preflight["changed_count"]:
                            ui.label(
                                f'{preflight["changed_count"]} orçamento(s) existente(s) possuem valores diferentes '
                                "na mesma data. Eles serão tratados como atualização somente após a etapa de confirmação."
                            ).classes("text-warning text-body2")

            ui.upload(
                label="Selecionar relatório HMV2670",
                on_upload=handle_upload,
                auto_upload=True,
                max_files=1,
            ).props('accept=".xml,.XML,.xlsx"').classes("w-full")

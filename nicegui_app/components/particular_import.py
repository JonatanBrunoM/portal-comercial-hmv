"""Tela de pré-validação para importação dos relatórios do Particular."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from nicegui import run, ui

from nicegui_app.services.particular_import_validation import inspect_hmv2670
from nicegui_app.services.particular_sheets_service import (
    cross_particular_budgets_with_sheets,
    get_particular_occurrences_preview,
    commit_particular_occurrences_preview,
)
from nicegui_app.services.particular_service import (
    ParticularAccess,
    decide_particular_annulment,
    preflight_particular_import,
    commit_particular_xml_import,
)


def _money_br(value) -> str:
    amount = Decimal(str(value or "0"))
    sign = "- " if amount < 0 else ""
    amount = abs(amount)
    text = f"{amount:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"{sign}R$ {text}"


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
                "O arquivo é analisado antes de qualquer gravação. A persistência no Supabase "
                "só é liberada após pré-validação, conferências e confirmação explícita."
            ).classes("text-body1 text-grey-7")

        with ui.card().classes("w-full p-5 gap-4"):
            with ui.row().classes("w-full items-center justify-between gap-4 flex-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("Relatório de orçamentos confeccionados · HMV2670").classes("text-h6 text-weight-bold")
                    ui.label(
                        "Envie o relatório original .XML ou a versão .XLSX. O Portal identificará automaticamente período, competência, "
                        "quantidade de orçamentos e fechamento financeiro."
                    ).classes("text-body2 text-grey-7")
                ui.badge("PRÉ-VALIDAÇÃO + CONFIRMAÇÃO", color="primary").props("outline")

            result_area = ui.column().classes("w-full gap-4")

            with ui.card().classes("w-full p-4 gap-3 bg-grey-1"):
                with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                    with ui.column().classes("gap-1"):
                        ui.label("Diagnóstico das grades operacionais").classes(
                            "text-subtitle1 text-weight-bold"
                        )
                        ui.label(
                            "Lê GRADE CIRÚRGICA, Negativas e GRADE PONTAL por completo, "
                            "normaliza as ocorrências e valida a estrutura. Nenhum dado é gravado no Supabase."
                        ).classes("text-body2 text-grey-7")
                    grade_preview_button = ui.button(
                        "Analisar grades",
                        icon="fact_check",
                    ).props("outline color=primary")

                grade_preview_area = ui.column().classes("w-full gap-3")

                async def analyze_grades() -> None:
                    grade_preview_button.disable()
                    grade_preview_area.clear()
                    with grade_preview_area:
                        ui.label("Lendo e validando as três grades...").classes(
                            "text-primary text-weight-medium"
                        )
                    try:
                        preview = await run.io_bound(
                            get_particular_occurrences_preview,
                            access,
                        )
                    except Exception as exc:
                        grade_preview_area.clear()
                        with grade_preview_area:
                            ui.label(f"Diagnóstico não concluído: {exc}").classes(
                                "text-negative text-weight-bold"
                            )
                            ui.label(
                                "Nenhuma informação foi gravada no Supabase."
                            ).classes("text-caption text-grey-7")
                        grade_preview_button.enable()
                        return

                    grade_preview_area.clear()
                    with grade_preview_area:
                        ui.label("Leitura das grades concluída").classes(
                            "text-positive text-weight-bold"
                        )
                        with ui.row().classes("w-full gap-3 flex-wrap"):
                            for label, value, icon in (
                                ("Linhas-fonte preservadas", preview.get("source_evidence_rows", preview["total_occurrences"]), "dataset"),
                                ("Ocorrências operacionais consolidadas", preview.get("consolidated_occurrences_count", 0), "event_available"),
                                ("Pendentes de confecção · FAZER", preview.get("to_do_occurrences", 0), "pending_actions"),
                                ("Orçamentos repetidos na mesma grade", preview["repeated_budget_sheet_pairs"], "history"),
                            ):
                                with ui.card().classes("flex-1 min-w-[220px] p-3 gap-1"):
                                    ui.icon(icon, size="22px").classes("text-primary")
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(str(value)).classes("text-h6 text-weight-bold")

                        stats = preview.get("sheet_stats", {})
                        with ui.row().classes("w-full gap-3 flex-wrap"):
                            for sheet_name in ("GRADE CIRÚRGICA", "Negativas", "GRADE PONTAL"):
                                sheet = stats.get(sheet_name, {})
                                with ui.card().classes("flex-1 min-w-[250px] p-3 gap-1"):
                                    ui.label(sheet_name).classes("text-subtitle2 text-weight-bold")
                                    ui.label(
                                        f'{sheet.get("valid_occurrences", 0)} ocorrência(s) válida(s)'
                                    ).classes("text-body2")
                                    ui.label(
                                        f'{sheet.get("to_do_rows", 0)} FAZER · '
                                        f'{sheet.get("invalid_or_missing_date", 0)} com data ausente/inválida'
                                    ).classes("text-caption text-grey-7")
                                    ui.label(
                                        f'{sheet.get("unidentified_budget_rows", 0)} linha(s) preenchida(s) '
                                        'com referência de orçamento não identificada'
                                    ).classes("text-caption text-grey-7")

                        collision_groups = int(preview.get("identity_collision_groups") or 0)
                        if collision_groups:
                            with ui.card().classes("w-full p-4 gap-3 bg-orange-1"):
                                ui.label(
                                    f"Identidades operacionais duplicadas · {collision_groups} grupo(s)"
                                ).classes("text-warning text-weight-bold")
                                ui.label(
                                    f'{preview.get("identity_collision_exact_groups", 0)} grupo(s) têm conteúdo '
                                    f'idêntico e {preview.get("identity_collision_different_groups", 0)} grupo(s) '
                                    "possuem diferenças em campos operacionais."
                                ).classes("text-body2")
                                ui.label(
                                    "A sincronização permanece bloqueada. O quadro abaixo mostra quais campos "
                                    "realmente diferenciam as linhas; nenhuma ocorrência será descartada."
                                ).classes("text-caption text-grey-7")

                                exact_sizes = preview.get("identity_collision_exact_size_counts") or {}
                                exact_distances = preview.get("identity_collision_exact_distance_counts") or {}
                                if exact_sizes:
                                    size_text = " · ".join(
                                        f"{count} grupo(s) com {size} linhas"
                                        for size, count in exact_sizes.items()
                                    )
                                    ui.label(f"Repetições exatas: {size_text}").classes(
                                        "text-body2 text-weight-medium"
                                    )
                                if exact_distances:
                                    distance_text = " · ".join(
                                        f"distância {distance}: {count} grupo(s)"
                                        for distance, count in list(exact_distances.items())[:12]
                                    )
                                    ui.label(
                                        f"Menor distância entre linhas idênticas: {distance_text}"
                                    ).classes("text-caption text-grey-7")

                                exact_details = preview.get("identity_collision_exact_details") or []
                                if exact_details:
                                    with ui.expansion(
                                        f"Inspecionar repetições integralmente idênticas · {len(exact_details)} amostra(s)",
                                        icon="content_copy",
                                    ).classes("w-full border rounded"):
                                        for row in exact_details:
                                            budget_label = (
                                                str(row.get("budget_number"))
                                                if row.get("budget_number") is not None
                                                else row.get("budget_reference_raw") or "—"
                                            )
                                            lines = ", ".join(
                                                str(number) for number in row.get("row_numbers") or []
                                            )
                                            ui.label(
                                                f'{row.get("source_sheet")} · {budget_label} · '
                                                f'aviso {row.get("notice_number") or "—"} · '
                                                f'{_date_br(row.get("procedure_date"))} · '
                                                f'{row.get("patient_name") or "—"} · '
                                                f'{row.get("occurrences")}x · linhas {lines} · '
                                                f'distância mínima {row.get("min_row_distance", 0)}'
                                            ).classes("text-caption")

                                for index, group in enumerate(
                                    preview.get("identity_collision_details", [])[:20],
                                    start=1,
                                ):
                                    rows_group = group.get("rows") or []
                                    if not rows_group:
                                        continue
                                    first = rows_group[0]
                                    budget_label = (
                                        str(first.get("budget_number"))
                                        if first.get("budget_number") is not None
                                        else first.get("budget_reference_raw") or "—"
                                    )
                                    varying = ", ".join(group.get("varying_fields") or []) or "nenhum"
                                    with ui.expansion(
                                        f'Grupo {index} · {first.get("source_sheet")} · {budget_label} · '
                                        f'aviso {first.get("notice_number") or "—"} · '
                                        f'{_date_br(first.get("procedure_date"))} · diferenças: {varying}',
                                        icon="difference",
                                    ).classes("w-full border rounded"):
                                        for row in rows_group:
                                            ui.label(
                                                f'Linha {row.get("source_row_number")} · '
                                                f'valor {_money_br(row.get("operational_value")) if row.get("operational_value") is not None else "—"} · '
                                                f'médico {row.get("doctor_name") or "—"} · '
                                                f'diferencial {row.get("differential") or "—"} · '
                                                f'tipo/valor negativa {row.get("negative_type_value") or "—"} · '
                                                f'contato {row.get("contact_status") or "—"} · '
                                                f'confirmação {row.get("patient_confirmation") or "—"} · '
                                                f'evolução {row.get("evolution_status") or "—"}'
                                            ).classes("text-caption")
                                            ui.label(
                                                f'Observação: {row.get("notes_original") or "—"}'
                                            ).classes("text-caption text-grey-7")
                                            ui.label(
                                                f'Hash: {row.get("source_row_hash") or "—"}'
                                            ).classes("text-caption text-grey-6")

                        occurrences = preview.get("occurrences", [])
                        attention = [
                            row for row in occurrences
                            if row.get("procedure_date") is None
                            or row.get("budget_number") == 84992
                            or row.get("budget_reference_status") == "TO_DO"
                        ]
                        if attention:
                            with ui.expansion(
                                f"Inspecionar amostra de validação · {len(attention)} ocorrência(s)",
                                icon="manage_search",
                            ).classes("w-full border rounded"):
                                rows = [
                                    {
                                        "budget": (
                                            str(row.get("budget_number"))
                                            if row.get("budget_number") is not None
                                            else row.get("budget_reference_raw") or "—"
                                        ),
                                        "reference_status": row.get("budget_reference_status") or "—",
                                        "sheet": row.get("source_sheet"),
                                        "date": _date_br(row.get("procedure_date")),
                                        "notice": row.get("notice_number") or "—",
                                        "location": row.get("location") or "—",
                                        "value": _money_br(row.get("operational_value"))
                                        if row.get("operational_value") is not None else "—",
                                        "row": row.get("source_row_number"),
                                    }
                                    for row in attention[:100]
                                ]
                                ui.table(
                                    columns=[
                                        {"name": "budget", "label": "Orçamento / referência", "field": "budget"},
                                        {"name": "reference_status", "label": "Situação referência", "field": "reference_status"},
                                        {"name": "sheet", "label": "Grade", "field": "sheet"},
                                        {"name": "date", "label": "Data", "field": "date"},
                                        {"name": "notice", "label": "Aviso", "field": "notice"},
                                        {"name": "location", "label": "Local", "field": "location"},
                                        {"name": "value", "label": "Valor", "field": "value", "align": "right"},
                                        {"name": "row", "label": "Linha fonte", "field": "row", "align": "right"},
                                    ],
                                    rows=rows,
                                    row_key="row",
                                    pagination={"rowsPerPage": 10},
                                ).classes("w-full").props("dense flat bordered wrap-cells")

                        ui.label(
                            "Diagnóstico concluído. Até este ponto nenhuma ocorrência foi persistida."
                        ).classes("text-caption text-grey-7")
                        ui.label(
                            f'{preview.get("source_evidence_rows", preview["total_occurrences"])} linha(s)-fonte → '
                            f'{preview.get("consolidated_occurrences_count", 0)} ocorrência(s) operacional(is) '
                            f'consolidada(s) · {preview.get("consolidated_conflict_occurrences", 0)} '
                            "com evidências divergentes preservadas para análise."
                        ).classes("text-body2 text-weight-medium")

                        if access.can_write:
                            ui.separator()
                            with ui.card().classes("w-full p-4 gap-3 border border-primary"):
                                ui.label("Sincronização das grades no Supabase").classes(
                                    "text-subtitle1 text-weight-bold"
                                )
                                ui.label(
                                    "A gravação utilizará exatamente esta fotografia já analisada. "
                                    "Orçamentos identificados serão relacionados à base e referências FAZER "
                                    "serão preservadas sem criar orçamento fictício."
                                ).classes("text-body2 text-grey-7")
                                grade_sync_status = ui.column().classes("w-full gap-2")

                                with ui.dialog() as grade_sync_dialog, ui.card().classes("p-5 gap-4"):
                                    ui.label("Confirmar sincronização das grades?").classes(
                                        "text-h6 text-weight-bold"
                                    )
                                    ui.label(
                                        f'{preview.get("source_evidence_rows", preview["total_occurrences"])} linha(s)-fonte e '
                                        f'{preview.get("consolidated_occurrences_count", 0)} ocorrência(s) consolidada(s) '
                                        "serão enviadas pelo protocolo V3 em lotes controlados. Cada lote é validado "
                                        "pelo banco e a sincronização só é finalizada após a conferência dos totais."
                                    ).classes("text-body2")
                                    ui.label(
                                        f'{preview.get("to_do_occurrences", 0)} ocorrência(s) possuem referência '
                                        "FAZER e permanecerão sem budget_id até existir evidência segura de vínculo."
                                    ).classes("text-body2 text-weight-medium")

                                    async def execute_grade_sync() -> None:
                                        grade_sync_confirm_button.disable()
                                        grade_sync_button.disable()
                                        grade_sync_dialog.close()
                                        grade_sync_status.clear()
                                        with grade_sync_status:
                                            ui.label("Sincronizando fotografia validada...").classes(
                                                "text-primary text-weight-bold"
                                            )
                                        try:
                                            sync_result = await run.io_bound(
                                                commit_particular_occurrences_preview,
                                                access,
                                                preview,
                                            )
                                        except Exception as exc:
                                            grade_sync_status.clear()
                                            with grade_sync_status:
                                                ui.label(
                                                    f"Sincronização não concluída: {exc}"
                                                ).classes("text-negative text-weight-bold")
                                                ui.label(
                                                    "Nenhuma correção automática foi aplicada. "
                                                    "Revise a mensagem antes de tentar novamente."
                                                ).classes("text-caption text-grey-7")
                                            grade_sync_button.enable()
                                            grade_sync_confirm_button.enable()
                                            return

                                        grade_sync_status.clear()
                                        with grade_sync_status:
                                            ui.label("Grades sincronizadas e auditadas.").classes(
                                                "text-positive text-h6 text-weight-bold"
                                            )
                                            ui.label(
                                                f'Sync {sync_result.get("sync_id", "—")} · '
                                                f'{sync_result.get("source_rows", preview.get("source_evidence_rows", 0))} '
                                                "linha(s)-fonte preservada(s) · "
                                                f'{sync_result.get("consolidated_occurrences", preview.get("consolidated_occurrences_count", 0))} '
                                                "ocorrência(s) consolidada(s) · "
                                                f'{sync_result.get("expected_batches", 0)} lote(s) V3 concluído(s).'
                                            ).classes("text-body2")
                                        ui.notify(
                                            "Sincronização das grades concluída.",
                                            color="positive",
                                        )

                                    with ui.row().classes("w-full justify-end gap-2"):
                                        ui.button(
                                            "Cancelar",
                                            on_click=grade_sync_dialog.close,
                                        ).props("flat")
                                        grade_sync_confirm_button = ui.button(
                                            "Confirmar sincronização",
                                            icon="sync",
                                            on_click=execute_grade_sync,
                                        ).props("color=primary")

                                grade_sync_button = ui.button(
                                    "Sincronizar grades no Supabase",
                                    icon="cloud_sync",
                                    on_click=grade_sync_dialog.open,
                                ).props("color=primary")
                                ui.label(
                                    "Baseline V3: todas as linhas-fonte serão preservadas como evidência, os grupos "
                                    "semânticos não serão divididos entre lotes e nenhuma classificação operacional "
                                    "será inferida automaticamente."
                                ).classes("text-caption text-grey-7")
                    grade_preview_button.enable()

                grade_preview_button.on("click", analyze_grades)

            async def handle_upload(event) -> None:
                result_area.clear()
                try:
                    content = await event.file.read()
                    filename = event.file.name
                    with result_area:
                        ui.label("Analisando estrutura e integridade do relatório...").classes("text-body2 text-grey-7")
                    result = await run.io_bound(inspect_hmv2670, content, filename)
                    preflight = None
                    grade_cross = None
                    if result.get("valid_for_import"):
                        preflight = await run.io_bound(
                            preflight_particular_import,
                            access=access,
                            validated_report=result,
                        )
                        grade_cross = await run.io_bound(
                            cross_particular_budgets_with_sheets,
                            access,
                            [
                                record.get("SEQ_ORCAMENTO")
                                for record in result.get("budget_records", [])
                            ],
                        )
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
                                ("Total bruto do arquivo", result["total_value_label"]),
                            ):
                                with ui.card().classes("flex-1 min-w-[220px] p-4 gap-1"):
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(value).classes("text-h5 text-weight-bold")

                    if grade_cross is not None:
                        with ui.card().classes("w-full p-4 gap-3"):
                            ui.label("Cruzamento HMV2670 × grades").classes("text-subtitle1 text-weight-bold")
                            ui.label(
                                "Chave de relacionamento: nº do orçamento. Repetições na mesma grade são "
                                "tratadas como histórico do mesmo caso e não duplicam o orçamento."
                            ).classes("text-body2 text-grey-7")

                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                for label, value, icon in (
                                    ("Orçamentos no XML", grade_cross["total_xml"], "receipt_long"),
                                    ("Encontrados nas grades", grade_cross["found_any_grade"], "link"),
                                    ("Sem grade", grade_cross["without_grade"], "link_off"),
                                    ("Em múltiplas grades", grade_cross["multiple_grades"], "account_tree"),
                                ):
                                    with ui.card().classes("flex-1 min-w-[180px] p-3 gap-1"):
                                        ui.icon(icon, size="22px").classes("text-primary")
                                        ui.label(label).classes("text-caption text-grey-7")
                                        ui.label(str(value)).classes("text-h6 text-weight-bold")

                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                for name in ("GRADE CIRÚRGICA", "Negativas", "GRADE PONTAL"):
                                    with ui.column().classes("flex-1 min-w-[180px] gap-0"):
                                        ui.label(name).classes("text-caption text-grey-7")
                                        ui.label(
                                            f'{grade_cross["by_sheet"].get(name, 0)} orçamento(s) do XML'
                                        ).classes("text-subtitle1 text-weight-bold")

                            ui.label(
                                f'{grade_cross["repeated_history"]} orçamento(s) possuem repetição dentro de '
                                "uma grade, preservada como sinal de histórico/reagendamento."
                            ).classes("text-caption text-grey-7")

                            contexts = grade_cross.get("context_counts", {})
                            if contexts:
                                context_text = " · ".join(
                                    f"{name}: {qty}"
                                    for name, qty in sorted(contexts.items())
                                )
                                ui.label(context_text).classes("text-body2")

                            exceptional = [
                                row for row in grade_cross.get("cases", [])
                                if row.get("context") in {
                                    "SEM GRADE",
                                    "NEGATIVA TOTAL",
                                    "TRANSFERÊNCIA SEDE ↔ PONTAL",
                                    "REVISAR PONTAL + NEGATIVAS",
                                    "REVISAR FLUXO MÚLTIPLO",
                                }
                                or row.get("has_repeated_history")
                            ]
                            if exceptional:
                                with ui.expansion(
                                    f"Detalhar cruzamento · {len(exceptional)} caso(s) de atenção/histórico",
                                    icon="manage_search",
                                ).classes("w-full border rounded"):
                                    rows = []
                                    for row in exceptional:
                                        grades = row.get("grades") or []
                                        occurrences = row.get("grade_occurrences") or {}
                                        grade_text = ", ".join(
                                            f"{name} ({occurrences.get(name, 1)}x)"
                                            for name in grades
                                        ) or "—"
                                        rows.append({
                                            "budget": row["budget_number"],
                                            "context": row["context"],
                                            "grades": grade_text,
                                        })
                                    ui.table(
                                        columns=[
                                            {"name": "budget", "label": "Orçamento", "field": "budget"},
                                            {"name": "context", "label": "Contexto", "field": "context"},
                                            {"name": "grades", "label": "Grades / ocorrências", "field": "grades"},
                                        ],
                                        rows=rows,
                                        row_key="budget",
                                        pagination={"rowsPerPage": 10},
                                    ).classes("w-full").props("dense flat bordered wrap-cells")

                    if result.get("annulment_candidate_count"):
                        with ui.card().classes("w-full p-4 gap-3"):
                            ui.label("Possíveis anulações · conferência operacional").classes("text-subtitle1 text-weight-bold text-warning")
                            ui.label(
                                "O HMV2670 não informa ANULADO como status confiável. O Portal mantém a evidência "
                                "detectada no arquivo e cruza o achado com a decisão humana já registrada na base."
                            ).classes("text-body2 text-grey-7")

                            signal_labels = {
                                "TOTAL_ZERO": "total zerado",
                                "TOTAL_ZERO_COM_ITENS": "total zerado com itens",
                                "PACIENTE_AUSENTE": "paciente ausente",
                                "MEDICO_AUSENTE": "médico ausente",
                                "SOLICITANTE_AUSENTE": "solicitante ausente",
                                "PACIENTE_NOME_ATIPICO": "nome do paciente atípico",
                                "ITENS_VALORIZADOS_CABECALHO_ZERO": "itens valorizados com cabeçalho zerado",
                            }
                            reviews = (preflight or {}).get("annulment_reviews", {})
                            signal_count = (preflight or {}).get(
                                "annulment_signal_count", result.get("annulment_candidate_count", 0)
                            )
                            reviewed_count = (preflight or {}).get("annulment_reviewed_count", 0)
                            pending_count = (preflight or {}).get(
                                "annulment_pending_count", result.get("annulment_candidate_count", 0)
                            )

                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                for label, value, icon in (
                                    ("Sinais detectados", signal_count, "manage_search"),
                                    ("Já revisados", reviewed_count, "fact_check"),
                                    ("Pendentes", pending_count, "pending_actions"),
                                ):
                                    with ui.card().classes("flex-1 min-w-[180px] p-3 gap-1"):
                                        ui.icon(icon, size="22px").classes("text-primary")
                                        ui.label(label).classes("text-caption text-grey-7")
                                        ui.label(str(value)).classes("text-h6 text-weight-bold")

                            for candidate in result.get("annulment_candidates", []):
                                budget_number = int(candidate.get("budget_number"))
                                review = reviews.get(budget_number) or reviews.get(str(budget_number)) or {}
                                review_state = str(review.get("review_state") or "PENDING").upper()
                                signals_text = ", ".join(
                                    signal_labels.get(signal, signal)
                                    for signal in candidate.get("signals", [])
                                )

                                if review_state == "CONFIRMED":
                                    title = f"Anulação confirmada · orçamento {budget_number}"
                                    icon = "block"
                                elif review_state == "NORMAL_REVIEWED":
                                    title = f"Revisado como normal · orçamento {budget_number}"
                                    icon = "verified"
                                else:
                                    title = f"Requer revisão · orçamento {budget_number}"
                                    icon = "fact_check"

                                with ui.expansion(title, icon=icon).classes("w-full border rounded"):
                                    ui.label(f"Evidências: {signals_text}").classes("text-body2")
                                    ui.label(
                                        f"Valor informado no arquivo: {_money_br(candidate.get('total_value'))}"
                                    ).classes("text-body2 text-weight-medium")

                                    if review_state in {"CONFIRMED", "NORMAL_REVIEWED"}:
                                        if review_state == "CONFIRMED":
                                            ui.label("Decisão vigente: ANULAÇÃO CONFIRMADA").classes(
                                                "text-negative text-weight-bold"
                                            )
                                        else:
                                            ui.label("Decisão vigente: ORÇAMENTO NORMAL").classes(
                                                "text-positive text-weight-bold"
                                            )
                                        if review.get("reason"):
                                            ui.label(f"Justificativa: {review['reason']}").classes("text-body2 text-grey-7")
                                        ui.label(
                                            "A evidência continua visível para auditoria, mas não exige nova conferência."
                                        ).classes("text-caption text-grey-7")
                                        continue

                                    if not access.can_write:
                                        ui.label(
                                            "Seu perfil pode consultar a evidência, mas não registrar a decisão."
                                        ).classes("text-caption text-grey-7")
                                        continue

                                    reason = ui.textarea(
                                        "Justificativa da decisão",
                                        placeholder="Descreva a conferência realizada antes de confirmar.",
                                    ).props("outlined autogrow maxlength=1000").classes("w-full")
                                    decision_area = ui.column().classes("w-full gap-2")

                                    async def decide_candidate(
                                        decision: str,
                                        *,
                                        number: int = budget_number,
                                        reason_input=reason,
                                        area=decision_area,
                                    ) -> None:
                                        justification = str(reason_input.value or "").strip()
                                        if not justification:
                                            ui.notify("Informe a justificativa da decisão.", type="warning")
                                            return
                                        try:
                                            saved = await run.io_bound(
                                                decide_particular_annulment,
                                                access=access,
                                                budget_number=number,
                                                decision=decision,
                                                reason=justification,
                                            )
                                        except Exception as exc:
                                            ui.notify(f"Não foi possível registrar a decisão: {exc}", type="negative")
                                            return

                                        area.clear()
                                        with area:
                                            status = str(saved.get("annulment_status") or decision).upper()
                                            if status == "CONFIRMED":
                                                ui.label("Anulação confirmada e persistida na base.").classes(
                                                    "text-negative text-weight-bold"
                                                )
                                            else:
                                                ui.label("Orçamento confirmado como normal.").classes(
                                                    "text-positive text-weight-bold"
                                                )
                                            ui.label(
                                                "Reenvie o relatório para atualizar o resumo de revisões desta análise."
                                            ).classes("text-caption text-grey-7")
                                        reason_input.disable()
                                        ui.notify("Decisão registrada com rastreabilidade.", type="positive")

                                    with ui.row().classes("w-full gap-2 flex-wrap"):
                                        ui.button(
                                            "Confirmar como normal",
                                            icon="check_circle",
                                            on_click=lambda _, fn=decide_candidate: fn("NORMAL"),
                                        ).props("outline")
                                        ui.button(
                                            "Confirmar anulação",
                                            icon="block",
                                            on_click=lambda _, fn=decide_candidate: fn("CONFIRMED"),
                                        ).props("color=negative")

                                    decision_area

                    ui.label("Validações").classes("text-subtitle1 text-weight-bold")
                    annulment_pending = (preflight or {}).get("annulment_pending_count")
                    annulment_reviewed = (preflight or {}).get("annulment_reviewed_count", 0)
                    annulment_signals = (preflight or {}).get(
                        "annulment_signal_count", result.get("annulment_candidate_count", 0)
                    )
                    for issue in result.get("issues", []):
                        severity = issue.get("severity")
                        message = issue.get("message", "")

                        if (
                            preflight is not None
                            and result.get("annulment_candidate_count")
                            and "anula" in str(message).lower()
                            and "confer" in str(message).lower()
                        ):
                            if annulment_pending == 0:
                                severity = "OK"
                                message = (
                                    f"{annulment_signals} orçamento(s) apresentaram sinais compatíveis com "
                                    f"cadastro incompleto/anulação; {annulment_reviewed} já foram revisados "
                                    "e não há conferências pendentes."
                                )
                            else:
                                severity = "WARNING"
                                message = (
                                    f"{annulment_signals} orçamento(s) apresentaram sinais compatíveis com "
                                    f"cadastro incompleto/anulação; {annulment_reviewed} já revisado(s) e "
                                    f"{annulment_pending} ainda exigem conferência."
                                )

                        icon = "check_circle" if severity == "OK" else ("warning" if severity == "WARNING" else "error")
                        css = "text-positive" if severity == "OK" else ("text-warning" if severity == "WARNING" else "text-negative")
                        with ui.row().classes("w-full items-start gap-2"):
                            ui.icon(icon, size="20px").classes(css)
                            ui.label(message).classes("text-body2")

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

                        with ui.card().classes("w-full p-4 gap-3"):
                            ui.label("Regra de total mensal").classes("text-subtitle1 text-weight-bold")
                            ui.label(
                                "O valor bruto do arquivo é preservado para auditoria. Somente um orçamento com "
                                "anulação confirmada e persistida na base poderá contribuir com R$ 0,00 para o total "
                                "mensal. Sinais detectados no XML não excluem valores automaticamente."
                            ).classes("text-body2 text-grey-7")
                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                for label, value in (
                                    ("Bruto do arquivo", _money_br(preflight.get("raw_total_value"))),
                                    ("Anulados confirmados excluídos", _money_br(preflight.get("annulled_value"))),
                                    ("Total considerado no mês", _money_br(preflight.get("effective_total_value"))),
                                ):
                                    with ui.column().classes("flex-1 min-w-[190px] gap-0"):
                                        ui.label(label).classes("text-caption text-grey-7")
                                        ui.label(value).classes("text-h6 text-weight-bold")
                            ui.label(
                                f'{preflight.get("effective_count", preflight["total_file"])} orçamento(s) considerados · '
                                f'{preflight.get("annulled_count", 0)} anulado(s) excluído(s) do total.'
                            ).classes("text-caption text-grey-7")
                            if preflight.get("annulled_numbers"):
                                numbers = ", ".join(str(value) for value in preflight["annulled_numbers"])
                                ui.label(f"Anulados identificados: {numbers}").classes("text-warning text-body2")

                        if preflight["safe_to_import"]:
                            ui.label(
                                "Preflight concluído: nenhum conflito estrutural foi encontrado. "
                                "A gravação poderá ser confirmada ao final desta análise."
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

                            details = preflight.get("changed_details", [])
                            total_proc = sum((Decimal(row["diff_procedure"]) for row in details), Decimal("0"))
                            total_mat = sum((Decimal(row["diff_material"]) for row in details), Decimal("0"))
                            total_diff = sum((Decimal(row["diff_total"]) for row in details), Decimal("0"))

                            with ui.card().classes("w-full p-4 gap-3"):
                                ui.label("Diferenças financeiras detectadas").classes("text-subtitle1 text-weight-bold")
                                with ui.row().classes("w-full gap-3 flex-wrap"):
                                    for label, value in (
                                        ("Δ Procedimentos", _money_br(total_proc)),
                                        ("Δ Materiais", _money_br(total_mat)),
                                        ("Δ Total", _money_br(total_diff)),
                                    ):
                                        with ui.column().classes("flex-1 min-w-[180px] gap-0"):
                                            ui.label(label).classes("text-caption text-grey-7")
                                            ui.label(value).classes("text-h6 text-weight-bold")

                                columns = [
                                    {"name": "budget", "label": "Orçamento", "field": "budget", "align": "left"},
                                    {"name": "date", "label": "Data", "field": "date", "align": "left"},
                                    {"name": "proc_old", "label": "Proced. anterior", "field": "proc_old", "align": "right"},
                                    {"name": "proc_new", "label": "Proced. novo", "field": "proc_new", "align": "right"},
                                    {"name": "proc_diff", "label": "Δ Proced.", "field": "proc_diff", "align": "right"},
                                    {"name": "mat_old", "label": "Material anterior", "field": "mat_old", "align": "right"},
                                    {"name": "mat_new", "label": "Material novo", "field": "mat_new", "align": "right"},
                                    {"name": "mat_diff", "label": "Δ Material", "field": "mat_diff", "align": "right"},
                                    {"name": "total_old", "label": "Total anterior", "field": "total_old", "align": "right"},
                                    {"name": "total_new", "label": "Total novo", "field": "total_new", "align": "right"},
                                    {"name": "total_diff", "label": "Δ Total", "field": "total_diff", "align": "right"},
                                ]
                                rows = [
                                    {
                                        "budget": str(row["budget_number"]),
                                        "date": _date_br(row["budget_date"]),
                                        "proc_old": _money_br(row["old_procedure"]),
                                        "proc_new": _money_br(row["new_procedure"]),
                                        "proc_diff": _money_br(row["diff_procedure"]),
                                        "mat_old": _money_br(row["old_material"]),
                                        "mat_new": _money_br(row["new_material"]),
                                        "mat_diff": _money_br(row["diff_material"]),
                                        "total_old": _money_br(row["old_total"]),
                                        "total_new": _money_br(row["new_total"]),
                                        "total_diff": _money_br(row["diff_total"]),
                                    }
                                    for row in details
                                    if any(Decimal(row[key]) != 0 for key in ("diff_procedure", "diff_material", "diff_total"))
                                ]
                                ui.table(
                                    columns=columns,
                                    rows=rows,
                                    row_key="budget",
                                    pagination={"rowsPerPage": 10},
                                ).classes("w-full").props("dense flat bordered wrap-cells")
                                ui.label(
                                    "A tabela mostra somente diferenças financeiras entre o valor ORIGINAL vigente "
                                    "na base e o novo XML. Nenhuma alteração foi gravada."
                                ).classes("text-caption text-grey-7")

                            comparisons = preflight.get("item_comparison", {})
                            if comparisons:
                                with ui.expansion(
                                    "Explicar alterações pelos itens",
                                    icon="manage_search",
                                ).classes("w-full border rounded"):
                                    for detail in details:
                                        number = int(detail["budget_number"])
                                        comparison = comparisons.get(number) or comparisons.get(str(number)) or {}
                                        added_items = comparison.get("added", [])
                                        removed_items = comparison.get("removed", [])
                                        modified_items = comparison.get("modified", [])
                                        unchanged_items = comparison.get("unchanged", False)

                                        with ui.expansion(
                                            f'Orçamento {number} · {_date_br(detail["budget_date"])}',
                                            icon="receipt_long",
                                        ).classes("w-full"):
                                            item_delta = comparison.get("item_delta", "0")
                                            residual_delta = comparison.get("residual_delta", "0")
                                            total_delta = comparison.get("total_delta", detail.get("delta_total", "0"))
                                            reconciled = comparison.get("reconciled", False)

                                            with ui.card().classes("w-full bg-blue-1"):
                                                ui.label("Explicação da variação").classes("text-subtitle2 text-weight-bold")
                                                ui.label(
                                                    f'Itens detalhados: {_money_br(item_delta)} · '
                                                    f'Fora dos itens detalhados: {_money_br(residual_delta)} · '
                                                    f'Variação total: {_money_br(total_delta)}'
                                                ).classes("text-body2")
                                                if reconciled:
                                                    ui.label(
                                                        "Conciliação fechada: as parcelas explicadas correspondem à variação total."
                                                    ).classes("text-positive text-weight-medium")
                                                else:
                                                    ui.label(
                                                        "Conciliação não fechou. Revisão obrigatória antes de qualquer gravação."
                                                    ).classes("text-negative text-weight-bold")

                                            if unchanged_items:
                                                ui.label(
                                                    "Itens sem alteração. A diferença está no cabeçalho financeiro do orçamento."
                                                ).classes("text-positive text-weight-medium")
                                            else:
                                                ui.label(
                                                    f'{len(added_items)} incluído(s) · '
                                                    f'{len(removed_items)} removido(s) · '
                                                    f'{len(modified_items)} alterado(s)'
                                                ).classes("text-body2 text-weight-medium")

                                                for title, items, icon in (
                                                    ("Itens incluídos", added_items, "add_circle"),
                                                    ("Itens removidos", removed_items, "remove_circle"),
                                                ):
                                                    if items:
                                                        ui.label(title).classes("text-subtitle2 text-weight-bold")
                                                        item_rows = [
                                                            {
                                                                "code": row["item_code"],
                                                                "description": row["description"],
                                                                "quantity": row["quantity"],
                                                                "unit": _money_br(row["unit_value"]),
                                                                "total": _money_br(row["total_value"]),
                                                            }
                                                            for row in items
                                                        ]
                                                        ui.table(
                                                            columns=[
                                                                {"name": "code", "label": "Código", "field": "code"},
                                                                {"name": "description", "label": "Descrição", "field": "description"},
                                                                {"name": "quantity", "label": "Qtd.", "field": "quantity", "align": "right"},
                                                                {"name": "unit", "label": "Valor unit.", "field": "unit", "align": "right"},
                                                                {"name": "total", "label": "Total", "field": "total", "align": "right"},
                                                            ],
                                                            rows=item_rows,
                                                            row_key="code",
                                                            pagination={"rowsPerPage": 5},
                                                        ).classes("w-full").props("dense flat bordered")

                                                if modified_items:
                                                    ui.label("Itens alterados").classes("text-subtitle2 text-weight-bold")
                                                    mod_rows = [
                                                        {
                                                            "code": row["item_code"],
                                                            "description": row["description"],
                                                            "changes": ", ".join(row["changes"]),
                                                            "qty": f'{row["old_quantity"]} → {row["new_quantity"]}',
                                                            "unit": f'{_money_br(row["old_unit_value"])} → {_money_br(row["new_unit_value"])}',
                                                            "total": f'{_money_br(row["old_total_value"])} → {_money_br(row["new_total_value"])}',
                                                        }
                                                        for row in modified_items
                                                    ]
                                                    ui.table(
                                                        columns=[
                                                            {"name": "code", "label": "Código", "field": "code"},
                                                            {"name": "description", "label": "Descrição", "field": "description"},
                                                            {"name": "changes", "label": "Alteração", "field": "changes"},
                                                            {"name": "qty", "label": "Quantidade", "field": "qty"},
                                                            {"name": "unit", "label": "Valor unit.", "field": "unit"},
                                                            {"name": "total", "label": "Total", "field": "total"},
                                                        ],
                                                        rows=mod_rows,
                                                        row_key="code",
                                                        pagination={"rowsPerPage": 5},
                                                    ).classes("w-full").props("dense flat bordered")

                        if (
                            preflight["safe_to_import"]
                            and int(preflight.get("annulment_pending_count") or 0) == 0
                            and result.get("source_format") == "XML"
                        ):
                            ui.separator()
                            with ui.card().classes("w-full p-4 gap-3 border border-primary"):
                                ui.label("Gravação real no Supabase").classes("text-h6 text-weight-bold")
                                ui.label(
                                    "Esta ação persistirá orçamentos, identidade, itens e o valor ORIGINAL "
                                    "do HMV2670. A operação é atômica: se qualquer orçamento ou item falhar, "
                                    "as alterações do lote são revertidas."
                                ).classes("text-body2 text-grey-7")

                                import_status_area = ui.column().classes("w-full gap-2")

                                with ui.dialog() as confirm_import_dialog, ui.card().classes("p-5 gap-4"):
                                    ui.label("Confirmar importação real?").classes("text-h6 text-weight-bold")
                                    ui.label(
                                        f'{preflight["total_file"]} orçamento(s) serão processados. '
                                        f'{preflight["new_count"]} novo(s), '
                                        f'{preflight["changed_count"]} com alteração e '
                                        f'{preflight["identical_count"]} já existente(s) idêntico(s).'
                                    ).classes("text-body2")
                                    ui.label(
                                        f'Total bruto auditável: {_money_br(preflight.get("raw_total_value"))} · '
                                        f'Total gerencial após anulações confirmadas: '
                                        f'{_money_br(preflight.get("effective_total_value"))}.'
                                    ).classes("text-body2 text-weight-medium")

                                    async def execute_real_import() -> None:
                                        confirm_import_button.disable()
                                        import_button.disable()
                                        confirm_import_dialog.close()
                                        import_status_area.clear()
                                        with import_status_area:
                                            ui.label(
                                                "Gravando lote validado no Supabase..."
                                            ).classes("text-primary text-weight-bold")
                                        try:
                                            commit_result = await run.io_bound(
                                                commit_particular_xml_import,
                                                access=access,
                                                validated_report=result,
                                                preflight=preflight,
                                            )
                                        except Exception as exc:
                                            import_status_area.clear()
                                            with import_status_area:
                                                ui.label(
                                                    f"Importação não concluída: {exc}"
                                                ).classes("text-negative text-weight-bold")
                                                ui.label(
                                                    "A transação foi bloqueada/revertida; revise a mensagem antes de tentar novamente."
                                                ).classes("text-caption text-grey-7")
                                            import_button.enable()
                                            confirm_import_button.enable()
                                            return

                                        import_status_area.clear()
                                        with import_status_area:
                                            ui.label(
                                                "Importação concluída e auditada."
                                            ).classes("text-positive text-h6 text-weight-bold")
                                            ui.label(
                                                f'Lote {commit_result.get("batch_id", "—")} · '
                                                f'{commit_result.get("records_processed", 0)} orçamento(s) · '
                                                f'{commit_result.get("items_processed", 0)} item(ns) processado(s) · '
                                                f'{commit_result.get("items_deactivated", 0)} item(ns) antigo(s) desativado(s).'
                                            ).classes("text-body2")
                                            ui.label(
                                                "O mesmo arquivo fica protegido contra importação acidental pela assinatura SHA-256."
                                            ).classes("text-caption text-grey-7")
                                        ui.notify("Importação concluída com sucesso.", color="positive")

                                    with ui.row().classes("w-full justify-end gap-2"):
                                        ui.button(
                                            "Cancelar",
                                            on_click=confirm_import_dialog.close,
                                        ).props("flat")
                                        confirm_import_button = ui.button(
                                            "Confirmar gravação",
                                            icon="save",
                                            on_click=execute_real_import,
                                        ).props("color=primary")

                                import_button = ui.button(
                                    "Confirmar importação real",
                                    icon="cloud_upload",
                                    on_click=confirm_import_dialog.open,
                                ).props("color=primary")
                                ui.label(
                                    "Reenvio do mesmo arquivo concluído é bloqueado pela assinatura SHA-256."
                                ).classes("text-caption text-grey-7")

            ui.upload(
                label="Selecionar relatório HMV2670",
                on_upload=handle_upload,
                auto_upload=True,
                max_files=1,
            ).props('accept=".xml,.XML,.xlsx"').classes("w-full")

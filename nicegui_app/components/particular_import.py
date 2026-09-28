"""Tela de pré-validação para importação dos relatórios do Particular."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from nicegui import run, ui

from nicegui_app.services.particular_import_validation import inspect_hmv2670
from nicegui_app.services.particular_service import (
    ParticularAccess,
    decide_particular_annulment,
    preflight_particular_import,
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
                                ("Total bruto do arquivo", result["total_value_label"]),
                            ):
                                with ui.card().classes("flex-1 min-w-[220px] p-4 gap-1"):
                                    ui.label(label).classes("text-caption text-grey-7")
                                    ui.label(value).classes("text-h5 text-weight-bold")

                    if result.get("annulment_candidate_count"):
                        with ui.card().classes("w-full p-4 gap-3"):
                            ui.label("Possíveis anulações · requer conferência").classes("text-subtitle1 text-weight-bold text-warning")
                            ui.label(
                                "O HMV2670 não informa ANULADO como status confiável. O Portal detecta evidências "
                                "objetivas, mas não retira valor do mês sem confirmação operacional."
                            ).classes("text-body2 text-grey-7")
                            candidate_rows = []
                            signal_labels = {
                                "TOTAL_ZERO": "total zerado",
                                "TOTAL_ZERO_COM_ITENS": "total zerado com itens",
                                "TOTAL_POSITIVO_SEM_ITENS": "total positivo sem itens",
                                "PACIENTE_AUSENTE": "paciente ausente",
                                "MEDICO_AUSENTE": "médico ausente",
                                "SOLICITANTE_AUSENTE": "solicitante ausente",
                                "PACIENTE_NOME_ATIPICO": "nome do paciente atípico",
                                "ITENS_VALORIZADOS_CABECALHO_ZERO": "itens valorizados com cabeçalho zerado",
                            }
                            for candidate in result.get("annulment_candidates", []):
                                candidate_rows.append({
                                    "budget": candidate.get("budget_number"),
                                    "signals": ", ".join(
                                        signal_labels.get(signal, signal)
                                        for signal in candidate.get("signals", [])
                                    ),
                                    "total": _money_br(candidate.get("total_value")),
                                })
                            ui.table(
                                columns=[
                                    {"name": "budget", "label": "Orçamento", "field": "budget", "align": "left"},
                                    {"name": "signals", "label": "Evidências encontradas", "field": "signals", "align": "left"},
                                    {"name": "total", "label": "Valor original", "field": "total", "align": "right"},
                                ],
                                rows=candidate_rows,
                                row_key="budget",
                            ).classes("w-full").props("flat bordered dense")

                            if access.can_write:
                                ui.label(
                                    "Decisão humana · a justificativa é obrigatória e a evidência do arquivo permanece preservada."
                                ).classes("text-caption text-grey-7")
                                for candidate in result.get("annulment_candidates", []):
                                    budget_number = int(candidate.get("budget_number"))
                                    signals_text = ", ".join(
                                        signal_labels.get(signal, signal)
                                        for signal in candidate.get("signals", [])
                                    )
                                    decision_area = ui.column().classes("w-full gap-2")

                                    with ui.expansion(
                                        f"Revisar orçamento {budget_number}",
                                        icon="fact_check",
                                    ).classes("w-full border rounded"):
                                        ui.label(f"Evidências: {signals_text}").classes("text-body2")
                                        ui.label(
                                            f"Valor informado no arquivo: {_money_br(candidate.get('total_value'))}"
                                        ).classes("text-body2 text-weight-medium")
                                        reason = ui.textarea(
                                            "Justificativa da decisão",
                                            placeholder="Descreva a conferência realizada antes de confirmar.",
                                        ).props("outlined autogrow maxlength=1000").classes("w-full")

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
                                                    ui.label(
                                                        "Anulação confirmada e persistida na base."
                                                    ).classes("text-negative text-weight-bold")
                                                else:
                                                    ui.label(
                                                        "Orçamento confirmado como normal."
                                                    ).classes("text-positive text-weight-bold")
                                                ui.label(
                                                    "A decisão já será considerada nas próximas consultas dos indicadores."
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

            ui.upload(
                label="Selecionar relatório HMV2670",
                on_upload=handle_upload,
                auto_upload=True,
                max_files=1,
            ).props('accept=".xml,.XML,.xlsx"').classes("w-full")

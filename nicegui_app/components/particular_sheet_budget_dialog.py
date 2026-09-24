"""Diálogo de consulta das grades a partir de um orçamento operacional."""
from __future__ import annotations

import logging

from nicegui import run, ui

from nicegui_app.services.particular_service import ParticularAccess
from nicegui_app.services.particular_sheets_lookup import get_particular_sheet_budget_matches
from nicegui_app.services.particular_grade_comparison import compare_grade_occurrences

logger = logging.getLogger(__name__)

_LABELS = {
    'data': 'Data', 'aviso': 'Aviso', 'paciente': 'Paciente', 'medico': 'Médico',
    'diferencial': 'Diferencial', 'valor_caixa': 'Valor em caixa',
    'contato': 'Contato', 'confirmacao': 'Confirmação', 'observacao': 'Observação',
    'tipo': 'Tipo', 'unique': 'Unique', 'valor': 'Valor',
    'confirmacao_contato': 'Confirmação de contato', 'evolucao': 'Evolução',
    'confirmacao_paciente': 'Confirmação do paciente',
}


def open_particular_sheet_budget_dialog(*, access: ParticularAccess, budget_number: str) -> None:
    """Consulta as grades sem modificar orçamento, planilha ou conferência MV."""
    if not access.can_read:
        ui.notify('Você não possui acesso às grades.', type='warning')
        return

    number = str(budget_number).strip()
    if not number or len(number) > 20 or not number.isascii() or not number.isdecimal():
        ui.notify('Número de orçamento inválido para consulta às grades.', type='warning')
        return

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl p-5 gap-3'):
        with ui.row().classes('w-full items-center justify-between gap-3'):
            ui.label(f'Orçamento {number} · Registros nas grades').classes('text-lg font-semibold')
            ui.button(icon='close', on_click=dialog.close).props('flat round')
        ui.label('Consulta somente leitura à cópia de testes. Presença nas grades não comprova realização no MV.').classes('text-sm text-gray-600')
        status = ui.label('Consultando as três grades...').classes('text-sm text-gray-600')
        with ui.scroll_area().classes('w-full').style('max-height: 65vh'):
            comparison = ui.column().classes('w-full gap-2')
            results = ui.column().classes('w-full gap-3')
        ui.button('Fechar', on_click=dialog.close).props('outline')

    dialog.open()

    async def load() -> None:
        try:
            data = await run.io_bound(get_particular_sheet_budget_matches, access, number)
        except Exception:
            logger.error('Falha ao consultar as grades para orçamento operacional.')
            if not dialog.is_deleted:
                status.set_text('Não foi possível consultar as grades. Tente novamente.')
            return
        if dialog.is_deleted:
            return
        total = data['total']
        status.set_text(f'{total} ocorrência(s) para o orçamento {number}.' +
                        (' Exibindo somente as primeiras 40.' if data['limitado'] else ''))
        comparison.clear()
        with comparison:
            if total:
                with ui.card().classes('w-full p-3 gap-2 bg-blue-50'):
                    ui.label('Pontos para conferência').classes('font-semibold')
                    ui.label('Comparação informativa apenas entre ocorrências deste orçamento. Não identifica pacientes nem confirma negativa, transferência ou realização no MV.').classes('text-xs text-gray-600')
                    for notice in compare_grade_occurrences(data):
                        ui.label('• ' + notice).classes('text-sm whitespace-pre-wrap break-words')
        results.clear()
        with results:
            if not total:
                ui.label('Nenhuma ocorrência encontrada nas três grades.').classes('text-sm text-gray-600')
            for match in data['ocorrencias']:
                with ui.card().classes('w-full p-3 gap-2'):
                    ui.label(f'{match["aba"]} · Linha {match["linha"]}').classes('font-semibold')
                    with ui.grid().classes('w-full grid-cols-1 md:grid-cols-2 gap-2'):
                        for key, value in match['campos'].items():
                            if value:
                                with ui.column().classes('gap-0'):
                                    ui.label(_LABELS.get(key, key)).classes('text-xs text-gray-600')
                                    ui.label(value).classes('text-sm whitespace-pre-wrap break-words')

    ui.timer(0.1, load, once=True)

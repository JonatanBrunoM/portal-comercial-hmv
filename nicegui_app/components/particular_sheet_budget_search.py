"""Pesquisa de orçamento nas grades, exibida apenas para perfis autorizados."""
from __future__ import annotations

import logging

from nicegui import run, ui

from nicegui_app.services.particular_service import ParticularAccess
from nicegui_app.services.particular_sheets_lookup import get_particular_sheet_budget_matches

logger = logging.getLogger(__name__)

_LABELS = {
    'data': 'Data', 'aviso': 'Aviso', 'paciente': 'Paciente', 'medico': 'Médico',
    'diferencial': 'Diferencial', 'valor_caixa': 'Valor em caixa',
    'contato': 'Contato', 'confirmacao': 'Confirmação', 'observacao': 'Observação',
    'tipo': 'Tipo', 'unique': 'Unique', 'valor': 'Valor',
    'confirmacao_contato': 'Confirmação de contato', 'evolucao': 'Evolução',
    'confirmacao_paciente': 'Confirmação do paciente',
}


def render_particular_sheet_budget_search(*, access: ParticularAccess) -> None:
    if not access.can_read:
        return

    with ui.card().classes('w-full p-4 gap-3'):
        ui.label('Consultar orçamento nas grades').classes('text-lg font-semibold')
        ui.label('Pesquisa na Grade Cirúrgica, Negativas e Grade Pontal. Os registros não confirmam realização no MV.').classes('text-sm text-gray-600')
        with ui.row().classes('w-full items-end gap-3'):
            number_input = ui.input('Número do orçamento', placeholder='Ex.: 84600').props('clearable').classes('w-64')
            search_button = ui.button('Pesquisar nas grades', icon='search')
        status = ui.label('').classes('text-sm text-gray-600')
        results = ui.column().classes('w-full gap-3')

    async def search() -> None:
        number = str(number_input.value or '').strip()
        if not number or len(number) > 20 or not number.isascii() or not number.isdecimal():
            ui.notify('Informe um número de orçamento de até 20 dígitos.', type='warning')
            return
        search_button.disable()
        status.set_text('Consultando as três grades...')
        results.clear()
        try:
            data = await run.io_bound(get_particular_sheet_budget_matches, access, number)
        except ValueError:
            status.set_text('Número de orçamento inválido.')
            return
        except Exception:
            logger.error('Falha na pesquisa autorizada de orçamento nas grades.')
            status.set_text('Não foi possível consultar as grades. Tente novamente.')
            ui.notify('Falha na consulta às grades.', type='negative')
            return
        finally:
            search_button.enable()

        total = data['total']
        status.set_text(f'{total} ocorrência(s) para o orçamento {data["numero"]}.' +
                        (' Exibindo somente as primeiras 40.' if data['limitado'] else ''))
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

    search_button.on('click', search)
    number_input.on('keydown.enter', search)

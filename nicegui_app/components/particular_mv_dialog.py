from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import ui

from nicegui_app.services.particular_service import (
    get_particular_mv_check_context,
    register_particular_mv_check,
)

logger = logging.getLogger(__name__)

OUTCOME_OPTIONS = {
    'PENDING': 'Pendente',
    'REALIZED': 'Realizado',
    'NOT_PERFORMED': 'Não realizado',
    'CANCELLED': 'Cancelado',
}

BUDGET_FIELDS = (
    ('budget_number', 'Número do orçamento'),
    ('budget_date', 'Data de confecção'),
    ('patient_name', 'Paciente'),
    ('doctor_name', 'Médico'),
    ('original_requester', 'Solicitante original'),
    ('origin', 'Origem'),
    ('modality', 'Modalidade'),
    ('location_hint', 'Local'),
    ('state', 'Situação'),
    ('is_liminar', 'Liminar'),
    ('is_international', 'Internacional'),
    ('is_transcription', 'Transcrição'),
)
ITEM_FIELDS = (
    ('source_sequence_original', 'Seq. XML'),
    ('item_code', 'Código'),
    ('description_original', 'Descrição'),
    ('quantity', 'Quantidade'),
    ('unit', 'Unidade'),
    ('unit_value', 'Valor unitário'),
    ('total_value', 'Valor total'),
)
VALUE_FIELDS = (
    ('procedure_value', 'Procedimentos'),
    ('material_value', 'Materiais'),
    ('total_value', 'Total original'),
)


def _text(value: Any) -> str:
    if value is None or str(value).strip() == '':
        return '—'
    if isinstance(value, bool):
        return 'Sim' if value else 'Não'
    return str(value).strip()


def _date(value: Any) -> str:
    if not value:
        return '—'
    try:
        return date.fromisoformat(str(value)[:10]).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return _text(value)


def _money(value: Any) -> str:
    if value is None or str(value).strip() == '':
        return '—'
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return '—'
    except (InvalidOperation, ValueError):
        return _text(value)
    formatted = f'{amount:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')
    return f'R$ {formatted}'


def _field(label: str, value: Any) -> None:
    with ui.column().classes('gap-0 min-w-0'):
        ui.label(label).classes('text-caption text-gray-600')
        ui.label(_text(value)).classes('text-body2 text-weight-medium break-words')


def _section(title: str) -> None:
    ui.label(title).classes('text-subtitle1 text-weight-bold')


def _render_budget(budget: dict[str, Any]) -> None:
    _section('Identificação e classificação')
    with ui.grid(columns=2).classes('w-full gap-4'):
        for key, label in BUDGET_FIELDS:
            if key in budget:
                value = _date(budget.get(key)) if key == 'budget_date' else budget.get(key)
                _field(label, value)

    # Mostra outros campos retornados pela consulta sem presumir que estejam no XML.
    shown = {key for key, _ in BUDGET_FIELDS}
    hidden = {'id', 'patient_name_normalized', 'created_at', 'updated_at',
              'import_batch_id', 'profile_id', 'patient_id'}
    extra = [(key, value) for key, value in budget.items()
             if key not in shown | hidden and value is not None
             and not isinstance(value, (dict, list, tuple))]
    if extra:
        with ui.expansion('Outros dados disponíveis do orçamento').classes('w-full'):
            with ui.grid(columns=2).classes('w-full gap-4'):
                for key, value in extra:
                    _field(key.replace('_', ' ').capitalize(), value)


def _render_items(context: dict[str, Any]) -> None:
    ui.separator()
    _section('Itens do orçamento')
    items = context.get('items')
    if not isinstance(items, list):
        items = context.get('budget_items')
    if not isinstance(items, list):
        ui.label('A consulta atual ainda não disponibiliza os itens do XML nesta janela.').classes(
            'text-sm text-gray-600'
        )
        return
    if not items:
        ui.label('Nenhum item retornado para este orçamento.').classes('text-sm text-gray-600')
        return
    ui.label(f'{len(items)} item(ns) retornado(s).').classes('text-sm text-gray-600')
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        with ui.card().classes('w-full p-3 gap-2'):
            ui.label(f'Item {index}').classes('font-semibold')
            with ui.grid(columns=2).classes('w-full gap-2'):
                for key, label in ITEM_FIELDS:
                    if key in item:
                        value = _money(item.get(key)) if key in {'unit_value', 'total_value'} else item.get(key)
                        _field(label, value)


def _render_values(context: dict[str, Any]) -> None:
    ui.separator()
    _section('Valores originais do orçamento')
    values = context.get('original_values')
    if not isinstance(values, dict):
        values = context.get('values')
    if not isinstance(values, dict):
        ui.label('Os valores originais do XML ainda não são retornados pela consulta atual.').classes(
            'text-sm text-gray-600'
        )
        return
    with ui.grid(columns=2).classes('w-full gap-4'):
        for key, label in VALUE_FIELDS:
            if key in values:
                _field(label, _money(values.get(key)))


def open_particular_mv_dialog(*, access: Any, budget_id: str) -> None:
    """Detalhes disponíveis do orçamento e conferência manual, sem inferir realização."""
    try:
        context = get_particular_mv_check_context(access=access, budget_id=budget_id)
    except Exception:
        logger.exception('Falha ao carregar os detalhes do orçamento no Particular.')
        ui.notify('Não foi possível carregar os detalhes do orçamento.', type='negative')
        return

    budget = context['budget']
    latest_check = context.get('latest_mv_check')
    can_register = access.can_write and str(access.module_role).upper() == 'MANAGER'

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-[1100px] p-0'):
        with ui.row().classes('w-full items-center justify-between gap-4 p-5'):
            with ui.column().classes('gap-1'):
                ui.label('DETALHES DO ORÇAMENTO').classes('text-caption text-weight-bold')
                ui.label(f'Orçamento nº {_text(budget.get("budget_number"))}').classes(
                    'text-h5 text-weight-bold'
                )
            ui.button(icon='close', on_click=dialog.close).props('flat round')
        ui.separator()
        with ui.column().classes('w-full p-5 gap-4').style('max-height: 75vh; overflow-y: auto'):
            _render_budget(budget)
            _render_items(context)
            _render_values(context)
            ui.separator()
            _section('Última conferência registrada no MV')
            ui.label('Somente o registro manual de conferência no MV determina este resultado; as grades não comprovam realização.').classes(
                'text-sm text-gray-600'
            )
            if latest_check:
                _field('Resultado', OUTCOME_OPTIONS.get(latest_check.get('outcome'), _text(latest_check.get('outcome'))))
                with ui.grid(columns=2).classes('w-full gap-4'):
                    for label, key in (
                        ('Data da conferência', 'checked_at'),
                        ('Aviso', 'notice_number'),
                        ('Atendimento', 'attendance_number'),
                        ('Valor da conta', 'account_value'),
                        ('Observações', 'notes'),
                    ):
                        value = _money(latest_check.get(key)) if key == 'account_value' else latest_check.get(key)
                        _field(label, value)
            else:
                ui.label('Nenhuma conferência registrada para este orçamento.').classes('text-body2')

            if can_register:
                ui.separator()
                _section('Registrar nova conferência no MV')
                outcome = ui.select(options=OUTCOME_OPTIONS, label='Resultado da conferência', value='PENDING').classes('w-full')
                notice_number = ui.input(label='Número do aviso (opcional)').classes('w-full')
                attendance_number = ui.input(label='Número do atendimento (opcional)').classes('w-full')
                account_value = ui.input(label='Valor da conta em R$ (opcional)', placeholder='Ex.: 1250,50').classes('w-full')
                notes = ui.textarea(label='Observações da conferência').classes('w-full')
                saving = False

                async def save_check() -> None:
                    nonlocal saving
                    if saving:
                        return
                    saving = True
                    save_button.disable()
                    raw_amount = str(account_value.value or '').strip()
                    normalized_amount = None
                    if raw_amount:
                        try:
                            normalized_amount = Decimal(raw_amount.replace('.', '').replace(',', '.'))
                        except InvalidOperation:
                            saving = False
                            save_button.enable()
                            ui.notify('Informe um valor de conta válido.', type='warning')
                            return
                        if not normalized_amount.is_finite() or normalized_amount < 0:
                            saving = False
                            save_button.enable()
                            ui.notify('O valor da conta deve ser um número válido e não negativo.', type='warning')
                            return
                        normalized_amount = str(normalized_amount)
                    try:
                        register_particular_mv_check(
                            access=access,
                            budget_id=budget_id,
                            outcome=outcome.value,
                            notice_number=notice_number.value,
                            attendance_number=attendance_number.value,
                            account_value=normalized_amount,
                            notes=notes.value,
                        )
                    except Exception:
                        saving = False
                        save_button.enable()
                        ui.notify('Não foi possível registrar a conferência no MV.', type='negative')
                        return
                    ui.notify('Conferência registrada com sucesso.', type='positive')
                    dialog.close()

                with ui.row().classes('w-full justify-end gap-3'):
                    ui.button('Cancelar', on_click=dialog.close).props('flat no-caps')
                    save_button = ui.button('Registrar conferência', icon='save', on_click=save_check).props('unelevated no-caps')
            else:
                ui.label('O registro de conferências é restrito aos gestores.').classes('text-caption')
    dialog.open()

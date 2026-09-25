"""Análise financeira mensal por médico, com CONSULTORIO separado como transcrição."""
from __future__ import annotations

from decimal import Decimal
import unicodedata

from nicegui import run, ui

from nicegui_app.services.particular_doctor_dashboard import list_doctor_monthly
from nicegui_app.services.particular_monthly_dashboard import format_brl
from nicegui_app.services.particular_service import ParticularAccess


_FIELDS = (
    'orcamentos_importados', 'valor_bruto_importado',
    'orcamentos_liberados', 'valor_liberado_duplicidade',
    'orcamentos_aguardando_analise', 'valor_aguardando_analise',
    'orcamentos_excluidos', 'valor_excluido_duplicidade',
    'orcamentos_decisao_incompleta', 'valor_decisao_incompleta',
    'orcamentos_transcricao', 'valor_transcricao', 'orcamentos_valor_nao_validado',
)


def _is_transcription(name: str) -> bool:
    normalized = unicodedata.normalize('NFKD', name or '')
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char)).upper()
    return 'CONSULTORIO' in normalized


def _money(value: object) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def render_doctor_dashboard(access: ParticularAccess, month_select: ui.select, monthly_rows: dict) -> None:
    """Renderiza tabela de médicos ligada ao mesmo seletor do painel mensal."""
    with ui.expansion('Composição financeira por médico', icon='medical_services').classes('w-full border rounded-lg'):
        ui.label('Valores totais dos orçamentos associados ao médico, não honorários nem receita realizada.').classes('text-body2 text-grey-7')
        ui.label('Registros com CONSULTORIO no nome do médico são exibidos separadamente como transcrições.').classes('text-body2 text-grey-7')
        status = ui.column().classes('w-full gap-2')
        table_area = ui.column().classes('w-full gap-3')
        version = 0
        cache: dict[str, list[dict]] = {}

        async def load(month: str | None, force: bool = False) -> None:
            nonlocal version
            version += 1
            request = version
            status.clear()
            table_area.clear()
            if not month or month not in monthly_rows:
                return
            with status:
                ui.label('Carregando composição por médico...').classes('text-caption text-grey-7')
            try:
                if force or month not in cache:
                    cache[month] = await run.io_bound(list_doctor_monthly, access, month)
                rows = cache[month]
                if request != version or month_select.value != month:
                    return
                status.clear()
                monthly = monthly_rows[month]
                if any(
                    sum(_money(record.get(field)) for record in rows) != _money(monthly.get(field))
                    for field in _FIELDS
                ):
                    with status:
                        ui.label('Composição por médico não conciliada com o resumo mensal. Atualize os indicadores antes de utilizar os valores.').classes('text-negative')
                    return
                transcription = [r for r in rows if _is_transcription(str(r.get('medico') or ''))]
                doctors = [r for r in rows if not _is_transcription(str(r.get('medico') or ''))]
                with table_area:
                    if transcription:
                        total = sum((_money(r.get('valor_bruto_importado')) for r in transcription), Decimal(0))
                        identified = sum(int(r.get('orcamentos_importados') or 0) for r in transcription)
                        classified = sum(int(r.get('orcamentos_transcricao') or 0) for r in transcription)
                        classified_value = sum((_money(r.get('valor_transcricao')) for r in transcription), Decimal(0))
                        pending = sum(int(r.get('orcamentos_aguardando_analise') or 0) for r in transcription)
                        excluded = sum(int(r.get('orcamentos_excluidos') or 0) for r in transcription)
                        incomplete = sum(int(r.get('orcamentos_decisao_incompleta') or 0) for r in transcription)
                        ui.label(
                            f'CONSULTORIO identificado: {identified} orçamento(s) · {format_brl(total)} bruto'
                        ).classes('text-subtitle2')
                        ui.label(
                            f'Classificados como transcrição: {classified} orçamento(s) · {format_brl(classified_value)}'
                        ).classes('text-body2 text-grey-8')
                        if pending or excluded or incomplete:
                            ui.label(
                                f'Os demais registros com CONSULTORIO permanecem em classificações prioritárias: '
                                f'{pending} pendente(s), {excluded} excluído(s) por duplicidade e '
                                f'{incomplete} com decisão incompleta.'
                            ).classes('text-caption text-grey-7')
                        inconsistent = sum(int(r.get('orcamentos_liberados') or 0) for r in transcription)
                        if inconsistent:
                            ui.label(
                                f'Atenção: {inconsistent} orçamento(s) com CONSULTORIO ainda aparecem como liberados na visão financeira do banco.'
                            ).classes('text-warning text-weight-bold')
                    if not doctors:
                        ui.label('Nenhum orçamento associado a médico neste mês.').classes('text-caption')
                        return
                    columns = [
                        {'name': 'medico', 'label': 'Médico', 'field': 'medico', 'align': 'left', 'sortable': True},
                        {'name': 'orcamentos', 'label': 'Orçamentos', 'field': 'orcamentos', 'sortable': True},
                        {'name': 'bruto', 'label': 'Bruto importado', 'field': 'bruto', 'sortable': True},
                        {'name': 'liberado', 'label': 'Liberado', 'field': 'liberado', 'sortable': True},
                        {'name': 'retido', 'label': 'Retido', 'field': 'retido', 'sortable': True},
                        {'name': 'excluido', 'label': 'Excluído', 'field': 'excluido', 'sortable': True},
                    ]
                    data = [
                        {
                            'medico': str(r.get('medico') or 'Médico não informado'),
                            'orcamentos': int(r.get('orcamentos_importados') or 0),
                            'bruto': format_brl(r.get('valor_bruto_importado')),
                            'liberado': format_brl(r.get('valor_liberado_duplicidade')),
                            'retido': format_brl(r.get('valor_aguardando_analise')),
                            'excluido': format_brl(r.get('valor_excluido_duplicidade')),
                        }
                        for r in doctors
                    ]
                    ui.table(columns=columns, rows=data, row_key='medico', pagination=10).classes('w-full')
            except Exception:
                if request == version:
                    status.clear()
                    table_area.clear()
                    with status:
                        ui.label('Não foi possível carregar a composição por médico. Confira a visão e as permissões no Supabase.').classes('text-negative')

        month_select.on_value_change(lambda event: load(event.value))
        ui.button('Atualizar composição por médico', icon='refresh', on_click=lambda: load(month_select.value, True)).props('outline no-caps')
        ui.timer(0.2, lambda: load(month_select.value), once=True)

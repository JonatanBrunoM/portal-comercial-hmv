"""Análise mensal da carteira por médico, com CONSULTORIO separado como transcrição."""
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
    """Renderiza a leitura gerencial por médico ligada ao seletor mensal principal."""
    with ui.column().classes('w-full gap-3'):
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
                ui.label('Carregando carteira por médico...').classes('text-caption text-grey-7')

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
                        ui.label(
                            'Composição por médico não conciliada com o resumo mensal. '
                            'Atualize os indicadores antes de utilizar os valores.'
                        ).classes('text-negative')
                    return

                transcription = [r for r in rows if _is_transcription(str(r.get('medico') or ''))]
                doctors = [r for r in rows if not _is_transcription(str(r.get('medico') or ''))]

                with table_area:
                    if not doctors and not transcription:
                        ui.label('Nenhum orçamento associado a médico neste mês.').classes(
                            'text-body2 text-grey-7'
                        )
                        return

                    total_doctors = len(doctors)
                    total_budgets = sum(int(r.get('orcamentos_importados') or 0) for r in doctors)
                    gross_value = sum((_money(r.get('valor_bruto_importado')) for r in doctors), Decimal(0))
                    released_value = sum((_money(r.get('valor_liberado_duplicidade')) for r in doctors), Decimal(0))
                    pending_budgets = sum(int(r.get('orcamentos_aguardando_analise') or 0) for r in doctors)

                    with ui.row().classes('w-full items-end justify-between gap-3 flex-wrap'):
                        with ui.column().classes('gap-0'):
                            ui.label('Carteira por médico').classes('text-subtitle1 text-weight-bold')
                            ui.label(
                                'Distribuição dos orçamentos identificados por médico.'
                            ).classes('text-caption text-grey-7')
                        ui.button(
                            'Atualizar',
                            icon='refresh',
                            on_click=lambda: load(month_select.value, True),
                        ).props('flat dense no-caps').classes('text-primary')

                    with ui.row().classes('w-full gap-3 flex-wrap'):
                        for label, value, note in (
                            ('Médicos identificados', str(total_doctors), f'{total_budgets} orçamento(s)'),
                            ('Valor bruto', format_brl(gross_value), 'Carteira médica identificada'),
                            ('Valor liberado', format_brl(released_value), 'Após decisões de duplicidade'),
                            ('Em análise', str(pending_budgets), 'Orçamento(s) retido(s)'),
                        ):
                            with ui.card().classes('flex-1 min-w-[190px] p-4 gap-1 shadow-sm'):
                                ui.label(label).classes('text-caption text-grey-7')
                                ui.label(value).classes('text-h5 text-weight-bold')
                                ui.label(note).classes('text-caption text-grey-7')

                    if doctors:
                        top = sorted(
                            doctors,
                            key=lambda row: _money(row.get('valor_bruto_importado')),
                            reverse=True,
                        )[:10]

                        with ui.card().classes('w-full p-4 gap-2 shadow-sm'):
                            with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                                ui.label('Maiores carteiras médicas').classes(
                                    'text-subtitle1 text-weight-bold'
                                )
                                ui.label('Top 10 por valor bruto').classes('text-caption text-grey-7')

                            ui.echart({
                                'tooltip': {
                                    'trigger': 'axis',
                                    'axisPointer': {'type': 'shadow'},
                                },
                                'grid': {
                                    'left': 220,
                                    'right': 35,
                                    'bottom': 30,
                                    'top': 20,
                                },
                                'xAxis': {
                                    'type': 'value',
                                    'name': 'R$ mil',
                                    'axisLabel': {'formatter': '{value}'},
                                },
                                'yAxis': {
                                    'type': 'category',
                                    'inverse': True,
                                    'data': [
                                        str(row.get('medico') or 'Médico não informado')
                                        for row in top
                                    ],
                                },
                                'series': [{
                                    'name': 'Valor bruto',
                                    'type': 'bar',
                                    'barMaxWidth': 24,
                                    'data': [
                                        float(
                                            _money(row.get('valor_bruto_importado'))
                                            / Decimal('1000')
                                        )
                                        for row in top
                                    ],
                                }],
                            }).classes('w-full h-[360px]')

                    if transcription:
                        total = sum(
                            (_money(r.get('valor_bruto_importado')) for r in transcription),
                            Decimal(0),
                        )
                        identified = sum(
                            int(r.get('orcamentos_importados') or 0) for r in transcription
                        )
                        classified = sum(
                            int(r.get('orcamentos_transcricao') or 0) for r in transcription
                        )
                        classified_value = sum(
                            (_money(r.get('valor_transcricao')) for r in transcription),
                            Decimal(0),
                        )
                        pending = sum(
                            int(r.get('orcamentos_aguardando_analise') or 0)
                            for r in transcription
                        )
                        excluded = sum(
                            int(r.get('orcamentos_excluidos') or 0) for r in transcription
                        )
                        incomplete = sum(
                            int(r.get('orcamentos_decisao_incompleta') or 0)
                            for r in transcription
                        )
                        inconsistent = sum(
                            int(r.get('orcamentos_liberados') or 0) for r in transcription
                        )

                        with ui.card().classes('w-full p-4 gap-2 shadow-none border border-grey-3'):
                            with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('description', size='20px').classes('text-primary')
                                    ui.label('Registros de consultório').classes(
                                        'text-subtitle2 text-weight-bold'
                                    )
                                ui.label(
                                    f'{identified} orçamento(s) · {format_brl(total)} bruto'
                                ).classes('text-caption text-grey-7')

                            ui.label(
                                f'{classified} transcrição(ões) · {format_brl(classified_value)}'
                            ).classes('text-body2')

                            notes = []
                            if pending:
                                notes.append(f'{pending} pendente(s)')
                            if excluded:
                                notes.append(f'{excluded} excluído(s)')
                            if incomplete:
                                notes.append(f'{incomplete} decisão(ões) incompleta(s)')
                            if notes:
                                ui.label(' · '.join(notes)).classes('text-caption text-grey-7')
                            if inconsistent:
                                ui.label(
                                    f'{inconsistent} registro(s) de CONSULTORIO ainda aparecem '
                                    'como liberados na visão financeira.'
                                ).classes('text-caption text-warning')

                    if doctors:
                        ui.separator().classes('my-1')
                        with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                            with ui.column().classes('gap-0'):
                                ui.label('Detalhamento').classes('text-subtitle1 text-weight-bold')
                                ui.label(
                                    'Consulte e ordene a carteira completa por médico.'
                                ).classes('text-caption text-grey-7')

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
                        ui.table(
                            columns=columns,
                            rows=data,
                            row_key='medico',
                            pagination=10,
                        ).props('flat bordered').classes('w-full')

            except Exception:
                if request == version:
                    status.clear()
                    table_area.clear()
                    with status:
                        ui.label(
                            'Não foi possível carregar a composição por médico. '
                            'Confira a visão e as permissões no Supabase.'
                        ).classes('text-negative')

        month_select.on_value_change(lambda event: load(event.value))
        ui.timer(0.2, lambda: load(month_select.value), once=True)

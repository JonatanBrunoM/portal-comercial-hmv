"""Análise mensal da carteira por médico, com CONSULTORIO separado como transcrição."""
from __future__ import annotations

from decimal import Decimal
import unicodedata

from nicegui import run, ui

from nicegui_app.services.particular_doctor_dashboard import list_doctor_monthly
from nicegui_app.services.particular_doctor_financial_composition import list_doctor_financial_composition
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


def _normalize(value: object) -> str:
    normalized = unicodedata.normalize('NFKD', str(value or ''))
    return ''.join(char for char in normalized if not unicodedata.combining(char)).lower().strip()


def _money(value: object) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def render_doctor_dashboard(access: ParticularAccess, month_select: ui.select, monthly_rows: dict) -> None:
    """Renderiza a leitura gerencial por médico ligada ao seletor mensal principal."""
    with ui.column().classes('w-full gap-3'):
        status = ui.column().classes('w-full gap-2')
        table_area = ui.column().classes('w-full gap-3')
        version = 0
        cache: dict[str, list[dict]] = {}
        composition_cache: dict[str, list[dict]] = {}

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
                if force or month not in composition_cache:
                    composition_cache[month] = await run.io_bound(list_doctor_financial_composition, access, month)
                rows = cache[month]
                composition_rows = composition_cache[month]

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

                    with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                        with ui.column().classes('gap-0'):
                            ui.label('Visão médica').classes('text-subtitle1 text-weight-bold')
                            ui.label('Leitura rápida da carteira vinculada aos médicos.').classes(
                                'text-caption text-grey-7'
                            )
                        ui.button(
                            'Atualizar',
                            icon='refresh',
                            on_click=lambda: load(month_select.value, True),
                        ).props('flat dense no-caps').classes('text-primary')

                    released_pct = (
                        (released_value / gross_value * Decimal('100'))
                        if gross_value > 0 else Decimal(0)
                    )

                    # Faixa executiva única: menos cartões e leitura mais rápida.
                    with ui.card().classes('w-full p-0 gap-0 shadow-sm overflow-hidden'):
                        with ui.row().classes('w-full items-stretch gap-0 flex-wrap'):
                            metrics = (
                                ('Médicos', str(total_doctors), f'{total_budgets} orçamentos', 'medical_services'),
                                ('Valor orçado', format_brl(gross_value), 'Carteira médica identificada', 'payments'),
                                ('Valor liberado', format_brl(released_value), f'{released_pct:.1f}% do valor orçado', 'verified'),
                                ('Em análise', str(pending_budgets), 'orçamentos retidos', 'pending_actions'),
                            )
                            for index, (label, value, note, icon) in enumerate(metrics):
                                classes = 'flex-1 min-w-[190px] p-4 gap-1'
                                if index:
                                    classes += ' border-l border-grey-3'
                                with ui.column().classes(classes):
                                    with ui.row().classes('w-full items-center justify-between gap-2'):
                                        ui.label(label).classes('text-caption text-grey-7')
                                        ui.icon(icon, size='18px').classes(
                                            'text-warning' if label == 'Em análise' and pending_budgets else 'text-primary'
                                        )
                                    ui.label(value).classes('text-h5 text-weight-bold')
                                    ui.label(note).classes('text-caption text-grey-7')

                    if doctors:
                        composition_by_doctor = {
                            _normalize(row.get('medico')): row for row in composition_rows
                            if not _is_transcription(str(row.get('medico') or ''))
                        }

                        analysis_area = ui.column().classes('w-full gap-2')

                        def render_doctor_analysis(mode: str) -> None:
                            analysis_area.clear()

                            if mode == 'ORCADO':
                                ranked = sorted(
                                    doctors,
                                    key=lambda row: _money(row.get('valor_bruto_importado')),
                                    reverse=True,
                                )[:5]
                                value_of = lambda row: _money(row.get('valor_bruto_importado'))
                                series = [{
                                    'name': 'Valor orçado',
                                    'type': 'bar',
                                    'barMaxWidth': 22,
                                    'data': [float(value_of(row) / Decimal('1000')) for row in ranked],
                                }]
                                portfolio_total = gross_value
                            else:
                                ranked = sorted(
                                    [
                                        row for row in composition_rows
                                        if not _is_transcription(str(row.get('medico') or ''))
                                    ],
                                    key=lambda row: _money(row.get('valor_total_liberado')),
                                    reverse=True,
                                )[:5]
                                value_of = lambda row: _money(row.get('valor_total_liberado'))
                                portfolio_total = released_value
                                if mode == 'LIBERADO':
                                    series = [{
                                        'name': 'Valor liberado',
                                        'type': 'bar',
                                        'barMaxWidth': 22,
                                        'data': [float(value_of(row) / Decimal('1000')) for row in ranked],
                                    }]
                                else:
                                    series = [
                                        {
                                            'name': 'Procedimentos',
                                            'type': 'bar',
                                            'stack': 'total',
                                            'barMaxWidth': 22,
                                            'data': [
                                                float(_money(row.get('valor_procedimentos')) / Decimal('1000'))
                                                for row in ranked
                                            ],
                                        },
                                        {
                                            'name': 'Materiais',
                                            'type': 'bar',
                                            'stack': 'total',
                                            'barMaxWidth': 22,
                                            'data': [
                                                float(_money(row.get('valor_materiais')) / Decimal('1000'))
                                                for row in ranked
                                            ],
                                        },
                                    ]

                            top_value = value_of(ranked[0]) if ranked else Decimal(0)
                            top_share = (
                                top_value / portfolio_total * Decimal('100')
                                if portfolio_total > 0 else Decimal(0)
                            )

                            retained_doctor = max(
                                doctors,
                                key=lambda row: _money(row.get('valor_aguardando_analise')),
                                default=None,
                            )
                            retained_value = (
                                _money(retained_doctor.get('valor_aguardando_analise'))
                                if retained_doctor else Decimal(0)
                            )

                            material_rows = [
                                row for row in composition_rows
                                if not _is_transcription(str(row.get('medico') or ''))
                            ]
                            material_doctor = max(
                                material_rows,
                                key=lambda row: _money(row.get('valor_materiais')),
                                default=None,
                            )
                            material_value = (
                                _money(material_doctor.get('valor_materiais'))
                                if material_doctor else Decimal(0)
                            )

                            with analysis_area:
                                with ui.row().classes('w-full gap-3 items-stretch flex-wrap'):
                                    with ui.card().classes('flex-[2] min-w-[560px] p-4 gap-2 shadow-sm'):
                                        with ui.row().classes('w-full items-center justify-between'):
                                            ui.label('Principais carteiras').classes('text-subtitle1 text-weight-bold')
                                            ui.label('Top 5').classes('text-caption text-grey-6')
                                        ui.echart({
                                            'tooltip': {
                                                'trigger': 'axis',
                                                'axisPointer': {'type': 'shadow'},
                                                'valueFormatter': 'function (value) { return "R$ " + Number(value).toLocaleString("pt-BR", {minimumFractionDigits: 1, maximumFractionDigits: 1}) + " mil"; }',
                                            },
                                            'legend': {'show': mode == 'COMPOSICAO', 'top': 0},
                                            'grid': {
                                                'left': 205,
                                                'right': 25,
                                                'bottom': 20,
                                                'top': 35 if mode == 'COMPOSICAO' else 10,
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
                                                    for row in ranked
                                                ],
                                            },
                                            'series': series,
                                        }).classes('w-full h-[245px]')

                                    with ui.card().classes('flex-1 min-w-[280px] p-4 gap-3 shadow-sm'):
                                        ui.label('Destaques').classes('text-subtitle1 text-weight-bold')

                                        if ranked:
                                            with ui.column().classes('gap-0'):
                                                ui.label('Maior carteira nesta leitura').classes('text-caption text-grey-7')
                                                ui.label(str(ranked[0].get('medico') or 'Médico não informado')).classes(
                                                    'text-body2 text-weight-bold'
                                                )
                                                ui.label(
                                                    f'{format_brl(top_value)} · {top_share:.1f}% da carteira'
                                                ).classes('text-caption text-primary')

                                        if retained_doctor and retained_value > 0:
                                            ui.separator()
                                            with ui.column().classes('gap-0'):
                                                ui.label('Maior valor em análise').classes('text-caption text-grey-7')
                                                ui.label(
                                                    str(retained_doctor.get('medico') or 'Médico não informado')
                                                ).classes('text-body2 text-weight-bold')
                                                ui.label(format_brl(retained_value)).classes(
                                                    'text-caption text-warning'
                                                )

                                        if material_doctor and material_value > 0:
                                            ui.separator()
                                            with ui.column().classes('gap-0'):
                                                ui.label('Maior valor em materiais').classes('text-caption text-grey-7')
                                                ui.label(
                                                    str(material_doctor.get('medico') or 'Médico não informado')
                                                ).classes('text-body2 text-weight-bold')
                                                ui.label(format_brl(material_value)).classes(
                                                    'text-caption text-primary'
                                                )

                        with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                            ui.label('Análise da carteira').classes('text-subtitle1 text-weight-bold')
                            chart_mode = ui.toggle(
                                {'ORCADO': 'Orçado', 'LIBERADO': 'Liberado', 'COMPOSICAO': 'Composição'},
                                value='ORCADO',
                            ).props('no-caps dense unelevated')
                        chart_mode.on_value_change(
                            lambda event: render_doctor_analysis(event.value or 'ORCADO')
                        )
                        render_doctor_analysis('ORCADO')

                    if transcription:
                        total = sum((_money(r.get('valor_bruto_importado')) for r in transcription), Decimal(0))
                        identified = sum(int(r.get('orcamentos_importados') or 0) for r in transcription)
                        classified = sum(int(r.get('orcamentos_transcricao') or 0) for r in transcription)
                        classified_value = sum((_money(r.get('valor_transcricao')) for r in transcription), Decimal(0))
                        pending = sum(int(r.get('orcamentos_aguardando_analise') or 0) for r in transcription)
                        excluded = sum(int(r.get('orcamentos_excluidos') or 0) for r in transcription)
                        incomplete = sum(int(r.get('orcamentos_decisao_incompleta') or 0) for r in transcription)
                        inconsistent = sum(int(r.get('orcamentos_liberados') or 0) for r in transcription)

                        with ui.expansion(
                            f'Registros de consultório · {identified} orçamento(s) · {format_brl(total)}',
                            icon='description',
                        ).classes('w-full border border-grey-3 rounded-lg').props('dense'):
                            with ui.column().classes('w-full px-4 pb-4 gap-1'):
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
                        with ui.expansion(
                            f'Consultar todos os médicos · {len(doctors)} identificados',
                            icon='manage_search',
                        ).classes('w-full border border-grey-3 rounded-lg').props('dense'):
                            with ui.column().classes('w-full px-3 pb-4 gap-3'):
                                ui.label(
                                    'Pesquise por médico e refine somente quando precisar do detalhamento.'
                                ).classes('text-caption text-grey-7')

                                filter_row = ui.row().classes('w-full items-end gap-3 flex-wrap')
                                results_area = ui.column().classes('w-full gap-2')

                                with filter_row:
                                    search = ui.input(
                                        'Médico',
                                        placeholder='Digite nome ou parte do nome...',
                                    ).props('outlined dense clearable').classes('flex-1 min-w-[280px]')
                                    situation = ui.select(
                                        {
                                            'TODOS': 'Todos',
                                            'LIBERADO': 'Com valor liberado',
                                            'RETIDO': 'Com valor retido',
                                            'EXCLUIDO': 'Com valor excluído',
                                        },
                                        value='TODOS',
                                        label='Situação',
                                    ).props('outlined dense options-dense').classes('w-[210px]')
                                    minimum = ui.select(
                                        {
                                            '0': 'Qualquer valor',
                                            '10000': 'Acima de R$ 10 mil',
                                            '50000': 'Acima de R$ 50 mil',
                                            '100000': 'Acima de R$ 100 mil',
                                            '250000': 'Acima de R$ 250 mil',
                                        },
                                        value='0',
                                        label='Valor orçado',
                                    ).props('outlined dense options-dense').classes('w-[210px]')
                                    clear_button = ui.button('Limpar', icon='filter_alt_off').props(
                                        'flat dense no-caps'
                                    ).classes('text-grey-7')

                                def render_results() -> None:
                                    results_area.clear()
                                    term = _normalize(search.value)
                                    selected_situation = str(situation.value or 'TODOS')
                                    minimum_value = _money(minimum.value or 0)

                                    filtered = []
                                    for row in doctors:
                                        name = str(row.get('medico') or 'Médico não informado')
                                        if term and term not in _normalize(name):
                                            continue
                                        if (
                                            selected_situation == 'LIBERADO'
                                            and _money(row.get('valor_liberado_duplicidade')) <= 0
                                        ):
                                            continue
                                        if (
                                            selected_situation == 'RETIDO'
                                            and _money(row.get('valor_aguardando_analise')) <= 0
                                        ):
                                            continue
                                        if (
                                            selected_situation == 'EXCLUIDO'
                                            and _money(row.get('valor_excluido_duplicidade')) <= 0
                                        ):
                                            continue
                                        if _money(row.get('valor_bruto_importado')) < minimum_value:
                                            continue
                                        filtered.append(row)

                                    filtered.sort(
                                        key=lambda row: _money(row.get('valor_bruto_importado')),
                                        reverse=True,
                                    )

                                    with results_area:
                                        with ui.row().classes(
                                            'w-full items-center justify-between gap-3 flex-wrap'
                                        ):
                                            ui.label(
                                                f'{len(filtered)} de {len(doctors)} médico(s)'
                                            ).classes('text-caption text-grey-7')
                                            if filtered:
                                                filtered_value = sum(
                                                    (
                                                        _money(r.get('valor_bruto_importado'))
                                                        for r in filtered
                                                    ),
                                                    Decimal(0),
                                                )
                                                ui.label(
                                                    f'{format_brl(filtered_value)} em valor orçado'
                                                ).classes('text-caption text-grey-7')

                                        if not filtered:
                                            ui.label(
                                                'Nenhum médico encontrado com estes filtros.'
                                            ).classes('text-body2 text-grey-7')
                                            return

                                        columns = [
                                            {'name': 'medico', 'label': 'Médico', 'field': 'medico', 'align': 'left', 'sortable': True},
                                            {'name': 'orcamentos', 'label': 'Orçamentos', 'field': 'orcamentos', 'sortable': True},
                                            {'name': 'bruto', 'label': 'Valor orçado', 'field': 'bruto', 'sortable': True},
                                            {'name': 'liberado', 'label': 'Liberado', 'field': 'liberado', 'sortable': True},
                                            {'name': 'retido', 'label': 'Em análise', 'field': 'retido', 'sortable': True},
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
                                            for r in filtered
                                        ]
                                        ui.table(
                                            columns=columns,
                                            rows=data,
                                            row_key='medico',
                                            pagination={'rowsPerPage': 10},
                                        ).props('flat bordered dense').classes('w-full')

                                def clear_filters() -> None:
                                    search.value = ''
                                    situation.value = 'TODOS'
                                    minimum.value = '0'
                                    render_results()

                                search.on_value_change(lambda _: render_results())
                                situation.on_value_change(lambda _: render_results())
                                minimum.on_value_change(lambda _: render_results())
                                clear_button.on_click(clear_filters)
                                render_results()

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

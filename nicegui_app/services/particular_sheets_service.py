from __future__ import annotations

import json
import os
import threading
import time
from collections import Counter
from typing import Any

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from nicegui_app.data.particular_sheets_client import (
    SHEET_NAMES,
    check_sheets_connection,
    read_sheet_range,
)
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied

_API_ROOT = 'https://sheets.googleapis.com/v4/spreadsheets'
_DEFAULT_ID = '1j7KKsA84_vOpIrHWQ0X0_WGXBsAAr6ItPjSJ6b4c8-0'
_BUDGET_COLUMNS = {'GRADE CIRÚRGICA': 'G', 'Negativas': 'E', 'GRADE PONTAL': 'F'}
_CACHE_SECONDS = 300
_cache_lock = threading.Lock()
_cache: dict[str, Any] = {'id': None, 'until': 0.0, 'value': None}


def _require_read(access: ParticularAccess) -> None:
    if not access.can_read:
        raise ParticularAccessDenied('Sem autorização para consultar o Particular.')


def check_particular_sheets(access: ParticularAccess) -> dict:
    _require_read(access)
    return check_sheets_connection()


def read_particular_sheet_rows(
    access: ParticularAccess, sheet_name: str, first_row: int, last_row: int
) -> list[list[str]]:
    _require_read(access)
    return read_sheet_range(sheet_name, first_row, last_row)


def _normalize_budget(value: Any) -> str | None:
    text = str(value).strip()
    if text.endswith('.0') and text[:-2].isdigit():
        text = text[:-2]
    return text if text.isdigit() else None


def _fetch_aggregate(spreadsheet_id: str) -> dict[str, Any]:
    raw = os.environ.get('PARTICULAR_SHEETS_SERVICE_ACCOUNT_JSON', '')
    if not raw:
        raise RuntimeError('Credencial do Sheets não configurada no backend.')
    try:
        info = json.loads(raw)
        if info.get('type') != 'service_account':
            raise ValueError('Credencial inválida')
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        credentials.refresh(Request())
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('Credencial do Sheets inválida.') from exc

    headers = {'Authorization': f'Bearer {credentials.token}'}
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
        def get(path: str, params: list[tuple[str, str]] | dict[str, str]) -> dict:
            for attempt in range(3):
                try:
                    response = client.get(f'{_API_ROOT}/{spreadsheet_id}/{path}',
                                          params=params, headers=headers)
                    if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                        time.sleep(2 ** attempt + 1)
                        continue
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    raise RuntimeError('Não foi possível consultar os indicadores das grades.') from exc
            raise RuntimeError('Limite de consultas ao Google Sheets.')

        metadata = get('', {'fields': 'sheets.properties(title,gridProperties.rowCount)'})
        properties: dict[str, list[dict]] = {name: [] for name in SHEET_NAMES}
        for sheet in metadata.get('sheets', []):
            prop = sheet.get('properties', {})
            title = prop.get('title')
            if isinstance(title, str) and title.strip() in properties:
                properties[title.strip()].append(prop)

        ranges: list[str] = []
        for name in SHEET_NAMES:
            matches = properties[name]
            if len(matches) != 1:
                raise RuntimeError('Aba Particular ausente ou ambígua.')
            prop = matches[0]
            last_row = prop.get('gridProperties', {}).get('rowCount', 0)
            if not isinstance(last_row, int) or last_row < 2:
                raise RuntimeError('Grade Particular sem linhas de dados.')
            escaped_title = prop['title'].replace("'", "''")
            column = _BUDGET_COLUMNS[name]
            ranges.append(f"'{escaped_title}'!{column}2:{column}{last_row}")

        # batchGet: uma solicitação para as três colunas, inclusive linhas ocultas.
        params = [('ranges', item) for item in ranges]
        params.append(('valueRenderOption', 'FORMATTED_VALUE'))
        response = get('values:batchGet', params)

    value_ranges = response.get('valueRanges', [])
    if len(value_ranges) != len(SHEET_NAMES):
        raise RuntimeError('Resposta incompleta das grades Particular.')

    distinct_by_sheet: dict[str, set[str]] = {}
    occurrences_by_sheet: dict[str, dict[str, int]] = {}
    stats: dict[str, dict[str, int]] = {}
    for name, value_range in zip(SHEET_NAMES, value_ranges):
        counts = Counter()
        for row in value_range.get('values', []):
            budget = _normalize_budget(row[0] if row else '')
            if budget is not None:
                counts[budget] += 1
        distinct_by_sheet[name] = set(counts)
        occurrences_by_sheet[name] = dict(counts)
        stats[name] = {
            'linhas_com_orcamento': sum(counts.values()),
            'orcamentos_distintos': len(counts),
            'orcamentos_repetidos_na_aba': sum(qty > 1 for qty in counts.values()),
        }

    appearances = Counter(number for numbers in distinct_by_sheet.values() for number in numbers)
    return {
        'origem': 'copia_de_testes' if spreadsheet_id == _DEFAULT_ID else 'planilha_configurada',
        'abas': stats,
        'orcamentos_distintos_total': len(appearances),
        'orcamentos_em_mais_de_uma_aba': sum(qty > 1 for qty in appearances.values()),
        'atualizado_em_epoch': int(time.time()),
        '_budget_occurrences_by_sheet': occurrences_by_sheet,
    }


def _get_cached_aggregate(access: ParticularAccess) -> dict[str, Any]:
    """Retorna a leitura consolidada preservando o cache e a autorização."""
    _require_read(access)
    spreadsheet_id = os.getenv('PARTICULAR_SHEETS_SPREADSHEET_ID', _DEFAULT_ID).strip()
    if not spreadsheet_id or not all(c.isalnum() or c in '-_' for c in spreadsheet_id):
        raise RuntimeError('ID da planilha Particular inválido.')
    with _cache_lock:
        if (_cache['id'] == spreadsheet_id and _cache['value'] is not None
                and time.monotonic() < _cache['until']):
            return dict(_cache['value'])
        result = _fetch_aggregate(spreadsheet_id)
        _cache.update(id=spreadsheet_id, value=result,
                      until=time.monotonic() + _CACHE_SECONDS)
        return dict(result)


def get_particular_sheets_summary(access: ParticularAccess) -> dict[str, Any]:
    """Indicadores agregados; não expõe o índice operacional de orçamentos."""
    result = _get_cached_aggregate(access)
    return {key: value for key, value in result.items() if not key.startswith('_')}


def cross_particular_budgets_with_sheets(
    access: ParticularAccess,
    budget_numbers: list[int | str],
) -> dict[str, Any]:
    """Cruza orçamentos do HMV2670 com as três grades sem duplicar casos.

    O número do orçamento é a chave operacional. Repetições dentro de uma grade
    são preservadas como ocorrências/histórico, mas o orçamento continua sendo
    contado uma única vez no cruzamento.
    """
    result = _get_cached_aggregate(access)
    occurrences = result.get('_budget_occurrences_by_sheet') or {}
    normalized = sorted({
        budget
        for value in budget_numbers
        if (budget := _normalize_budget(value)) is not None
    }, key=int)

    cases: list[dict[str, Any]] = []
    by_sheet = {name: 0 for name in SHEET_NAMES}
    found_any = 0
    multi_grade = 0
    repeated_history = 0
    context_counts: Counter[str] = Counter()

    for budget in normalized:
        grades = [
            name for name in SHEET_NAMES
            if int((occurrences.get(name) or {}).get(budget, 0)) > 0
        ]
        grade_occurrences = {
            name: int((occurrences.get(name) or {}).get(budget, 0))
            for name in grades
        }
        for name in grades:
            by_sheet[name] += 1

        grade_set = set(grades)
        if not grades:
            context = 'SEM GRADE'
        elif grade_set == {'GRADE CIRÚRGICA'}:
            context = 'SEDE'
        elif grade_set == {'GRADE PONTAL'}:
            context = 'PONTAL'
        elif grade_set == {'Negativas'}:
            context = 'NEGATIVA'
        elif grade_set == {'GRADE CIRÚRGICA', 'Negativas'}:
            context = 'NEGATIVA TOTAL'
        elif grade_set == {'GRADE CIRÚRGICA', 'GRADE PONTAL'}:
            context = 'TRANSFERÊNCIA SEDE ↔ PONTAL'
        elif grade_set == {'GRADE PONTAL', 'Negativas'}:
            context = 'REVISAR PONTAL + NEGATIVAS'
        else:
            context = 'REVISAR FLUXO MÚLTIPLO'

        has_history = any(qty > 1 for qty in grade_occurrences.values())
        if grades:
            found_any += 1
        if len(grades) > 1:
            multi_grade += 1
        if has_history:
            repeated_history += 1
        context_counts[context] += 1

        cases.append({
            'budget_number': budget,
            'grades': grades,
            'grade_occurrences': grade_occurrences,
            'context': context,
            'has_repeated_history': has_history,
        })

    return {
        'total_xml': len(normalized),
        'found_any_grade': found_any,
        'without_grade': len(normalized) - found_any,
        'multiple_grades': multi_grade,
        'repeated_history': repeated_history,
        'by_sheet': by_sheet,
        'context_counts': dict(context_counts),
        'cases': cases,
    }

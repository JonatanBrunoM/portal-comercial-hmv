"""Pesquisa de orçamento nas três grades; somente leitura, uso exclusivo no backend."""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from typing import Any

import httpx

from nicegui_app.data.particular_sheets_client import (
    API_ROOT, DEFAULT_SPREADSHEET_ID, SHEET_NAMES, _authorization_header,
)
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied

_COLUMNS = {'GRADE CIRÚRGICA': 'G', 'Negativas': 'E', 'GRADE PONTAL': 'F'}
_FIELDS = {
    'GRADE CIRÚRGICA': {'data': 1, 'aviso': 2, 'paciente': 3, 'medico': 4,
                        'diferencial': 5, 'valor_caixa': 7, 'contato': 9,
                        'confirmacao': 10, 'observacao': 11},
    'Negativas': {'data': 1, 'aviso': 2, 'paciente': 3, 'tipo': 5,
                 'unique': 6, 'contato': 7, 'confirmacao': 8, 'observacao': 9},
    'GRADE PONTAL': {'data': 1, 'aviso': 2, 'paciente': 3, 'medico': 4,
                     'valor': 6, 'unique': 7, 'contato': 8,
                     'confirmacao_contato': 9, 'evolucao': 10,
                     'confirmacao_paciente': 11},
}
_TTL = 300
_MAX_MATCHES = 40
_lock = threading.Lock()
_index_cache: dict[str, Any] = {'id': None, 'until': 0.0, 'index': None, 'titles': None}


def _number(value: Any) -> str | None:
    text = str(value).strip()
    if text.endswith('.0') and text[:-2].isdigit():
        text = text[:-2]
    return text if text.isdigit() else None


def _spreadsheet_id() -> str:
    value = os.getenv('PARTICULAR_SHEETS_SPREADSHEET_ID', DEFAULT_SPREADSHEET_ID).strip()
    if not value or not all(c.isalnum() or c in '-_' for c in value):
        raise RuntimeError('ID da planilha Particular inválido.')
    return value


def _get(client: httpx.Client, spreadsheet_id: str, path: str,
         params: list[tuple[str, str]] | dict[str, str]) -> dict[str, Any]:
    for attempt in range(3):
        try:
            response = client.get(f'{API_ROOT}/{spreadsheet_id}/{path}',
                                  params=params, headers=_authorization_header())
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt + 1)
                continue
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError('Resposta inválida')
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError('Não foi possível consultar as grades Particular.') from exc
    raise RuntimeError('Limite de consultas às grades Particular.')


def _build_index(client: httpx.Client, spreadsheet_id: str) -> tuple[dict[str, list[tuple[str, int]]], dict[str, str]]:
    metadata = _get(client, spreadsheet_id, '',
                    {'fields': 'sheets.properties(title,gridProperties.rowCount)'})
    properties: dict[str, list[dict[str, Any]]] = {name: [] for name in SHEET_NAMES}
    for sheet in metadata.get('sheets', []):
        prop = sheet.get('properties', {})
        title = prop.get('title')
        if isinstance(title, str) and title.strip() in properties:
            properties[title.strip()].append(prop)

    ranges: list[str] = []
    titles: dict[str, str] = {}
    for name in SHEET_NAMES:
        if len(properties[name]) != 1:
            raise RuntimeError('Aba Particular ausente ou ambígua.')
        prop = properties[name][0]
        last_row = prop.get('gridProperties', {}).get('rowCount')
        if not isinstance(last_row, int) or last_row < 2:
            raise RuntimeError('Grade Particular sem linhas de dados.')
        title = prop['title']
        titles[name] = title
        ranges.append(f"'{title.replace(chr(39), chr(39) * 2)}'!{_COLUMNS[name]}2:{_COLUMNS[name]}{last_row}")

    params = [('ranges', item) for item in ranges]
    params.append(('valueRenderOption', 'FORMATTED_VALUE'))
    payload = _get(client, spreadsheet_id, 'values:batchGet', params)
    value_ranges = payload.get('valueRanges', [])
    if len(value_ranges) != len(SHEET_NAMES):
        raise RuntimeError('Resposta incompleta das grades Particular.')
    index: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for name, value_range in zip(SHEET_NAMES, value_ranges):
        for row_number, row in enumerate(value_range.get('values', []), start=2):
            number = _number(row[0] if row else '')
            if number is not None:
                index[number].append((name, row_number))
    return dict(index), titles


def get_particular_sheet_budget_matches(access: ParticularAccess, budget_number: str) -> dict[str, Any]:
    """Busca exata; não interpreta avisos/contatos como realização no MV.

    Deve ser chamada via run.io_bound na interface. Não registrar resultados em logs.
    """
    if not access.can_read:
        raise ParticularAccessDenied('Sem autorização para consultar o Particular.')
    number = _number(budget_number)
    if number is None or len(number) > 20:
        raise ValueError('Informe um número de orçamento válido (somente dígitos).')
    spreadsheet_id = _spreadsheet_id()
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
        with _lock:
            if (_index_cache['id'] != spreadsheet_id or
                    _index_cache['index'] is None or
                    time.monotonic() >= _index_cache['until']):
                index, titles = _build_index(client, spreadsheet_id)
                _index_cache.update(id=spreadsheet_id, index=index, titles=titles,
                                    until=time.monotonic() + _TTL)
            locations = list(_index_cache['index'].get(number, []))
            titles = dict(_index_cache['titles'])

        selected = locations[:_MAX_MATCHES]
        if not selected:
            return {'numero': number, 'total': 0, 'limitado': False, 'ocorrencias': []}
        ranges = [f"'{titles[name].replace(chr(39), chr(39) * 2)}'!A{row}:L{row}"
                  for name, row in selected]
        params = [('ranges', item) for item in ranges]
        params.append(('valueRenderOption', 'FORMATTED_VALUE'))
        payload = _get(client, spreadsheet_id, 'values:batchGet', params)
        values = payload.get('valueRanges', [])
        if len(values) != len(selected):
            raise RuntimeError('Resposta incompleta dos registros do orçamento.')
        matches = []
        for (name, row_number), value_range in zip(selected, values):
            rows = value_range.get('values', [])
            cells = rows[0] if rows else []
            budget_column = ord(_COLUMNS[name]) - ord('A')
            if _number(cells[budget_column] if len(cells) > budget_column else '') != number:
                raise RuntimeError('A grade foi atualizada durante a pesquisa. Pesquise novamente.')
            fields = {key: str(cells[position]).strip() if position < len(cells) else ''
                      for key, position in _FIELDS[name].items()}
            matches.append({'aba': name, 'linha': row_number, 'campos': fields})
        return {'numero': number, 'total': len(locations),
                'limitado': len(locations) > _MAX_MATCHES, 'ocorrencias': matches}

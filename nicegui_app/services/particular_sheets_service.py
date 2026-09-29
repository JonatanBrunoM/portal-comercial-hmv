from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import unicodedata
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from nicegui_app.data.particular_sheets_client import (
    SHEET_NAMES,
    check_sheets_connection,
    read_sheet_all,
    read_sheet_range,
)
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied

_API_ROOT = 'https://sheets.googleapis.com/v4/spreadsheets'
_DEFAULT_ID = '1j7KKsA84_vOpIrHWQ0X0_WGXBsAAr6ItPjSJ6b4c8-0'
_BUDGET_COLUMNS = {'GRADE CIRÚRGICA': 'G', 'Negativas': 'E', 'GRADE PONTAL': 'F'}

_SHEET_FIELD_ALIASES = {
    'GRADE CIRÚRGICA': {
        'procedure_date': ('DATA',),
        'notice_number': ('N AVISO', 'N° AVISO', 'Nº AVISO'),
        'patient_name': ('NOME DO PACIENTE',),
        'doctor_name': ('MEDICO', 'MÉDICO'),
        'differential': ('DIFERENCIAL',),
        'budget_number': ('ORCAMENTO', 'ORÇAMENTO'),
        'operational_value': ('VALOR A VISTA', 'VALOR À VISTA'),
        'contact_status': ('CONTATO COM O PACIENTE',),
        'patient_confirmation': ('CONFIRMACAO DO PACIENTE', 'CONFIRMAÇÃO DO PACIENTE'),
        'notes_original': ('OBSERVACAO', 'OBSERVAÇÃO'),
    },
    'Negativas': {
        'procedure_date': ('DATA DO PROCEDIMENTO',),
        'notice_number': ('N AVISO', 'N° AVISO', 'Nº AVISO'),
        'patient_name': ('NOME DO PACIENTE',),
        'budget_number': ('ORCAMENTO', 'ORÇAMENTO'),
        'negative_type_value': ('TIPO/VALOR',),
        'contact_status': ('CONTATO PACIENTE',),
        'patient_confirmation': ('CONFIRMACAO CONTATO PACIENTE',),
        'notes_original': ('OBSERVACAO', 'OBSERVAÇÃO'),
    },
    'GRADE PONTAL': {
        'procedure_date': ('DATA DO PROCEDIMENTO',),
        'notice_number': ('N AVISO', 'N° AVISO', 'Nº AVISO'),
        'patient_name': ('NOME DO PACIENTE',),
        'doctor_name': ('NOME DO MEDICO', 'NOME DO MÉDICO'),
        'budget_number': ('ORCAMENTO', 'ORÇAMENTO'),
        'operational_value': ('VALOR',),
        'contact_status': ('CONTATO PACIENTE',),
        'patient_confirmation': ('CONFIRMACAO CONTATO PACIENTE', 'CONFIRMAÇÃO CONTATO PACIENTE'),
        'evolution_status': ('REGISTRO EM EVOLUCAO', 'REGISTRO EM EVOLUÇÃO'),
        'notes_original': ('CONFIRMACAO PACIENTE', 'CONFIRMAÇÃO PACIENTE'),
    },
}
_REQUIRED_SHEET_FIELDS = {
    'GRADE CIRÚRGICA': {'procedure_date', 'notice_number', 'budget_number'},
    'Negativas': {'procedure_date', 'notice_number', 'budget_number'},
    'GRADE PONTAL': {'procedure_date', 'notice_number', 'budget_number'},
}
_LOCATION_BY_SHEET = {'GRADE CIRÚRGICA': 'SEDE', 'GRADE PONTAL': 'PONTAL', 'Negativas': None}
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


def _budget_reference(value: Any) -> tuple[str | None, str, str | None]:
    raw = _normalize_text(value)
    budget = _normalize_budget(value)
    if budget is not None:
        return budget, 'IDENTIFIED', raw

    normalized = _normalize_header(raw)
    if normalized == 'FAZER':
        return None, 'TO_DO', raw

    return None, 'UNIDENTIFIED', raw


def _normalize_header(value: Any) -> str:
    text = unicodedata.normalize('NFKD', str(value or '').strip().upper())
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[^A-Z0-9/]+', ' ', text.replace('\n', ' '))
    return re.sub(r'\s+', ' ', text).strip()


def _normalize_text(value: Any) -> str | None:
    text = str(value or '').strip()
    return text or None


def _normalize_integer_text(value: Any) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    if text.endswith('.0'):
        text = text[:-2]
    digits = re.sub(r'\D', '', text)
    return digits or None


def _normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d'):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _normalize_money(value: Any) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    cleaned = re.sub(r'[^\d,.\-]', '', text)
    if ',' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    try:
        return str(Decimal(cleaned).quantize(Decimal('0.01')))
    except (InvalidOperation, ValueError):
        return None


def _resolve_sheet_columns(sheet_name: str, header_row: list[Any]) -> dict[str, int]:
    aliases = _SHEET_FIELD_ALIASES[sheet_name]
    normalized_headers = {
        _normalize_header(value): index
        for index, value in enumerate(header_row)
        if _normalize_header(value)
    }
    resolved: dict[str, int] = {}
    for field, field_aliases in aliases.items():
        for alias in field_aliases:
            if _normalize_header(alias) in normalized_headers:
                resolved[field] = normalized_headers[_normalize_header(alias)]
                break
    missing = _REQUIRED_SHEET_FIELDS[sheet_name] - resolved.keys()
    if missing:
        raise RuntimeError(
            f'Estrutura inesperada em {sheet_name}. '
            f'Campos obrigatórios ausentes: {", ".join(sorted(missing))}.'
        )
    return resolved


def _cell(row: list[Any], index: int | None) -> Any:
    return None if index is None or index >= len(row) else row[index]


def _occurrence_source_row_key(payload: dict[str, Any]) -> str:
    """Identidade semântica estável; nunca depende do número físico da linha."""
    identity = {
        'source_sheet': payload.get('source_sheet'),
        'budget_reference_status': payload.get('budget_reference_status'),
        'budget_number': payload.get('budget_number'),
        'budget_reference_raw': payload.get('budget_reference_raw'),
        'notice_number': payload.get('notice_number'),
        'procedure_date': payload.get('procedure_date'),
        'patient_name': _normalize_header(payload.get('patient_name')) or None,
    }
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    ).hexdigest()


def _build_occurrence_payload(
    *, sheet_name: str, row_number: int, row: list[Any], columns: dict[str, int]
) -> dict[str, Any] | None:
    budget_number, budget_reference_status, budget_reference_raw = _budget_reference(
        _cell(row, columns.get('budget_number'))
    )
    if budget_reference_status == 'UNIDENTIFIED':
        return None
    payload = {
        'source_sheet': sheet_name,
        'source_row_number': row_number,
        'budget_number': int(budget_number) if budget_number is not None else None,
        'budget_reference_status': budget_reference_status,
        'budget_reference_raw': budget_reference_raw,
        'notice_number': _normalize_integer_text(_cell(row, columns.get('notice_number'))),
        'procedure_date': _normalize_date(_cell(row, columns.get('procedure_date'))),
        'location': _LOCATION_BY_SHEET[sheet_name],
        'operational_value': _normalize_money(_cell(row, columns.get('operational_value'))),
        'patient_name': _normalize_text(_cell(row, columns.get('patient_name'))),
        'doctor_name': _normalize_text(_cell(row, columns.get('doctor_name'))),
        'differential': _normalize_text(_cell(row, columns.get('differential'))),
        'negative_type_value': _normalize_text(_cell(row, columns.get('negative_type_value'))),
        'contact_status': _normalize_text(_cell(row, columns.get('contact_status'))),
        'patient_confirmation': _normalize_text(_cell(row, columns.get('patient_confirmation'))),
        'evolution_status': _normalize_text(_cell(row, columns.get('evolution_status'))),
        'notes_original': _normalize_text(_cell(row, columns.get('notes_original'))),
    }
    payload['source_row_key'] = _occurrence_source_row_key(payload)
    hash_payload = {key: value for key, value in payload.items() if key not in {'source_row_number', 'source_row_key'}}
    payload['source_row_hash'] = hashlib.sha256(
        json.dumps(hash_payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    ).hexdigest()
    return payload



def get_particular_occurrences_preview(access: ParticularAccess) -> dict[str, Any]:
    """Lê e normaliza as três grades sem persistir dados no Supabase."""
    _require_read(access)

    occurrences: list[dict[str, Any]] = []
    sheet_stats: dict[str, dict[str, Any]] = {}

    for sheet_name in SHEET_NAMES:
        all_rows = read_sheet_all(sheet_name)
        if not all_rows:
            raise RuntimeError(f'Grade {sheet_name} sem cabeçalho.')

        columns = _resolve_sheet_columns(sheet_name, all_rows[0])
        valid = 0
        invalid_date = 0
        to_do_rows = 0
        unidentified_budget_rows = 0

        for row_number, row in enumerate(all_rows[1:], start=2):
            raw_budget = _cell(row, columns.get('budget_number'))
            _, budget_reference_status, _ = _budget_reference(raw_budget)

            if budget_reference_status == 'UNIDENTIFIED':
                if any(str(cell or '').strip() for cell in row):
                    unidentified_budget_rows += 1
                continue

            if budget_reference_status == 'TO_DO':
                to_do_rows += 1

            occurrence = _build_occurrence_payload(
                sheet_name=sheet_name,
                row_number=row_number,
                row=row,
                columns=columns,
            )
            if occurrence is not None:
                if occurrence['procedure_date'] is None:
                    invalid_date += 1
                occurrences.append(occurrence)
                valid += 1

        sheet_stats[sheet_name] = {
            'valid_occurrences': valid,
            'invalid_or_missing_date': invalid_date,
            'nonempty_rows_without_budget': unidentified_budget_rows,
            'to_do_rows': to_do_rows,
            'unidentified_budget_rows': unidentified_budget_rows,
            'requests_used': 1,
            'resolved_columns': sorted(columns),
        }

    repeated = Counter(
        (row['source_sheet'], row['budget_number'])
        for row in occurrences
        if row.get('budget_number') is not None
    )
    repeated_budgets = sum(count > 1 for count in repeated.values())

    identity_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in occurrences:
        identity_groups.setdefault(
            (str(row.get('source_sheet') or ''), str(row.get('source_row_key') or '')),
            [],
        ).append(row)
    identity_collisions = [
        rows for rows in identity_groups.values()
        if len(rows) > 1
    ]

    return {
        'persisted': False,
        'total_occurrences': len(occurrences),
        'sheet_stats': sheet_stats,
        'repeated_budget_sheet_pairs': repeated_budgets,
        'to_do_occurrences': sum(
            row.get('budget_reference_status') == 'TO_DO'
            for row in occurrences
        ),
        'identity_collision_groups': len(identity_collisions),
        'identity_collision_occurrences': sum(len(rows) for rows in identity_collisions),
        'identity_collision_sample': [
            {
                'source_sheet': row.get('source_sheet'),
                'source_row_number': row.get('source_row_number'),
                'budget_number': row.get('budget_number'),
                'budget_reference_status': row.get('budget_reference_status'),
                'budget_reference_raw': row.get('budget_reference_raw'),
                'notice_number': row.get('notice_number'),
                'procedure_date': row.get('procedure_date'),
                'patient_name': row.get('patient_name'),
                'operational_value': row.get('operational_value'),
                'source_row_hash': row.get('source_row_hash'),
            }
            for rows in identity_collisions[:20]
            for row in rows[:10]
        ],
        'occurrences': occurrences,
    }



def commit_particular_occurrences_preview(
    access: ParticularAccess,
    preview: dict[str, Any],
) -> dict[str, Any]:
    """Persiste exatamente a fotografia já analisada das três grades."""
    if not access.can_write:
        raise ParticularAccessDenied(
            'Seu perfil não possui permissão para sincronizar as grades do Particular.'
        )
    if not isinstance(preview, dict) or preview.get('persisted') is not False:
        raise ValueError('Execute um novo diagnóstico das grades antes da sincronização.')

    occurrences = preview.get('occurrences')
    if not isinstance(occurrences, list) or not occurrences:
        raise ValueError('O diagnóstico não contém ocorrências para sincronização.')
    if len(occurrences) != int(preview.get('total_occurrences') or 0):
        raise ValueError('A fotografia analisada está inconsistente; execute o diagnóstico novamente.')

    scoped_keys = [
        (str(row.get('source_sheet') or ''), str(row.get('source_row_key') or ''))
        for row in occurrences
    ]
    if any(not sheet or not key for sheet, key in scoped_keys):
        raise ValueError('Há ocorrência sem identidade operacional; sincronização bloqueada.')
    if len(scoped_keys) != len(set(scoped_keys)):
        raise ValueError(
            'Foram encontradas identidades operacionais duplicadas. '
            'Nenhum dado foi gravado; revise o diagnóstico.'
        )

    spreadsheet_id = os.getenv('PARTICULAR_SHEETS_SPREADSHEET_ID', _DEFAULT_ID).strip()
    if not spreadsheet_id:
        raise RuntimeError('ID da planilha Particular não configurado.')

    from nicegui_app.repositories.particular_repository import commit_sheet_sync

    result = commit_sheet_sync(
        spreadsheet_id=spreadsheet_id,
        occurrences=occurrences,
        sync_mode='MANUAL',
        triggered_by=access.profile_id,
        metadata={
            'portal_sync_version': 'PARTICULAR_GRADES_V1',
            'source': 'GRADE_CIRURGICA_NEGATIVAS_GRADE_PONTAL',
            'total_occurrences': len(occurrences),
            'to_do_occurrences': int(preview.get('to_do_occurrences') or 0),
            'repeated_budget_sheet_pairs': int(
                preview.get('repeated_budget_sheet_pairs') or 0
            ),
            'sheet_stats': preview.get('sheet_stats') or {},
        },
    )
    return result

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

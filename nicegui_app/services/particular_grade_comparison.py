"""Sinalizações informativas entre ocorrências de um mesmo orçamento nas grades.

Não identifica pacientes, não confirma negativa/transferência e não altera dados.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any


def _normalized(value: object) -> str:
    text = unicodedata.normalize('NFKD', str(value or '').strip())
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).casefold().split())


def _date(value: object) -> str:
    text = str(value or '').strip()
    for pattern in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            pass
    return _normalized(text)


def compare_grade_occurrences(data: dict[str, Any]) -> list[str]:
    """Retorna mensagens sem dados pessoais; apenas compara registros já consultados.

    Nenhuma conclusão sobre identidade, procedimento, negativa ou realização no MV.
    """
    matches = data.get('ocorrencias', [])
    if data.get('limitado'):
        return ['A consulta está limitada às primeiras 40 ocorrências; a conferência não abrange todos os registros.']
    if len(matches) < 2:
        return ['Não há duas ocorrências deste orçamento para comparação entre grades.']

    notices: list[str] = []
    names = {_normalized(item.get('campos', {}).get('paciente')) for item in matches}
    names.discard('')
    if len(names) > 1:
        notices.append('Há nomes de pacientes diferentes nos registros deste orçamento. Confira as linhas antes de associá-los.')
    elif not names:
        notices.append('Nome do paciente não informado nas ocorrências consultadas.')
    elif any(not _normalized(item.get('campos', {}).get('paciente')) for item in matches):
        notices.append('Há ocorrência sem nome do paciente; a correspondência precisa de conferência.')

    dates = {_date(item.get('campos', {}).get('data')) for item in matches}
    dates.discard('')
    if len(dates) > 1:
        notices.append('As datas previstas do procedimento diferem entre as ocorrências. Confira possível remarcação ou erro de registro.')
    if any(not _date(item.get('campos', {}).get('data')) for item in matches):
        notices.append('Há ocorrência sem data prevista do procedimento.')

    avisos = {_normalized(item.get('campos', {}).get('aviso')) for item in matches}
    avisos.discard('')
    if len(avisos) > 1:
        notices.append('Os números de aviso diferem entre as ocorrências. Verifique possível erro de digitação ou registros distintos.')
    if any(not _normalized(item.get('campos', {}).get('aviso')) for item in matches):
        notices.append('Há ocorrência sem número de aviso.')

    tabs = {item.get('aba') for item in matches}
    has_sede = 'GRADE CIRÚRGICA' in tabs
    if has_sede and 'Negativas' in tabs:
        marked = any(re.search(r'(?<![\w])2\s*G(?![\w])',
                               _normalized(item.get('campos', {}).get('observacao')).upper())
                     for item in matches if item.get('aba') in ('GRADE CIRÚRGICA', 'Negativas'))
        if marked:
            notices.append('Sede + Negativas: indicação “2G” encontrada nas Observações. Confira o vínculo do procedimento e da negativa; a anotação não confirma a situação no MV.')
        else:
            notices.append('Sede + Negativas: não foi localizada a indicação “2G” nas Observações consultadas. Confira se os registros correspondem ao mesmo procedimento.')
    if has_sede and 'GRADE PONTAL' in tabs:
        notices.append('Sede + Pontal: confira se houve transferência entre unidades. A presença nas duas grades não confirma transferência ou dois procedimentos.')
    if 'Negativas' in tabs and 'GRADE PONTAL' in tabs:
        notices.append('Negativas + Pontal: combinação fora do fluxo habitual informado. Confira os registros; não foi estabelecido vínculo automático entre essas grades.')
    if not notices:
        notices.append('Não foram identificadas diferenças nos campos comparáveis preenchidos. Isso não confirma identidade, procedimento ou realização no MV.')
    return notices

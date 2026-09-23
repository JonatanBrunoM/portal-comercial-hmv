"""Leitura server-side das três abas autorizadas do Google Sheets Particular.

Exigir ParticularAccess.can_read no serviço antes de chamar funções de leitura.
Não registrar conteúdo de células, tokens ou respostas da API em logs.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any
from urllib.parse import quote

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

SCOPES = ("https://www.googleapis.com/auth/spreadsheets.readonly",)
SHEET_NAMES = ("GRADE CIRÚRGICA", "Negativas", "GRADE PONTAL")
DEFAULT_SPREADSHEET_ID = "1j7KKsA84_vOpIrHWQ0X0_WGXBsAAr6ItPjSJ6b4c8-0"
API_ROOT = "https://sheets.googleapis.com/v4/spreadsheets"


def _spreadsheet_id() -> str:
    value = os.getenv("PARTICULAR_SHEETS_SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID).strip()
    if not value or not all(c.isalnum() or c in "-_" for c in value):
        raise RuntimeError("ID da planilha Particular inválido.")
    return value


@lru_cache(maxsize=1)
def _credentials():
    raw = os.getenv("PARTICULAR_SHEETS_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("Credencial de leitura do Sheets não configurada no backend.")
    try:
        info = json.loads(raw)
        if info.get("type") != "service_account":
            raise ValueError("Tipo de credencial inválido")
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    except (ValueError, TypeError, KeyError) as exc:
        raise RuntimeError("Configuração da credencial do Sheets inválida.") from exc


def _authorization_header() -> dict[str, str]:
    credentials = _credentials()
    if not credentials.valid or not credentials.token:
        credentials.refresh(Request())
    return {"Authorization": f"Bearer {credentials.token}"}


def _get(path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=httpx.Timeout(25.0, connect=5.0)) as client:
            response = client.get(
                f"{API_ROOT}/{_spreadsheet_id()}/{path}",
                params=params,
                headers=_authorization_header(),
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("Não foi possível consultar a planilha Particular.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Resposta inválida do Google Sheets.")
    return payload


@lru_cache(maxsize=1)
def _real_sheet_names(spreadsheet_id: str) -> dict[str, str]:
    """Resolve os nomes reais (com espaços) sem alterar a planilha."""
    payload = _get("", {"fields": "sheets.properties.title"})
    matches: dict[str, list[str]] = {name: [] for name in SHEET_NAMES}
    for sheet in payload.get("sheets", []):
        title = sheet.get("properties", {}).get("title")
        if isinstance(title, str) and title.strip() in matches:
            matches[title.strip()].append(title)
    if any(len(matches[name]) != 1 for name in SHEET_NAMES):
        raise RuntimeError("Abas autorizadas ausentes ou com nomes ambíguos na planilha.")
    return {name: matches[name][0] for name in SHEET_NAMES}


def check_sheets_connection() -> dict[str, Any]:
    """Retorna apenas disponibilidade das abas, sem ler valores de células."""
    payload = _get("", {"fields": "sheets.properties.title"})
    available = [sheet.get("properties", {}).get("title", "")
                 for sheet in payload.get("sheets", [])]
    counts = {name: sum(isinstance(title, str) and title.strip() == name
                        for title in available) for name in SHEET_NAMES}
    return {
        "configured": True,
        "tabs": [{"name": name, "available": counts[name] == 1} for name in SHEET_NAMES],
        "all_tabs_available": all(counts[name] == 1 for name in SHEET_NAMES),
    }


def read_sheet_range(sheet_name: str, first_row: int, last_row: int) -> list[list[str]]:
    """Lê até 500 linhas, inclusive ocultas; chamar apenas no backend autorizado."""
    if sheet_name not in SHEET_NAMES:
        raise ValueError("Aba não autorizada para o Particular.")
    if not (1 <= first_row <= last_row <= first_row + 499):
        raise ValueError("Intervalo de linhas inválido (máximo de 500).")
    real_name = _real_sheet_names(_spreadsheet_id())[sheet_name]
    escaped_name = real_name.replace("'", "''")
    a1_range = f"'{escaped_name}'!A{first_row}:AZ{last_row}"
    payload = _get(
        f"values/{quote(a1_range, safe='')}",
        {"valueRenderOption": "FORMATTED_VALUE"},
    )
    rows = payload.get("values", [])
    if not isinstance(rows, list):
        raise RuntimeError("Resposta inválida do Google Sheets.")
    return rows

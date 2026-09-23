from __future__ import annotations

from nicegui_app.data.particular_sheets_client import (
    check_sheets_connection,
    read_sheet_range,
)
from nicegui_app.services.particular_service import ParticularAccess, ParticularAccessDenied


def check_particular_sheets(access: ParticularAccess) -> dict:
    if not access.can_read:
        raise ParticularAccessDenied("Sem autorização para consultar o Particular.")
    return check_sheets_connection()


def read_particular_sheet_rows(
    access: ParticularAccess, sheet_name: str, first_row: int, last_row: int
) -> list[list[str]]:
    if not access.can_read:
        raise ParticularAccessDenied("Sem autorização para consultar o Particular.")
    return read_sheet_range(sheet_name, first_row, last_row)

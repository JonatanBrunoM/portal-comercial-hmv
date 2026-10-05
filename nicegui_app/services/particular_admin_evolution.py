from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from datetime import datetime
from typing import Any


EXPECTED_HEADER = (
    "paciente", "atendimento", "dt_atendimento", "cd_evol_admin",
    "dt_registro_evol_admin", "nm_usuario", "tipo_evolucao", "descricao",
)


def _header(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _name(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").strip().upper())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", value).split())


def _date(value: str) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:10], fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Data de atendimento invalida: {raw}.")


def _datetime(value: str) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    # O export real pode trazer apenas a data (ex.: 31/08/26), sem horario.
    # Nesse caso preservamos meia-noite como horario tecnico, sem inventar
    # uma hora operacional que a fonte nao informou.
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%d/%m/%y %H:%M",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt).isoformat(timespec="seconds")
        except ValueError:
            pass
    raise ValueError(f"Data/hora de evolucao invalida: {raw}.")


def _number(value: str, label: str, row_number: int, required: bool = False) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        if required:
            raise ValueError(f"{label} ausente na linha {row_number}.")
        return None
    raw = raw[:-2] if raw.endswith(".0") else raw
    if not raw.isdecimal():
        raise ValueError(f"{label} invalido na linha {row_number}: {raw}.")
    return raw


def inspect_admin_evolution(content: bytes, filename: str) -> dict[str, Any]:
    """Pre-valida o TSV de evolucao administrativa sem interpretar o desfecho."""
    digest = hashlib.sha256(content).hexdigest()
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text), delimiter="\t", quotechar='"')
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ValueError("O relatorio esta vazio.") from exc

    normalized_header = tuple(_header(v) for v in header)
    header_aliases = {
        "paciente": {"paciente", "nm_paciente", "nome_paciente"},
        "atendimento": {"atendimento", "nr_atendimento", "cd_atendimento"},
        "dt_atendimento": {"dt_atendimento", "data_atendimento"},
        "cd_evol_admin": {"cd_evol_admin", "codigo_evol_admin", "codigo_evolucao_admin"},
        "dt_registro_evol_admin": {"dt_registro_evol_admin", "data_registro_evol_admin", "dt_evol_admin"},
        "nm_usuario": {"nm_usuario", "usuario", "nome_usuario"},
        "tipo_evolucao": {"tipo_evolucao", "tipo_evol", "ds_tipo_evolucao"},
        "descricao": {"descricao", "ds_evolucao", "descricao_evolucao", "evolucao"},
    }
    if len(normalized_header) < 8:
        raise ValueError(
            f"Estrutura do Relatorio Evolucao AGO incompleta: {len(normalized_header)} coluna(s)."
        )
    for position, expected in enumerate(EXPECTED_HEADER):
        if normalized_header[position] not in header_aliases[expected]:
            raise ValueError(
                "Estrutura do Relatorio Evolucao AGO nao reconhecida. "
                f"Coluna {position + 1}: recebido '{header[position]}'."
            )

    records: list[dict[str, Any]] = []
    attendances: set[str] = set()
    months: set[str] = set()
    embedded_tab_rows = 0

    for row_number, raw in enumerate(reader, start=2):
        if not raw or not any(str(v).strip() for v in raw):
            continue
        if len(raw) < 8:
            raise ValueError(f"Linha {row_number} incompleta: foram encontradas {len(raw)} colunas.")

        first = [str(v or "").strip() for v in raw[:7]]
        description = "\t".join(str(v or "") for v in raw[7:]).strip()
        patient, attendance_raw, attendance_date_raw, code_raw, recorded_raw, user, evolution_type = first
        attendance = _number(attendance_raw, "Atendimento", row_number, True)
        code = _number(code_raw, "Codigo da evolucao", row_number)
        attendance_date = _date(attendance_date_raw)
        recorded_at = _datetime(recorded_raw)

        attendances.add(attendance)
        if attendance_date:
            months.add(attendance_date[:7])
        if len(raw) > 8:
            embedded_tab_rows += 1

        hash_fields = first + [description]
        row_hash = hashlib.sha256("\x1f".join(hash_fields).encode("utf-8")).hexdigest()

        records.append({
            "source_row_number": row_number,
            "patient_name_raw": patient or None,
            "attendance_number_raw": attendance_raw or None,
            "attendance_date_raw": attendance_date_raw or None,
            "admin_evolution_code_raw": code_raw or None,
            "evolution_recorded_at_raw": recorded_raw or None,
            "user_name_raw": user or None,
            "evolution_type_raw": evolution_type or None,
            "description_raw": description or None,
            "patient_name_normalized": _name(patient) or None,
            "attendance_number": attendance,
            "attendance_date": attendance_date,
            "admin_evolution_code": code,
            "evolution_recorded_at": recorded_at,
            "user_name": user or None,
            "evolution_type": evolution_type or None,
            "source_row_hash": row_hash,
            "raw_payload": {
                "source_columns": len(raw),
                "description_had_embedded_tabs": len(raw) > 8,
            },
        })

    if not records:
        raise ValueError("Nenhuma evolucao administrativa encontrada.")

    return {
        "source_filename": str(filename or "").strip() or "Relatorio Evolucao AGO.csv",
        "file_sha256": digest,
        "records": records,
        "records_total": len(records),
        "distinct_attendances": len(attendances),
        "reference_month": next(iter(months)) + "-01" if len(months) == 1 else None,
        "months_found": sorted(months),
        "embedded_tab_rows": embedded_tab_rows,
        "valid_for_import": True,
    }

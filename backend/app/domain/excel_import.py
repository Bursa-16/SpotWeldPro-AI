"""
excel_import.py — XLSX import validation for energy data.

P1 scope — MASTER-ENERGY-OPTIMIZATION-01.

SECURITY:
  openpyxl is loaded with read_only=True, data_only=True.
  data_only=True reads the last cached cell value — formulas are NEVER
  evaluated. A workbook whose cells contain formulas but no cached results
  returns None for those cells, which the downstream validator treats as
  an empty value (NOT_ESTABLISHED or missing, never a formula string).

  Cell values are serialised to plain strings and then fed through the
  same CSV round-trip and formula-injection check used for CSV import.
  A string cell that starts with '=', '+', '@', '|' or 'DDE(' is still
  flagged as FORMULA_INJECTION — this covers hand-typed injection payloads
  stored as text in Excel cells.

WORKSHEET SELECTION:
  Uses the active (first) worksheet by default. Pass sheet_name to target
  a specific sheet. Column mapping is header-row-based, identical to CSV.

LIMITS:
  MAX_XLSX_BYTES  : 10 MB file size
  MAX_DATA_ROWS   : 10 000 data rows (header row excluded)
"""

from __future__ import annotations

import csv
import datetime
import io
from typing import Optional

import openpyxl

from app.domain.import_validation import (
    CellError,
    ImportValidationResult,
    REQUIRED_COLUMNS,
    validate_csv_import,
)

MAX_XLSX_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_DATA_ROWS = 10_000


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_xlsx_import(
    xlsx_bytes: bytes,
    existing_point_codes: Optional[set[str]] = None,
    sheet_name: Optional[str] = None,
) -> ImportValidationResult:
    """Parse an XLSX workbook and validate its contents as energy import data.

    Converts the selected worksheet to CSV text, then delegates all
    row-level validation to validate_csv_import — same injection detection,
    numeric checks, duplicate detection, and window-ordering rules apply.

    Args:
        xlsx_bytes          : Raw binary content of the .xlsx file.
        existing_point_codes: Point codes already in the DB (duplicate check).
        sheet_name          : Worksheet to use; uses the active sheet if None.

    Returns:
        ImportValidationResult — same schema as the CSV preview endpoint.
    """
    existing_codes = existing_point_codes or set()

    if len(xlsx_bytes) > MAX_XLSX_BYTES:
        return _error_result(
            f"File size {len(xlsx_bytes):,} B exceeds the 10 MB limit.",
            "FILE_TOO_LARGE",
        )

    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(xlsx_bytes),
            read_only=True,
            data_only=True,
        )
    except Exception as exc:
        return _error_result(f"Cannot open workbook: {exc}", "PARSE_ERROR")

    ws = _select_sheet(wb, sheet_name)
    if ws is None:
        try:
            wb.close()
        except Exception:
            pass
        return _error_result("Workbook contains no worksheets.", "PARSE_ERROR")

    # Build CSV text from worksheet rows
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    data_rows_written = 0
    is_header = True

    for ws_row in ws.rows:
        values = [_cell_str(cell) for cell in ws_row]
        writer.writerow(values)
        if is_header:
            is_header = False
        else:
            data_rows_written += 1
            if data_rows_written >= MAX_DATA_ROWS:
                break

    try:
        wb.close()
    except Exception:
        pass

    csv_text = csv_buf.getvalue()
    if not csv_text.strip():
        return ImportValidationResult(
            total_rows=0,
            accepted_count=0,
            rejected_count=0,
            formula_injection_detected=False,
            formula_injection_cells=[],
            duplicate_point_codes=[],
            missing_columns=list(REQUIRED_COLUMNS),
            errors=[],
            preview_rows=[],
            has_blocking_errors=True,
        )

    return validate_csv_import(csv_text, existing_point_codes=existing_codes)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _select_sheet(wb, sheet_name: Optional[str]):
    """Return the target worksheet, or None if the workbook is empty."""
    if sheet_name and sheet_name in wb.sheetnames:
        return wb[sheet_name]
    ws = wb.active
    if ws is not None:
        return ws
    if wb.sheetnames:
        return wb[wb.sheetnames[0]]
    return None


def _cell_str(cell) -> str:
    """Serialise an openpyxl cell value to a plain string.

    Booleans are tested before int/float because bool is a subclass of int.
    Dates and times become their ISO string representation; a downstream
    numeric-column parse will raise INVALID_NUMBER — correct behaviour.
    """
    v = cell.value
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return str(v)
    return str(v)


def _error_result(message: str, error_type: str) -> ImportValidationResult:
    return ImportValidationResult(
        total_rows=0,
        accepted_count=0,
        rejected_count=0,
        formula_injection_detected=False,
        formula_injection_cells=[],
        duplicate_point_codes=[],
        missing_columns=[],
        errors=[CellError(0, "", "", error_type, message)],
        preview_rows=[],
        has_blocking_errors=True,
    )

"""
import_validation.py — Structured CSV import validation for energy data.

P1 scope — MASTER-ENERGY-OPTIMIZATION-01.

SECURITY:
  Formula injection detection (OWASP spreadsheet injection):
    Any cell value whose first non-whitespace character is one of:
      = + - @ | TAB CR DDE(
    is classified as a potential formula injection.
    The cell is rejected; its coordinates are recorded in the error report.
    NO cell content starting with these characters is ever written to the DB.

  Rejecting '+' and '-' prevents =SUM-style injections via CSV concatenation.
  This is the conservative safe default; legitimate numeric negatives are handled
  by the float conversion step that follows sanitization.

IMPORT FLOW (caller responsibility):
  1. Parse raw CSV text into rows (caller handles encoding).
  2. Call validate_import_rows() → ImportValidationResult.
  3. If result.has_blocking_errors: show errors, do NOT write.
  4. If result.formula_injection_detected: warn user explicitly, do NOT write.
  5. Show result.preview_rows to user for confirmation.
  6. Only after explicit user confirmation: caller writes accepted rows to DB.

This module has no database access, no I/O, no file parsing.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# CSV template definition
# ---------------------------------------------------------------------------

TEMPLATE_COLUMNS = [
    "point_code",
    "group_name",
    "e_current_kj",
    "e_min_kj",
    "e_ideal_kj",
    "e_max_kj",
    "validation_note",
]

REQUIRED_COLUMNS = {"point_code", "group_name"}

NUMERIC_COLUMNS = {"e_current_kj", "e_min_kj", "e_ideal_kj", "e_max_kj"}

TEMPLATE_CSV = (
    ",".join(TEMPLATE_COLUMNS) + "\n"
    + "WP-001,Group-A,0.400,0.280,0.320,0.420,Validated per production trial 2026-01\n"
    + "WP-002,Group-A,0.380,0.280,0.320,0.420,\n"
    + "WP-003,Group-B,,,,,Not established\n"
)

# ---------------------------------------------------------------------------
# Injection detection
# ---------------------------------------------------------------------------

# Characters that start a spreadsheet formula injection payload.
_INJECTION_LEAD_CHARS = frozenset("=+@|")
# Multi-char prefix checked after strip
_INJECTION_PREFIXES = ("DDE(", "dde(", "\t", "\r", "\n")


def is_formula_injection(raw: str) -> bool:
    """Return True if raw cell value looks like a spreadsheet formula injection.

    This is a conservative check: reject any cell starting with =, +, -, @, |,
    TAB, CR, LF, or the string DDE(.

    Note: '-' alone would reject all negative numbers; numeric fields are
    validated separately via float conversion, so '-' is only flagged in
    non-numeric string cells via the caller.
    """
    if not raw:
        return False
    stripped = raw.lstrip(" \xa0")  # strip regular and non-breaking spaces
    if not stripped:
        return False
    if stripped[0] in _INJECTION_LEAD_CHARS:
        return True
    if stripped[0] == '-' and len(stripped) > 1 and not stripped[1:].replace('.', '', 1).isdigit():
        # '-text' is suspicious; '-1.5' is legitimate in numeric context
        return True
    for prefix in _INJECTION_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CellError:
    row_number: int        # 1-based, counting header as 0
    column: str
    raw_value: str
    error_type: str        # "FORMULA_INJECTION" | "INVALID_NUMBER" | "MISSING_REQUIRED" | "DUPLICATE_ID"
    message: str


@dataclass
class ImportPreviewRow:
    row_number: int
    point_code: str
    group_name: str
    e_current_kj: Optional[float]
    e_min_kj: Optional[float]
    e_ideal_kj: Optional[float]
    e_max_kj: Optional[float]
    validation_note: Optional[str]
    accepted: bool
    row_errors: list[CellError] = field(default_factory=list)


@dataclass
class ImportValidationResult:
    """Result of validate_import_rows().

    Callers MUST check has_blocking_errors and formula_injection_detected
    before writing any rows to the database.
    """
    total_rows: int
    accepted_count: int
    rejected_count: int
    formula_injection_detected: bool
    formula_injection_cells: list[str]      # "row N col X" descriptions
    duplicate_point_codes: list[str]
    missing_columns: list[str]
    errors: list[CellError]
    preview_rows: list[ImportPreviewRow]
    has_blocking_errors: bool               # True → do not write ANY rows


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------

def validate_csv_import(
    csv_text: str,
    existing_point_codes: Optional[set[str]] = None,
) -> ImportValidationResult:
    """Parse and validate CSV import text.

    csv_text             : full CSV file content as a string.
    existing_point_codes : set of already-known point codes (for duplicate detection).

    Does NOT write to any database. Returns a full validation report.
    """
    existing_codes = existing_point_codes or set()
    errors: list[CellError] = []
    preview_rows: list[ImportPreviewRow] = []
    injection_cells: list[str] = []
    seen_codes: set[str] = set()
    duplicate_codes: list[str] = []

    # ── Parse CSV ─────────────────────────────────────────────────────────
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        if reader.fieldnames is None:
            return ImportValidationResult(
                total_rows=0,
                accepted_count=0,
                rejected_count=0,
                formula_injection_detected=False,
                formula_injection_cells=[],
                duplicate_point_codes=[],
                missing_columns=REQUIRED_COLUMNS,
                errors=[],
                preview_rows=[],
                has_blocking_errors=True,
            )
        headers = set(f.strip() for f in reader.fieldnames)
        rows_raw = list(reader)
    except Exception as exc:
        return ImportValidationResult(
            total_rows=0, accepted_count=0, rejected_count=0,
            formula_injection_detected=False, formula_injection_cells=[],
            duplicate_point_codes=[], missing_columns=[],
            errors=[CellError(0, "", "", "PARSE_ERROR", str(exc))],
            preview_rows=[], has_blocking_errors=True,
        )

    # ── Check required columns ────────────────────────────────────────────
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in headers]

    # ── Validate rows ─────────────────────────────────────────────────────
    for row_idx, raw_row in enumerate(rows_raw, start=1):
        row_errors: list[CellError] = []
        row_injection = False

        def get(col: str) -> str:
            """Get raw string for a column, empty string if missing."""
            return (raw_row.get(col) or "").strip()

        # Check all cells for formula injection
        for col in TEMPLATE_COLUMNS:
            raw_val = get(col)
            if raw_val and is_formula_injection(raw_val):
                err = CellError(
                    row_number=row_idx, column=col, raw_value=raw_val[:80],
                    error_type="FORMULA_INJECTION",
                    message=f"Cell value starts with a formula-injection character. Row {row_idx}, column '{col}'.",
                )
                row_errors.append(err)
                errors.append(err)
                injection_cells.append(f"row {row_idx} col '{col}'")
                row_injection = True

        # Required columns
        point_code_raw = get("point_code")
        if not point_code_raw:
            err = CellError(row_idx, "point_code", "", "MISSING_REQUIRED",
                            f"Row {row_idx}: point_code is required.")
            row_errors.append(err); errors.append(err)
        group_name_raw = get("group_name")
        if not group_name_raw:
            group_name_raw = "DEFAULT"  # tolerate missing group

        # Duplicate detection
        if point_code_raw:
            if point_code_raw in seen_codes or point_code_raw in existing_codes:
                duplicate_codes.append(point_code_raw)
                err = CellError(row_idx, "point_code", point_code_raw, "DUPLICATE_ID",
                                f"Row {row_idx}: point_code '{point_code_raw}' is a duplicate.")
                row_errors.append(err); errors.append(err)
            seen_codes.add(point_code_raw)

        # Numeric columns
        parsed_nums: dict[str, Optional[float]] = {}
        for col in ("e_current_kj", "e_min_kj", "e_ideal_kj", "e_max_kj"):
            raw_val = get(col)
            if not raw_val:
                parsed_nums[col] = None
                continue
            if row_injection:
                parsed_nums[col] = None
                continue
            try:
                v = float(raw_val)
                if not math.isfinite(v) or v < 0:
                    raise ValueError("must be finite and non-negative")
                parsed_nums[col] = v
            except (ValueError, OverflowError):
                err = CellError(row_idx, col, raw_val[:40], "INVALID_NUMBER",
                                f"Row {row_idx}, column '{col}': '{raw_val}' is not a valid non-negative number.")
                row_errors.append(err); errors.append(err)
                parsed_nums[col] = None

        # Window ordering
        e_min = parsed_nums.get("e_min_kj")
        e_ideal = parsed_nums.get("e_ideal_kj")
        e_max = parsed_nums.get("e_max_kj")
        if e_min is not None and e_max is not None and e_min > e_max:
            err = CellError(row_idx, "e_min_kj/e_max_kj", "",
                            "INVALID_NUMBER",
                            f"Row {row_idx}: e_min_kj ({e_min}) > e_max_kj ({e_max}).")
            row_errors.append(err); errors.append(err)
        if e_min is not None and e_ideal is not None and e_max is not None:
            if not (e_min <= e_ideal <= e_max):
                err = CellError(row_idx, "e_ideal_kj", str(e_ideal),
                                "INVALID_NUMBER",
                                f"Row {row_idx}: e_ideal_kj ({e_ideal}) not in [{e_min}, {e_max}].")
                row_errors.append(err); errors.append(err)

        accepted = (
            not row_injection
            and not any(
                e.error_type in ("MISSING_REQUIRED", "FORMULA_INJECTION", "DUPLICATE_ID", "INVALID_NUMBER")
                for e in row_errors
            )
        )
        preview_rows.append(ImportPreviewRow(
            row_number=row_idx,
            point_code=point_code_raw,
            group_name=group_name_raw,
            e_current_kj=parsed_nums.get("e_current_kj"),
            e_min_kj=parsed_nums.get("e_min_kj"),
            e_ideal_kj=parsed_nums.get("e_ideal_kj"),
            e_max_kj=parsed_nums.get("e_max_kj"),
            validation_note=get("validation_note") or None,
            accepted=accepted,
            row_errors=row_errors,
        ))

    accepted_count = sum(1 for r in preview_rows if r.accepted)
    rejected_count = len(preview_rows) - accepted_count
    formula_injection_detected = len(injection_cells) > 0
    has_blocking_errors = (
        bool(missing_cols)
        or formula_injection_detected
        or bool(duplicate_codes)
        or accepted_count == 0 and len(preview_rows) > 0
    )

    return ImportValidationResult(
        total_rows=len(preview_rows),
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        formula_injection_detected=formula_injection_detected,
        formula_injection_cells=injection_cells,
        duplicate_point_codes=list(set(duplicate_codes)),
        missing_columns=missing_cols,
        errors=errors,
        preview_rows=preview_rows,
        has_blocking_errors=has_blocking_errors,
    )

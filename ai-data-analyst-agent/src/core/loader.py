"""
Loads a user-uploaded CSV/Excel file into a pandas DataFrame, defensively.

Real-world uploads break in predictable ways: wrong encoding, a stray BOM,
Excel files with several sheets, or files that are simply too large to hold
in memory comfortably. This module exists so every other module can assume
`load_dataset()` always returns either a clean DataFrame or a clear error —
never a half-loaded, silently-corrupted one.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from config import settings


@dataclass
class LoadResult:
    success: bool
    df: Optional[pd.DataFrame] = None
    error: Optional[str] = None
    sheet_names: Optional[list[str]] = None  # populated when an Excel file has multiple sheets


ENCODING_FALLBACKS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]


def validate_file(filename: str, size_bytes: int) -> Optional[str]:
    """Returns an error string if the file fails basic checks, else None."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        return f"Unsupported file type '{ext}'. Upload a CSV or Excel file."
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        return f"File is {size_bytes / 1e6:.1f} MB, which exceeds the {settings.MAX_FILE_SIZE_MB} MB limit."
    if size_bytes == 0:
        return "The file appears to be empty."
    return None


def _read_csv_with_fallback(raw_bytes: bytes) -> pd.DataFrame:
    last_error: Exception | None = None
    for enc in ENCODING_FALLBACKS:
        try:
            return pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue
    # Last resort: decode ignoring bad bytes rather than failing outright.
    try:
        return pd.read_csv(io.BytesIO(raw_bytes), encoding="utf-8", encoding_errors="ignore")
    except Exception as e:
        raise last_error or e


def load_dataset(filename: str, raw_bytes: bytes, sheet_name: Optional[str] = None) -> LoadResult:
    """
    Main entry point. `raw_bytes` is the uploaded file's raw content
    (e.g. `uploaded_file.getvalue()` from Streamlit).
    """
    error = validate_file(filename, len(raw_bytes))
    if error:
        return LoadResult(success=False, error=error)

    ext = Path(filename).suffix.lower()

    try:
        if ext == ".csv":
            df = _read_csv_with_fallback(raw_bytes)
        else:  # .xlsx / .xls
            xls = pd.ExcelFile(io.BytesIO(raw_bytes))
            if len(xls.sheet_names) > 1 and sheet_name is None:
                # Ask the caller (UI layer) to let the user pick a sheet.
                return LoadResult(success=False, sheet_names=xls.sheet_names,
                                   error="MULTIPLE_SHEETS")
            chosen_sheet = sheet_name or xls.sheet_names[0]
            df = pd.read_excel(xls, sheet_name=chosen_sheet)
    except Exception as e:
        return LoadResult(success=False, error=f"Could not parse file: {e}")

    if df.empty:
        return LoadResult(success=False, error="The dataset has no rows after parsing.")
    if df.shape[1] == 0:
        return LoadResult(success=False, error="No columns detected — check the file's delimiter/format.")

    # Normalize column names: strip whitespace, keep original casing (renaming is a judgment
    # call we don't want to make silently for the user's real column names).
    df.columns = [str(c).strip() for c in df.columns]

    return LoadResult(success=True, df=df)

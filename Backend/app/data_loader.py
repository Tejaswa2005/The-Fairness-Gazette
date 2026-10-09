from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}


def generate_synthetic_dataset(rows: int = 500, random_state: int = 42) -> pd.DataFrame:
    """Create a realistic loan-style dataset for testing the fairness engine."""

    if rows <= 0:
        raise ValueError("rows must be a positive integer.")

    rng = np.random.default_rng(random_state)

    gender = rng.choice(["Female", "Male", "Non-binary"], size=rows, p=[0.46, 0.47, 0.07])
    region = rng.choice(["North", "South", "East", "West"], size=rows, p=[0.28, 0.26, 0.23, 0.23])
    income = rng.normal(loc=72_000, scale=18_000, size=rows).clip(24_000, 160_000).round(0)
    credit_score = rng.normal(loc=675, scale=55, size=rows).clip(480, 825).round(0)
    age = rng.integers(21, 66, size=rows)
    employment_years = rng.integers(0, 31, size=rows)
    debt_to_income = rng.normal(loc=0.33, scale=0.12, size=rows).clip(0.05, 0.65).round(3)
    loan_amount = rng.normal(loc=26_000, scale=9_000, size=rows).clip(4_000, 75_000).round(0)

    region_bias = np.where(np.isin(region, ["South", "West"]), -0.35, 0.0)
    gender_bias = np.where(gender == "Female", -0.25, 0.0)
    non_binary_bias = np.where(gender == "Non-binary", -0.18, 0.0)

    income_score = (income - 55_000) / 25_000
    credit_score_component = (credit_score - 640) / 80
    employment_component = employment_years / 10
    debt_penalty = debt_to_income * 2.1
    loan_penalty = loan_amount / 90_000

    logit = (
        0.95 * income_score
        + 1.05 * credit_score_component
        + 0.25 * employment_component
        - 0.95 * debt_penalty
        - 0.35 * loan_penalty
        + region_bias
        + gender_bias
        + non_binary_bias
        + rng.normal(0, 0.45, size=rows)
    )
    probability = 1.0 / (1.0 + np.exp(-logit))
    approved = (probability >= rng.random(rows)).astype(int)

    data = pd.DataFrame(
        {
            "income": income,
            "credit_score": credit_score,
            "age": age,
            "employment_years": employment_years,
            "debt_to_income": debt_to_income,
            "loan_amount": loan_amount,
            "gender": gender,
            "region": region,
            "approved": approved,
        }
    )

    missing_locations = rng.choice(data.index, size=max(1, rows // 40), replace=False)
    if len(missing_locations) > 0:
        data.loc[missing_locations[: len(missing_locations) // 2], "income"] = np.nan
        data.loc[missing_locations[len(missing_locations) // 2 :], "region"] = None

    return clean_dataframe(data)


def load_dataset(file_path: str | Path | None = None, *, synthetic_rows: int = 500) -> pd.DataFrame:
    """Load a dataset from disk or return a synthetic dataset when no file is given."""

    if file_path is None:
        return generate_synthetic_dataset(rows=synthetic_rows)

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{suffix}'. Supported formats are: {allowed}.")

    try:
        if suffix == ".csv":
            frame = pd.read_csv(path)
        elif suffix in {".xlsx", ".xls"}:
            frame = _read_excel_file(path)
        else:
            frame = _read_json_file(path)
    except Exception as exc:  # pragma: no cover - re-raised with friendlier message
        raise ValueError(f"Could not read dataset '{path.name}': {exc}") from exc

    return clean_dataframe(frame)


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize missing values, strip messy column names, and coerce easy type issues."""

    if frame is None or frame.empty:
        raise ValueError("The dataset is empty. Please provide rows with real data.")

    cleaned = frame.copy()
    cleaned.columns = [_normalize_column_name(column, index) for index, column in enumerate(cleaned.columns)]
    cleaned = cleaned.dropna(how="all")
    cleaned = cleaned.dropna(axis=1, how="all")

    if cleaned.empty:
        raise ValueError("The dataset became empty after removing blank rows and columns.")

    for column in cleaned.columns:
        series = cleaned[column]

        if pd.api.types.is_datetime64_any_dtype(series):
            cleaned[column] = series.fillna(method="ffill").fillna(method="bfill")
            continue

        if pd.api.types.is_bool_dtype(series):
            cleaned[column] = series.fillna(series.mode(dropna=True).iloc[0] if not series.dropna().empty else False)
            continue

        if pd.api.types.is_numeric_dtype(series):
            numeric_series = pd.to_numeric(series, errors="coerce")
            median = float(numeric_series.median()) if not numeric_series.dropna().empty else 0.0
            cleaned[column] = numeric_series.fillna(median)
            continue

        coerced_numeric = pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")
        numeric_ratio = coerced_numeric.notna().mean()
        if numeric_ratio >= 0.8:
            median = float(coerced_numeric.median()) if not coerced_numeric.dropna().empty else 0.0
            cleaned[column] = coerced_numeric.fillna(median)
            continue

        text_series = series.astype("string").str.strip()
        text_series = text_series.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "null": pd.NA})
        if text_series.dropna().empty:
            cleaned[column] = text_series.fillna("Unknown")
        else:
            mode_values = text_series.dropna().mode()
            fallback = mode_values.iloc[0] if not mode_values.empty else "Unknown"
            cleaned[column] = text_series.fillna(fallback)

    cleaned = cleaned.reset_index(drop=True)
    return cleaned


def _read_excel_file(path: Path) -> pd.DataFrame:
    engine = "openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd"
    try:
        return pd.read_excel(path, engine=engine)
    except ImportError as exc:
        raise ValueError(
            f"Excel support for '{path.suffix}' files is unavailable because the '{engine}' engine is missing."
        ) from exc


def _read_json_file(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as handle:
        payload: Any = json.load(handle)

    if isinstance(payload, list):
        if not payload:
            raise ValueError("The JSON file contains an empty list.")
        if all(isinstance(item, dict) for item in payload):
            return pd.DataFrame(payload)
        raise ValueError("JSON lists must contain objects with named fields.")

    if isinstance(payload, dict):
        if "records" in payload and isinstance(payload["records"], list):
            return pd.DataFrame(payload["records"])
        if "data" in payload and isinstance(payload["data"], list):
            return pd.DataFrame(payload["data"])
        return pd.json_normalize(payload)

    raise ValueError("Unsupported JSON structure. Use a list of records or an object with tabular data.")


def _normalize_column_name(name: Any, index: int) -> str:
    text = str(name).strip()
    if not text:
        return f"column_{index + 1}"

    normalized = []
    previous_was_separator = False
    for character in text:
        if character.isalnum():
            normalized.append(character.lower())
            previous_was_separator = False
        else:
            if not previous_was_separator:
                normalized.append("_")
                previous_was_separator = True

    cleaned = "".join(normalized).strip("_")
    return cleaned or f"column_{index + 1}"
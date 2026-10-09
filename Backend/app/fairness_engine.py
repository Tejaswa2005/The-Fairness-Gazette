from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fairlearn.metrics import MetricFrame, demographic_parity_difference, equalized_odds_difference, selection_rate
from fairlearn.postprocessing import ThresholdOptimizer
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.data_loader import clean_dataframe, generate_synthetic_dataset, load_dataset


DEFAULT_TARGET_COLUMN = "approved"
DEFAULT_SENSITIVE_FEATURE = "gender"
DEFAULT_VERDICT_THRESHOLD = 70.0

logger = logging.getLogger("fairness-gazette.engine")


def audit_fairness(
    data: pd.DataFrame | None = None,
    *,
    file_path: str | Path | None = None,
    sensitive_feature: str = DEFAULT_SENSITIVE_FEATURE,
    target_column: str = DEFAULT_TARGET_COLUMN,
    verdict_threshold: float = DEFAULT_VERDICT_THRESHOLD,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run the fairness audit and return a structured summary."""

    logger.info("Starting fairness audit for sensitive_feature=%s target_column=%s", sensitive_feature, target_column)
    source = _resolve_dataset(data=data, file_path=file_path)
    dataset = clean_dataframe(source)

    prepared = _prepare_training_data(dataset, sensitive_feature=sensitive_feature, target_column=target_column)
    X_train, X_test, y_train, y_test, _, sensitive_test = _split_data(
        prepared.features,
        prepared.target,
        prepared.sensitive,
        random_state=random_state,
    )

    model = _build_classifier(prepared.features)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    metrics = _compute_metrics(y_test, predictions, sensitive_test)
    fairness_score = _calculate_fairness_score(metrics)
    verdict = _determine_verdict(fairness_score, threshold=verdict_threshold)
    editor_note = generate_editor_note(fairness_score, verdict, metrics)

    logger.info("Audit finished with fairness_score=%.2f verdict=%s", fairness_score, verdict)

    return {
        "dataset": {
            "rows": int(dataset.shape[0]),
            "columns": list(dataset.columns),
            "sensitive_feature": sensitive_feature,
            "target_column": target_column,
        },
        "baseline": {
            "metrics": metrics,
            "fairness_score": fairness_score,
            "verdict": verdict,
            "editor_note": editor_note,
        },
        "training": {
            "rows_train": int(len(X_train)),
            "rows_test": int(len(X_test)),
            "model": "LogisticRegression",
        },
    }


def mitigate_fairness(
    data: pd.DataFrame | None = None,
    *,
    file_path: str | Path | None = None,
    sensitive_feature: str = DEFAULT_SENSITIVE_FEATURE,
    target_column: str = DEFAULT_TARGET_COLUMN,
    verdict_threshold: float = DEFAULT_VERDICT_THRESHOLD,
    random_state: int = 42,
) -> dict[str, Any]:
    """Run the baseline model, then apply Fairlearn mitigation and compare the results."""

    logger.info("Starting mitigation comparison for sensitive_feature=%s target_column=%s", sensitive_feature, target_column)
    source = _resolve_dataset(data=data, file_path=file_path)
    dataset = clean_dataframe(source)

    prepared = _prepare_training_data(dataset, sensitive_feature=sensitive_feature, target_column=target_column)
    X_train, X_test, y_train, y_test, sensitive_train, sensitive_test = _split_data(
        prepared.features,
        prepared.target,
        prepared.sensitive,
        random_state=random_state,
    )

    base_model = _build_classifier(prepared.features)
    base_model.fit(X_train, y_train)
    baseline_predictions = base_model.predict(X_test)
    baseline_metrics = _compute_metrics(y_test, baseline_predictions, sensitive_test)
    baseline_score = _calculate_fairness_score(baseline_metrics)
    baseline_verdict = _determine_verdict(baseline_score, threshold=verdict_threshold)

    mitigation_model = ThresholdOptimizer(
        estimator=_build_classifier(prepared.features),
        constraints="equalized_odds",
        predict_method="predict_proba",
    )
    mitigation_model.fit(X_train, y_train, sensitive_features=sensitive_train)
    mitigated_predictions = mitigation_model.predict(X_test, sensitive_features=sensitive_test)

    mitigated_metrics = _compute_metrics(y_test, mitigated_predictions, sensitive_test)
    mitigated_score = _calculate_fairness_score(mitigated_metrics)
    mitigated_verdict = _determine_verdict(mitigated_score, threshold=verdict_threshold)

    logger.info("Mitigation comparison finished with score_change=%.2f", mitigated_score - baseline_score)

    return {
        "before": {
            "metrics": baseline_metrics,
            "fairness_score": baseline_score,
            "verdict": baseline_verdict,
            "editor_note": generate_editor_note(baseline_score, baseline_verdict, baseline_metrics),
        },
        "after": {
            "metrics": mitigated_metrics,
            "fairness_score": mitigated_score,
            "verdict": mitigated_verdict,
            "editor_note": generate_editor_note(mitigated_score, mitigated_verdict, mitigated_metrics),
        },
        "improvement": {
            "score_change": round(mitigated_score - baseline_score, 2),
            "demographic_parity_change": round(
                baseline_metrics["demographic_parity_difference"] - mitigated_metrics["demographic_parity_difference"],
                4,
            ),
            "equalized_odds_change": round(
                baseline_metrics["equalized_odds_difference"] - mitigated_metrics["equalized_odds_difference"],
                4,
            ),
        },
    }


def generate_editor_note(fairness_score: float, verdict: str, metrics: dict[str, Any]) -> str:
    """Write a short newspaper-style note that matches the severity of the verdict."""

    dp_diff = float(metrics.get("demographic_parity_difference", 0.0))
    eo_diff = float(metrics.get("equalized_odds_difference", 0.0))
    severity = _severity_band(fairness_score)

    if severity == "critical":
        first_line = (
            f"BREAKING: The tribunal finds the model {verdict} with a fairness score of {fairness_score:.1f}."
        )
        second_line = (
            f"The record shows sharp disparity, with demographic parity at {dp_diff:.3f} and equalized odds at {eo_diff:.3f}."
        )
        third_line = "The evidence points to a model that treats comparable groups unevenly and demands immediate reform."
    elif severity == "high":
        first_line = f"The court returns a {verdict} verdict as the model posts a fairness score of {fairness_score:.1f}."
        second_line = (
            f"Disparities remain visible, with demographic parity at {dp_diff:.3f} and equalized odds at {eo_diff:.3f}."
        )
        third_line = "The model may still function, but the fairness record is too uneven to ignore."
    elif severity == "moderate":
        first_line = f"The gallery hears an uneasy {verdict} as the model reaches a fairness score of {fairness_score:.1f}."
        second_line = (
            f"The numbers show moderate imbalance, with demographic parity at {dp_diff:.3f} and equalized odds at {eo_diff:.3f}."
        )
        third_line = "This verdict is fair enough for the moment, though the case for improvement remains open."
    else:
        first_line = f"The model is {verdict} with a strong fairness score of {fairness_score:.1f}."
        second_line = (
            f"Only modest differences remain, with demographic parity at {dp_diff:.3f} and equalized odds at {eo_diff:.3f}."
        )
        third_line = "By the paper's account, the model's treatment of groups is largely even-handed."

    return "\n".join([first_line, second_line, third_line])


def run_demo() -> dict[str, Any]:
    """Run the fairness engine on a synthetic dataset and return the demo output."""

    synthetic_data = generate_synthetic_dataset()
    baseline = audit_fairness(synthetic_data)
    mitigation = mitigate_fairness(synthetic_data)

    demo_output = {
        "baseline": baseline,
        "mitigation": mitigation,
    }
    return demo_output


def _resolve_dataset(
    *,
    data: pd.DataFrame | None,
    file_path: str | Path | None,
) -> pd.DataFrame:
    if data is not None:
        return data.copy()
    return load_dataset(file_path)


def _prepare_training_data(
    frame: pd.DataFrame,
    *,
    sensitive_feature: str,
    target_column: str,
) -> _PreparedData:
    if sensitive_feature == target_column:
        raise ValueError("The sensitive feature and target column must be different.")

    missing_columns = [column for column in [sensitive_feature, target_column] if column not in frame.columns]
    if missing_columns:
        missing_list = ", ".join(missing_columns)
        raise ValueError(f"Missing required column(s): {missing_list}.")

    target = _encode_binary_target(frame[target_column])
    sensitive = frame[sensitive_feature].astype("string").fillna("Unknown")

    feature_frame = frame.drop(columns=[target_column, sensitive_feature]).copy()
    if feature_frame.empty:
        raise ValueError("No feature columns remain after removing the target and sensitive feature.")

    categorical_columns = [column for column in feature_frame.columns if not pd.api.types.is_numeric_dtype(feature_frame[column])]
    numeric_columns = [column for column in feature_frame.columns if column not in categorical_columns]

    if not numeric_columns and not categorical_columns:
        raise ValueError("The dataset does not contain usable feature columns for model training.")

    return _PreparedData(
        features=feature_frame,
        target=target,
        sensitive=sensitive,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
    )


def _build_classifier(feature_frame: pd.DataFrame) -> Pipeline:
    numeric_columns = [column for column in feature_frame.columns if pd.api.types.is_numeric_dtype(feature_frame[column])]
    categorical_columns = [column for column in feature_frame.columns if column not in numeric_columns]

    transformers = []
    if numeric_columns:
        transformers.append(("numeric", StandardScaler(), numeric_columns))
    if categorical_columns:
        transformers.append(
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_columns,
            )
        )

    if not transformers:
        raise ValueError("Unable to build a model because no usable feature columns were found.")

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    classifier = LogisticRegression(max_iter=1_000, solver="lbfgs")

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def _split_data(
    features: pd.DataFrame,
    target: pd.Series,
    sensitive: pd.Series,
    *,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    stratification_labels = target.astype("string") + "__" + sensitive.astype("string")

    try:
        X_train, X_test, y_train, y_test, sensitive_train, sensitive_test = train_test_split(
            features,
            target,
            sensitive,
            test_size=0.3,
            random_state=random_state,
            stratify=stratification_labels,
        )
    except ValueError:
        X_train, X_test, y_train, y_test, sensitive_train, sensitive_test = train_test_split(
            features,
            target,
            sensitive,
            test_size=0.3,
            random_state=random_state,
            stratify=target,
        )

    return X_train, X_test, y_train, y_test, sensitive_train, sensitive_test


def _compute_metrics(y_true: pd.Series, y_pred: np.ndarray | pd.Series, sensitive: pd.Series) -> dict[str, Any]:
    sensitive_text = sensitive.astype("string").fillna("Unknown")
    predicted = pd.Series(y_pred, index=y_true.index, name="prediction")

    selection_rates = MetricFrame(
        metrics=selection_rate,
        y_true=y_true,
        y_pred=predicted,
        sensitive_features=sensitive_text,
    ).by_group

    selection_rate_dict = {str(group): round(float(rate), 4) for group, rate in selection_rates.items()}
    selection_rate_values = list(selection_rate_dict.values())
    selection_rate_spread = round(max(selection_rate_values) - min(selection_rate_values), 4) if selection_rate_values else 0.0

    return {
        "demographic_parity_difference": round(
            float(demographic_parity_difference(y_true, predicted, sensitive_features=sensitive_text)),
            4,
        ),
        "equalized_odds_difference": round(
            float(equalized_odds_difference(y_true, predicted, sensitive_features=sensitive_text)),
            4,
        ),
        "selection_rate_by_group": selection_rate_dict,
        "selection_rate_spread": selection_rate_spread,
    }


def _calculate_fairness_score(metrics: dict[str, Any]) -> float:
    dp_diff = min(max(float(metrics.get("demographic_parity_difference", 0.0)), 0.0), 1.0)
    eo_diff = min(max(float(metrics.get("equalized_odds_difference", 0.0)), 0.0), 1.0)
    spread = min(max(float(metrics.get("selection_rate_spread", 0.0)), 0.0), 1.0)

    penalty = (dp_diff + eo_diff + spread) / 3.0
    score = max(0.0, 100.0 * (1.0 - penalty))
    return round(score, 2)


def _determine_verdict(fairness_score: float, *, threshold: float) -> str:
    return "ACQUITTED" if fairness_score >= threshold else "GUILTY"


def _severity_band(fairness_score: float) -> str:
    if fairness_score < 40:
        return "critical"
    if fairness_score < 60:
        return "high"
    if fairness_score < 80:
        return "moderate"
    return "low"


def _encode_binary_target(target: pd.Series) -> pd.Series:
    values = target.copy()
    if pd.api.types.is_numeric_dtype(values):
        numeric = pd.to_numeric(values, errors="coerce")
        if numeric.isna().any():
            raise ValueError("The target column contains non-numeric values that could not be cleaned.")
        unique_values = sorted(pd.unique(numeric))
        if len(unique_values) != 2:
            raise ValueError("The target column must contain exactly two classes for binary classification.")
        positive = unique_values[-1]
        return (numeric == positive).astype(int)

    normalized = values.astype("string").str.strip().str.lower()
    normalized = normalized.replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "null": pd.NA})
    if normalized.isna().any():
        raise ValueError("The target column contains missing values that must be filled before training.")

    positive_tokens = {
        "1",
        "true",
        "yes",
        "approved",
        "approve",
        "hired",
        "grant",
        "granted",
        "positive",
        "favorable",
    }
    negative_tokens = {
        "0",
        "false",
        "no",
        "denied",
        "deny",
        "rejected",
        "reject",
        "negative",
        "unfavorable",
    }

    unique_values = list(pd.unique(normalized))
    if len(unique_values) != 2:
        raise ValueError("The target column must contain exactly two classes for binary classification.")

    if set(unique_values).issubset(positive_tokens | negative_tokens):
        positive_label = next((value for value in unique_values if value in positive_tokens), unique_values[-1])
        return (normalized == positive_label).astype(int)

    positive_label = sorted(unique_values)[-1]
    return (normalized == positive_label).astype(int)


def _to_native(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_native(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_native(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_native(item) for item in value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Series):
        return {str(key): _to_native(item) for key, item in value.to_dict().items()}
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    return value


def _print_json(title: str, payload: Any) -> None:
    print(f"\n{title}")
    print(json.dumps(_to_native(payload), indent=2, ensure_ascii=True))


class _PreparedData:
    def __init__(
        self,
        *,
        features: pd.DataFrame,
        target: pd.Series,
        sensitive: pd.Series,
        numeric_columns: list[str],
        categorical_columns: list[str],
    ) -> None:
        self.features = features
        self.target = target
        self.sensitive = sensitive
        self.numeric_columns = numeric_columns
        self.categorical_columns = categorical_columns


if __name__ == "__main__":
    demo_dataset = generate_synthetic_dataset()
    demo_baseline = audit_fairness(demo_dataset)
    demo_mitigation = mitigate_fairness(demo_dataset)

    _print_json("BASELINE AUDIT", demo_baseline)
    _print_json("MITIGATION COMPARISON", demo_mitigation)
"""
drift.py

Evidently AI helpers for data profiling and drift detection.

Three responsibilities:
  - build_data_profile(df)           -> Report  (data quality / summary stats)
  - build_drift_report(ref, cur)     -> Report  (data + target drift)
  - save_report(report, name)        -> (html_path, json_path)

Reports are written under reports/evidently/ with a timestamp suffix so
historic runs are preserved (the directory is gitignored except for a
.gitkeep placeholder).
"""

import json
import os
from datetime import datetime

import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import (
    DataDriftPreset,
    DataQualityPreset,
    TargetDriftPreset,
)
from evidently.report import Report

from src.data.preprocess import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CATEGORICAL_WITH_MISSING,
    NUMERIC_FEATURES,
    NUMERIC_WITH_MISSING,
    TARGET,
)

DEFAULT_OUTPUT_DIR = "reports/evidently"


def build_column_mapping(target_col=TARGET):
    """Return an Evidently ColumnMapping consistent with preprocess.py."""
    return ColumnMapping(
        target=target_col,
        prediction=None,
        numerical_features=NUMERIC_FEATURES + NUMERIC_WITH_MISSING,
        categorical_features=(
            CATEGORICAL_FEATURES + CATEGORICAL_WITH_MISSING + BINARY_FEATURES
        ),
    )


def build_data_profile(df: pd.DataFrame, target_col=TARGET) -> Report:
    """Run a DataQualityPreset profile on a single DataFrame."""
    report = Report(metrics=[DataQualityPreset()])
    report.run(
        reference_data=None,
        current_data=df,
        column_mapping=build_column_mapping(target_col),
    )
    return report


def build_drift_report(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    target_col=TARGET,
) -> Report:
    """Run DataDriftPreset (+ TargetDriftPreset if target present in both)."""
    metrics = [DataDriftPreset()]
    if target_col in reference_df.columns and target_col in current_df.columns:
        metrics.append(TargetDriftPreset())
    report = Report(metrics=metrics)
    report.run(
        reference_data=reference_df,
        current_data=current_df,
        column_mapping=build_column_mapping(target_col),
    )
    return report


def save_report(report: Report, name: str, output_dir: str = DEFAULT_OUTPUT_DIR):
    """Write the report as HTML + JSON, returning both paths."""
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base = f"{name}_{ts}"
    html_path = os.path.join(output_dir, f"{base}.html")
    json_path = os.path.join(output_dir, f"{base}.json")
    report.save_html(html_path)
    with open(json_path, "w") as fh:
        json.dump(report.as_dict(), fh, indent=2, default=str)
    return html_path, json_path


def extract_drift_summary(drift_report: Report) -> dict:
    """Pull the headline drift figures out of a DataDriftPreset report."""
    payload = drift_report.as_dict()
    for metric in payload.get("metrics", []):
        result = metric.get("result", {})
        if "dataset_drift" in result:
            return {
                "dataset_drift": bool(result.get("dataset_drift", False)),
                "number_of_columns": int(result.get("number_of_columns", 0)),
                "number_of_drifted_columns": int(
                    result.get("number_of_drifted_columns", 0)
                ),
                "share_of_drifted_columns": float(
                    result.get("share_of_drifted_columns", 0.0)
                ),
            }
    return {
        "dataset_drift": False,
        "number_of_columns": 0,
        "number_of_drifted_columns": 0,
        "share_of_drifted_columns": 0.0,
    }

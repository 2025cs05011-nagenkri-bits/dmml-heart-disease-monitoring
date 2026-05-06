"""
test_drift.py

Unit tests for the Evidently AI drift utilities in src/monitoring/drift.py.
"""

import os

import numpy as np
import pandas as pd
import pytest

from src.monitoring.drift import (
    build_data_profile,
    build_drift_report,
    extract_drift_summary,
    save_report,
)


def _toy_dataframe(n=120, seed=0):
    """In-memory DataFrame mimicking the Cleveland schema."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "age":      rng.integers(40, 70, n),
        "sex":      rng.integers(0, 2, n),
        "cp":       rng.integers(1, 5, n),
        "trestbps": rng.integers(110, 160, n),
        "chol":     rng.integers(180, 320, n),
        "fbs":      rng.integers(0, 2, n),
        "restecg":  rng.integers(0, 3, n),
        "thalach":  rng.integers(110, 190, n),
        "exang":    rng.integers(0, 2, n),
        "oldpeak":  rng.uniform(0.0, 4.0, n).round(1),
        "slope":    rng.integers(1, 4, n),
        "ca":       rng.integers(0, 4, n).astype(float),
        "thal":     rng.choice([3.0, 6.0, 7.0], n),
        "target":   rng.integers(0, 2, n),
    })


def test_no_drift_on_identical_data():
    """Reference vs identical reference -> dataset_drift must be False."""
    df = _toy_dataframe()
    report = build_drift_report(df, df.copy())
    summary = extract_drift_summary(report)
    assert summary["dataset_drift"] is False
    assert summary["number_of_drifted_columns"] == 0


def test_drift_detected_on_heavily_shifted_data():
    """Aggressively perturbed numerics + categoricals -> dataset_drift True."""
    reference = _toy_dataframe(seed=0)
    current = reference.copy()
    for col in ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]:
        current[col] = current[col] + current[col].std() * 3.0
    for col in ["cp", "restecg", "slope", "thal"]:
        current[col] = (current[col].fillna(current[col].mode()[0]).astype(int) % 4) + 1
    report = build_drift_report(reference, current)
    summary = extract_drift_summary(report)
    assert summary["dataset_drift"] is True
    assert summary["share_of_drifted_columns"] >= 0.5


def test_profile_generates_html_and_json(tmp_path):
    """save_report must produce a non-empty HTML and a parseable JSON."""
    df = _toy_dataframe()
    report = build_data_profile(df)
    html_path, json_path = save_report(
        report, "profile_test", output_dir=str(tmp_path),
    )
    assert os.path.exists(html_path)
    assert os.path.getsize(html_path) > 1000, "HTML report suspiciously small"
    assert os.path.exists(json_path)
    import json
    with open(json_path) as fh:
        payload = json.load(fh)
    assert "metrics" in payload
    assert len(payload["metrics"]) > 0


def test_extract_drift_summary_keys():
    """Summary dict must always expose the four expected keys."""
    df = _toy_dataframe()
    report = build_drift_report(df, df.copy())
    summary = extract_drift_summary(report)
    expected_keys = {
        "dataset_drift",
        "number_of_columns",
        "number_of_drifted_columns",
        "share_of_drifted_columns",
    }
    assert set(summary.keys()) == expected_keys


@pytest.mark.parametrize("col,delta", [("age", 25), ("chol", 150), ("thalach", -40)])
def test_single_column_shift_marks_that_column(col, delta):
    """Shifting one numeric column by a large delta should flag it as drifted."""
    reference = _toy_dataframe(seed=1)
    current = reference.copy()
    current[col] = current[col] + delta
    report = build_drift_report(reference, current)
    payload = report.as_dict()
    drift_table = None
    for metric in payload["metrics"]:
        result = metric.get("result", {})
        if "drift_by_columns" in result:
            drift_table = result["drift_by_columns"]
            break
    assert drift_table is not None, "DataDriftPreset did not produce per-column drift table"
    assert drift_table[col]["drift_detected"] is True

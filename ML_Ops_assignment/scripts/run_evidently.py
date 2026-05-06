"""
run_evidently.py

Generate an Evidently AI data profile and a reference-vs-current drift
report for the Heart Disease pipeline. Reports are written under
reports/evidently/ as both HTML (for humans) and JSON (for CI / further
processing).

By default the comparison is:
  reference = data/reference/reference_train_v1.0.0.csv  (frozen baseline)
  current   = data/processed/train.csv                   (today's regenerated split)

This catches three classes of issue:
  - Raw data file changed upstream
  - Split logic / random seed in src/data/prepare.py changed
  - Schema or value distributions diverge from the v1.0.0 baseline

Exits non-zero when the drift report flags ``dataset_drift=True`` so the
script can gate a CI job.

Usage:
  python scripts/run_evidently.py
  python scripts/run_evidently.py --reference data/reference/reference_train_v1.0.0.csv \
                                  --current   data/incoming/prod_sample.csv
  python scripts/run_evidently.py --no-fail-on-drift
"""

import argparse
import json
import os
import sys

import pandas as pd

# Make the project root importable when invoked as ``python scripts/...``.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from src.monitoring.drift import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    build_data_profile,
    build_drift_report,
    extract_drift_summary,
    save_report,
)

DEFAULT_REFERENCE = "data/reference/reference_train_v1.0.0.csv"
DEFAULT_CURRENT = "data/processed/train.csv"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Evidently AI profiling + drift detection",
    )
    parser.add_argument("--reference", default=DEFAULT_REFERENCE,
                        help=f"Reference CSV (default: {DEFAULT_REFERENCE})")
    parser.add_argument("--current", default=DEFAULT_CURRENT,
                        help=f"Current CSV (default: {DEFAULT_CURRENT})")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--no-fail-on-drift", action="store_true",
                        help="Always exit 0 even if drift is detected")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.reference):
        sys.exit(f"reference file not found: {args.reference}")
    if not os.path.exists(args.current):
        sys.exit(f"current file not found: {args.current}")

    reference_df = pd.read_csv(args.reference)
    current_df = pd.read_csv(args.current)

    print("Evidently AI report")
    print("=" * 50)
    print(f"Reference : {args.reference}  shape={reference_df.shape}")
    print(f"Current   : {args.current}  shape={current_df.shape}")
    print(f"Output    : {args.output_dir}")

    profile = build_data_profile(reference_df)
    profile_html, profile_json = save_report(
        profile, "profile", output_dir=args.output_dir,
    )
    print(f"Profile HTML : {profile_html}")
    print(f"Profile JSON : {profile_json}")

    drift = build_drift_report(reference_df, current_df)
    drift_html, drift_json = save_report(
        drift, "drift", output_dir=args.output_dir,
    )
    print(f"Drift HTML   : {drift_html}")
    print(f"Drift JSON   : {drift_json}")

    summary = extract_drift_summary(drift)
    summary_path = os.path.join(args.output_dir, "drift_summary.json")
    with open(summary_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"Summary      : {summary_path}")
    print("-" * 50)
    print(f"dataset_drift              : {summary['dataset_drift']}")
    print(f"number_of_columns          : {summary['number_of_columns']}")
    print(f"number_of_drifted_columns  : {summary['number_of_drifted_columns']}")
    print(f"share_of_drifted_columns   : {summary['share_of_drifted_columns']:.4f}")

    if summary["dataset_drift"] and not args.no_fail_on_drift:
        sys.exit("FAIL: dataset drift detected (use --no-fail-on-drift to override)")


if __name__ == "__main__":
    main()

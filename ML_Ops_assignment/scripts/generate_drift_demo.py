"""
generate_drift_demo.py

Produce two synthetic "current" datasets to demonstrate the drift
detection pipeline:

  data/demo/current_healthy.csv
      Same population as the training set: a bootstrap resample with a
      tiny amount of Gaussian jitter on numeric columns. Should NOT
      trigger dataset_drift.

  data/demo/current_drifted.csv
      A degraded production scenario: numeric columns shifted by 3*std,
      categorical columns rotated, and target prevalence flipped.
      Should trigger dataset_drift.

Run:
  python scripts/generate_drift_demo.py
  python scripts/generate_drift_demo.py --reference data/processed/train.csv \
                                        --output-dir data/demo --seed 42
"""

import argparse
import os

import numpy as np
import pandas as pd

DEFAULT_REFERENCE = "data/processed/train.csv"
DEFAULT_OUTPUT_DIR = "data/demo"

NUMERIC_COLS = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]
CATEGORICAL_COLS = ["cp", "restecg", "slope", "thal"]


def make_healthy(reference_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Bootstrap resample + tiny jitter -> same distribution as reference."""
    rng = np.random.default_rng(seed)
    n = len(reference_df)
    sampled = reference_df.sample(n=n, replace=True, random_state=seed).reset_index(drop=True)
    for col in NUMERIC_COLS:
        if col in sampled.columns:
            jitter = rng.normal(loc=0.0, scale=sampled[col].std() * 0.02, size=n)
            sampled[col] = sampled[col] + jitter
    return sampled


def make_drifted(reference_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Aggressively perturb numeric + categorical + target columns."""
    rng = np.random.default_rng(seed)
    drifted = reference_df.copy().reset_index(drop=True)
    n = len(drifted)
    for col in NUMERIC_COLS:
        if col in drifted.columns:
            shift = drifted[col].std() * 3.0
            noise = rng.normal(loc=0.0, scale=drifted[col].std() * 0.5, size=n)
            drifted[col] = drifted[col] + shift + noise
    for col in CATEGORICAL_COLS:
        if col in drifted.columns:
            mode = drifted[col].mode().iloc[0]
            filled = drifted[col].fillna(mode).astype(int)
            drifted[col] = (filled % 4) + 1
    if "target" in drifted.columns:
        flip_mask = rng.random(n) < 0.7
        drifted.loc[flip_mask, "target"] = 1 - drifted.loc[flip_mask, "target"]
    return drifted


def parse_args():
    parser = argparse.ArgumentParser(description="Generate demo current datasets for drift")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE,
                        help=f"Reference CSV (default: {DEFAULT_REFERENCE})")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.reference):
        raise SystemExit(f"reference file not found: {args.reference}")

    os.makedirs(args.output_dir, exist_ok=True)
    reference_df = pd.read_csv(args.reference)

    healthy = make_healthy(reference_df, args.seed)
    drifted = make_drifted(reference_df, args.seed)

    healthy_path = os.path.join(args.output_dir, "current_healthy.csv")
    drifted_path = os.path.join(args.output_dir, "current_drifted.csv")
    healthy.to_csv(healthy_path, index=False)
    drifted.to_csv(drifted_path, index=False)

    print("Drift demo datasets generated")
    print("=" * 50)
    print(f"Reference        : {args.reference}  shape={reference_df.shape}")
    print(f"Healthy current  : {healthy_path}  shape={healthy.shape}")
    print(f"Drifted current  : {drifted_path}  shape={drifted.shape}")
    print()
    print("Numeric column means (reference vs healthy vs drifted):")
    for col in NUMERIC_COLS:
        if col in reference_df.columns:
            print(f"  {col:>9}  ref={reference_df[col].mean():7.2f}  "
                  f"healthy={healthy[col].mean():7.2f}  "
                  f"drifted={drifted[col].mean():7.2f}")
    if "target" in reference_df.columns:
        print()
        print(f"Target prevalence  ref={reference_df['target'].mean():.3f}  "
              f"healthy={healthy['target'].mean():.3f}  "
              f"drifted={drifted['target'].mean():.3f}")


if __name__ == "__main__":
    main()

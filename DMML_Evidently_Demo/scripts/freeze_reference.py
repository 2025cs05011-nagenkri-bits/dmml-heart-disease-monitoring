"""
freeze_reference.py

Snapshot the current training set as the immutable "reference" dataset
for drift detection. The frozen snapshot represents the data
distribution the production model was trained on and is committed to
git so every subsequent CI run can compare incoming data against the
same baseline.

Output (default):
  data/reference/reference_train_<version>.csv
  data/reference/reference_train_<version>.metadata.json

The metadata captures: schema, row count, target prevalence, file
hash, source path, git commit (if available) and creation timestamp.
This makes the snapshot fully traceable.

Usage:
  python scripts/freeze_reference.py --version v1.0.0
  python scripts/freeze_reference.py --version v1.1.0 \
                                     --source data/processed/train.csv
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

import pandas as pd

DEFAULT_SOURCE = "data/processed/train.csv"
DEFAULT_OUTPUT_DIR = "data/reference"


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def build_metadata(version: str, source: str, snapshot_path: str) -> dict:
    df = pd.read_csv(snapshot_path)
    schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
    target_prevalence = (
        float(df["target"].mean()) if "target" in df.columns else None
    )
    return {
        "version": version,
        "source": source,
        "snapshot_path": snapshot_path,
        "created_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_commit(),
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "schema": schema,
        "target_column": "target" if "target" in df.columns else None,
        "target_prevalence": target_prevalence,
        "sha256": _file_sha256(snapshot_path),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Freeze a training-set snapshot for drift comparison",
    )
    parser.add_argument("--version", required=True,
                        help="Semver-style label, e.g. v1.0.0")
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                        help=f"Source CSV (default: {DEFAULT_SOURCE})")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite the snapshot if it already exists")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.source):
        sys.exit(f"source file not found: {args.source}")

    os.makedirs(args.output_dir, exist_ok=True)
    snapshot_name = f"reference_train_{args.version}.csv"
    snapshot_path = os.path.join(args.output_dir, snapshot_name)
    metadata_path = os.path.join(
        args.output_dir, f"reference_train_{args.version}.metadata.json",
    )

    if os.path.exists(snapshot_path) and not args.force:
        sys.exit(f"snapshot already exists: {snapshot_path}  (use --force to overwrite)")

    shutil.copyfile(args.source, snapshot_path)
    metadata = build_metadata(args.version, args.source, snapshot_path)
    with open(metadata_path, "w") as fh:
        json.dump(metadata, fh, indent=2)

    print("Reference snapshot frozen")
    print("=" * 50)
    print(f"Version       : {metadata['version']}")
    print(f"Source        : {metadata['source']}")
    print(f"Snapshot      : {snapshot_path}")
    print(f"Metadata      : {metadata_path}")
    print(f"Rows / cols   : {metadata['n_rows']} / {metadata['n_columns']}")
    print(f"Target prev.  : {metadata['target_prevalence']}")
    print(f"sha256        : {metadata['sha256']}")
    print(f"git commit    : {metadata['git_commit']}")


if __name__ == "__main__":
    main()

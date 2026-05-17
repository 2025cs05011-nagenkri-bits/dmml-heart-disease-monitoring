# Evidently / DMML Demo — Screenshot Capture Guide

Drop PNG screenshots into **this folder** with the **exact filenames** below.
The report generator (`scripts/generate_dmml_report.py`) embeds them in
order; missing files are silently skipped, so you can build the report
incrementally as you capture.

| #  | Filename                            | What to capture                                                                                       | Where in the report                |
| -- | ----------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 01 | `01_metadata_json.png`              | Open `data/reference/reference_train_v1.0.0.metadata.json` in the editor — show schema, SHA, prevalence. | §4 Frozen Reference Pattern        |
| 02 | `02_local_clean_run.png`            | Terminal: `python scripts/run_evidently.py` showing `dataset_drift: False`, `share=0.0000`.           | §6 Demonstration — Healthy Path    |
| 03 | `03_local_drifted_run.png`          | Terminal: same script vs `data/demo/current_drifted.csv` showing `FAIL: dataset drift detected` and `Exit code: 1`. | §6 Demonstration — Drifted Path    |
| 04 | `04_workflow_dispatch_dropdown.png` | GitHub Actions → CI → "Run workflow" dropdown open, **toggle checkbox visible** and ticked.           | §5 CI Gating                       |
| 05 | `05_runs_list_green_red.png`        | GitHub Actions runs list showing the green push run AND the red manual run side-by-side on same commit. | §6 Demonstration — Side-by-side    |
| 06 | `06_green_run_steps.png`            | Successful (green) run — full step list, real drift gate step expanded showing `dataset_drift: False`. | §6 Demonstration — Healthy Path    |
| 07 | `07_red_run_overview.png`           | Failed (red) manual run summary page — workflow status banner, "Triggered via workflow_dispatch".     | §6 Demonstration — Drifted Path    |
| 08 | `08_debug_inputs_step.png`          | Expanded "Show workflow inputs (debug)" step printing `demo_fail_on_drift = true`.                    | §5 CI Gating                       |
| 09 | `09_failed_step_log.png`            | Expanded "Drift gate FAILURE demo" step — log shows `FAIL: dataset drift detected` and exit code 1.   | §6 Demonstration — Drifted Path    |
| 10 | `10_artifacts_section.png`          | Bottom of the failed run page — Artifacts panel showing `evidently-reports-py3.9` still uploaded.     | §6 Demonstration — Artifacts       |
| 11 | `11_drift_html_overview.png`        | `drift.html` opened in browser — top section with `Dataset Drift = TRUE`, share-of-drifted-columns.   | §6 Demonstration — Visual Report   |
| 12 | `12_drift_html_per_column.png`      | `drift.html` scrolled to per-column drift — distribution overlays for one drifted column.             | §6 Demonstration — Visual Report   |
| 13 | `13_profile_html.png`               | `profile.html` opened in browser — DataQualityPreset summary stats / column distributions.            | §3 Evidently Engine                |
| 14 | `14_evidently_folder.png`           | File explorer / `ls` showing exactly 5 files in `reports/evidently/` (no timestamp accumulation).      | §3 Evidently Engine                |

## Tips

- Use **PNG** at native resolution. The generator scales to 14–16 cm wide.
- For terminal screenshots use a **light theme** with **font ≥ 14 pt** so
  the text is legible when scaled into a Word page.
- For browser screenshots crop to the relevant section — full-page
  captures of `drift.html` will be too tall and lose detail.
- The numeric prefix (`01_`, `02_`, …) controls embedding order if you
  later add `add_screenshots()` groups to the generator.

## How to (re)build the report

```bash
cd ML_Ops_assignment
source venv/bin/activate
pip install python-docx==1.1.2          # one-time, if not installed
python -m scripts.generate_dmml_report
open reports/DMML_Evidently_Report.docx
```

Re-run any time after adding new screenshots — the script is idempotent.

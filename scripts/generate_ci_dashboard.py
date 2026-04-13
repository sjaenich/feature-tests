
#!/usr/bin/env python3
"""
Generate a standalone CI evaluation dashboard from JSONL experiment logs.

Input format (one JSON object per line):
{
  "timestamp": "2026-04-11 18:39:43,483",
  "logger": "approach",
  "level": "INFO",
  "event": {
    "project": "dbus",
    "success": true,
    "precision": 1.0,
    "recall": 0.6666666666666666,
    "f1": 0.8,
    "approach": "filter"
  }
}

Optional event fields that improve the dashboard:
- commit_sha
- branch
- ci_run_id
- seed
- dataset_version
- runtime_sec
- tp, fp, fn

Outputs:
- summary.csv
- run_summary.json
- dashboard.html

Usage:
    python generate_ci_dashboard.py logs.jsonl --outdir ci_dashboard
    python generate_ci_dashboard.py logs.jsonl --outdir ci_dashboard --baseline-approach initial
    python generate_ci_dashboard.py logs.jsonl --outdir ci_dashboard --fail-on-f1-drop 0.02 --critical-projects dbus dropbear
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Path to JSONL log file")
    p.add_argument("--outdir", default="ci_dashboard", help="Output directory")
    p.add_argument(
        "--baseline-approach",
        default="initial",
        help="Approach used as within-project baseline for delta columns",
    )
    p.add_argument(
        "--fail-on-f1-drop",
        type=float,
        default=None,
        help="Fail if best macro F1 is lower than baseline approach macro F1 by more than this amount",
    )
    p.add_argument(
        "--critical-projects",
        nargs="*",
        default=[],
        help="Projects that should be highlighted in regression checks",
    )
    p.add_argument(
        "--critical-drop-threshold",
        type=float,
        default=0.05,
        help="Fail if any critical project drops by more than this threshold relative to the baseline approach",
    )
    return p.parse_args()


def load_jsonl(path: str | Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            event = obj.get("event", {})
            row = {
                "timestamp": obj.get("timestamp"),
                "logger": obj.get("logger"),
                "level": obj.get("level"),
                **event,
            }
            rows.append(row)

    if not rows:
        raise ValueError("No rows found in input JSONL.")

    df = pd.DataFrame(rows)
    required = {"project", "approach", "success", "precision", "recall", "f1"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["success"] = df["success"].astype(bool)
    for c in ["precision", "recall", "f1"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values(["timestamp", "project", "approach"]).reset_index(drop=True)
    df["run_index"] = df.groupby(["project", "approach"]).cumcount() + 1
    return df


def fmt_mean_std(mean: float, std: float, digits: int = 3) -> str:
    if pd.isna(std):
        return f"{mean:.{digits}f}±0.000"
    return f"{mean:.{digits}f}±{std:.{digits}f}"


def build_summary(df: pd.DataFrame, baseline_approach: str) -> pd.DataFrame:
    grouped = (
        df.groupby(["project", "approach"], dropna=False)
        .agg(
            runs=("f1", "size"),
            success_rate=("success", "mean"),
            precision_mean=("precision", "mean"),
            precision_std=("precision", "std"),
            recall_mean=("recall", "mean"),
            recall_std=("recall", "std"),
            f1_mean=("f1", "mean"),
            f1_std=("f1", "std"),
            first_seen=("timestamp", "min"),
            last_seen=("timestamp", "max"),
        )
        .reset_index()
    )

    baseline = (
        grouped[grouped["approach"] == baseline_approach][["project", "f1_mean"]]
        .rename(columns={"f1_mean": "baseline_f1_mean"})
    )
    grouped = grouped.merge(baseline, on="project", how="left")
    grouped["delta_f1_vs_baseline"] = grouped["f1_mean"] - grouped["baseline_f1_mean"]

    def status_of(delta: float) -> str:
        if pd.isna(delta):
            return "no-baseline"
        if delta > 1e-12:
            return "improve"
        if delta < -1e-12:
            return "regress"
        return "ok"

    grouped["status"] = grouped["delta_f1_vs_baseline"].apply(status_of)
    grouped["precision_avg_std"] = grouped.apply(
        lambda r: fmt_mean_std(r["precision_mean"], r["precision_std"]), axis=1
    )
    grouped["recall_avg_std"] = grouped.apply(
        lambda r: fmt_mean_std(r["recall_mean"], r["recall_std"]), axis=1
    )
    grouped["f1_avg_std"] = grouped.apply(
        lambda r: fmt_mean_std(r["f1_mean"], r["f1_std"]), axis=1
    )

    grouped = grouped.sort_values(["project", "approach"]).reset_index(drop=True)
    return grouped


def compute_global_metrics(df: pd.DataFrame, summary: pd.DataFrame) -> dict[str, Any]:
    macro_by_approach = (
        summary.groupby("approach")
        .agg(
            macro_precision=("precision_mean", "mean"),
            macro_recall=("recall_mean", "mean"),
            macro_f1=("f1_mean", "mean"),
            mean_success_rate=("success_rate", "mean"),
            mean_f1_std=("f1_std", "mean"),
            projects=("project", "nunique"),
        )
        .reset_index()
        .sort_values("macro_f1", ascending=False)
    )

    best_approach = None
    if not macro_by_approach.empty:
        best_approach = macro_by_approach.iloc[0]["approach"]

    # Win count per project: which approach has highest mean F1 on that project
    wins = (
        summary.sort_values(["project", "f1_mean", "approach"], ascending=[True, False, True])
        .groupby("project", as_index=False)
        .first()[["project", "approach", "f1_mean"]]
    )
    win_counts = wins["approach"].value_counts().to_dict()

    return {
        "macro_by_approach": macro_by_approach,
        "best_approach": best_approach,
        "win_counts": win_counts,
        "overall_success_rate": float(df["success"].mean()),
        "num_rows": int(len(df)),
        "num_projects": int(df["project"].nunique()),
        "num_approaches": int(df["approach"].nunique()),
    }


def regression_checks(
    summary: pd.DataFrame,
    global_metrics: dict[str, Any],
    baseline_approach: str,
    fail_on_f1_drop: float | None,
    critical_projects: list[str],
    critical_drop_threshold: float,
) -> dict[str, Any]:
    macro = global_metrics["macro_by_approach"]
    baseline_macro = macro.loc[macro["approach"] == baseline_approach, "macro_f1"]
    baseline_macro_f1 = float(baseline_macro.iloc[0]) if not baseline_macro.empty else None
    best_macro_f1 = float(macro["macro_f1"].max()) if not macro.empty else None

    checks: list[dict[str, Any]] = []

    if baseline_macro_f1 is not None and best_macro_f1 is not None:
        macro_delta = best_macro_f1 - baseline_macro_f1
        status = "pass"
        if fail_on_f1_drop is not None and macro_delta < -fail_on_f1_drop:
            status = "fail"
        checks.append(
            {
                "name": "macro_f1_vs_baseline",
                "status": status,
                "baseline_approach": baseline_approach,
                "baseline_macro_f1": baseline_macro_f1,
                "best_macro_f1": best_macro_f1,
                "delta": macro_delta,
                "threshold": fail_on_f1_drop,
            }
        )

    if critical_projects:
        crit_rows = summary[summary["project"].isin(critical_projects)].copy()
        if not crit_rows.empty:
            # Compare each project's best approach against its baseline
            per_project = (
                crit_rows.groupby("project")
                .agg(
                    best_f1=("f1_mean", "max"),
                    baseline_f1=("baseline_f1_mean", "first"),
                )
                .reset_index()
            )
            per_project["delta"] = per_project["best_f1"] - per_project["baseline_f1"]
            worst = per_project.sort_values("delta").head(1)
            if not worst.empty:
                delta = float(worst.iloc[0]["delta"])
                status = "pass" if delta >= -critical_drop_threshold else "fail"
                checks.append(
                    {
                        "name": "critical_projects_vs_baseline",
                        "status": status,
                        "worst_project": worst.iloc[0]["project"],
                        "worst_delta": delta,
                        "threshold": critical_drop_threshold,
                    }
                )

    final_status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
    return {"status": final_status, "checks": checks}


def build_html(
    df: pd.DataFrame,
    summary: pd.DataFrame,
    global_metrics: dict[str, Any],
    checks: dict[str, Any],
    baseline_approach: str,
) -> str:
    macro = global_metrics["macro_by_approach"].copy()

    # Trend table: mean metrics over timestamp and approach
    trend = (
        df.assign(ts_bucket=df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S"))
        .groupby(["ts_bucket", "approach"], dropna=False)
        .agg(
            precision=("precision", "mean"),
            recall=("recall", "mean"),
            f1=("f1", "mean"),
            runs=("f1", "size"),
        )
        .reset_index()
        .sort_values(["ts_bucket", "approach"])
    )

    # Heatmap-like pivot for F1
    pivot = summary.pivot(index="project", columns="approach", values="f1_mean")
    pivot_html = pivot.round(3).to_html(classes="table table-sm", border=0)

    # Main display table
    display = summary[
        [
            "project",
            "approach",
            "runs",
            "precision_avg_std",
            "recall_avg_std",
            "f1_avg_std",
            "success_rate",
            "delta_f1_vs_baseline",
            "status",
        ]
    ].copy()
    display["success_rate"] = (display["success_rate"] * 100).round(1).astype(str) + "%"
    display["delta_f1_vs_baseline"] = display["delta_f1_vs_baseline"].map(
        lambda x: "" if pd.isna(x) else f"{x:+.3f}"
    )

    regressions = summary.dropna(subset=["delta_f1_vs_baseline"]).sort_values("delta_f1_vs_baseline").head(10)
    improvements = summary.dropna(subset=["delta_f1_vs_baseline"]).sort_values("delta_f1_vs_baseline", ascending=False).head(10)

    def card(title: str, value: str, subtitle: str = "") -> str:
        return f"""
        <div class="card">
          <div class="card-title">{title}</div>
          <div class="card-value">{value}</div>
          <div class="card-subtitle">{subtitle}</div>
        </div>
        """

    best_approach = global_metrics["best_approach"] or "n/a"
    best_macro_f1 = "n/a"
    if not macro.empty:
        best_macro_f1 = f'{float(macro.iloc[0]["macro_f1"]):.3f}'

    cards = "\n".join(
        [
            card("Rows", str(global_metrics["num_rows"]), "log entries"),
            card("Projects", str(global_metrics["num_projects"]), "unique libraries"),
            card("Approaches", str(global_metrics["num_approaches"]), "unique methods"),
            card("Success rate", f'{global_metrics["overall_success_rate"] * 100:.1f}%', "across all runs"),
            card("Best macro F1", best_macro_f1, f"approach: {best_approach}"),
            card("CI status", checks["status"].upper(), f"baseline approach: {baseline_approach}"),
        ]
    )

    check_items = []
    for c in checks["checks"]:
        payload = json.dumps(c, indent=2)
        check_items.append(f"<pre>{payload}</pre>")
    checks_html = "\n".join(check_items) if check_items else "<p>No checks configured.</p>"

    def rows_for_table(frame: pd.DataFrame) -> str:
        return frame.to_html(classes="table", index=False, border=0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CI Evaluation Dashboard</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    margin: 24px;
    color: #222;
  }}
  h1, h2, h3 {{
    margin-top: 28px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .card {{
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 16px;
    background: #fafafa;
  }}
  .card-title {{
    font-size: 14px;
    color: #555;
    margin-bottom: 8px;
  }}
  .card-value {{
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 6px;
  }}
  .card-subtitle {{
    font-size: 13px;
    color: #666;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0 24px 0;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background: #f0f0f0;
  }}
  tr:nth-child(even) {{
    background: #fcfcfc;
  }}
  pre {{
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
    background: #fafafa;
    overflow-x: auto;
  }}
  .muted {{
    color: #666;
  }}
</style>
</head>
<body>
  <h1>CI Evaluation Dashboard</h1>
  <p class="muted">Generated from JSONL experiment logs. Baseline approach: <strong>{baseline_approach}</strong></p>

  <div class="grid">
    {cards}
  </div>

  <h2>Regression checks</h2>
  {checks_html}

  <h2>Macro metrics by approach</h2>
  {rows_for_table(macro.round(4))}

  <h2>Per-project summary</h2>
  {rows_for_table(display)}

  <h2>Worst regressions vs baseline</h2>
  {rows_for_table(regressions[["project", "approach", "f1_mean", "baseline_f1_mean", "delta_f1_vs_baseline", "f1_std"]].round(4))}

  <h2>Best improvements vs baseline</h2>
  {rows_for_table(improvements[["project", "approach", "f1_mean", "baseline_f1_mean", "delta_f1_vs_baseline", "f1_std"]].round(4))}

  <h2>F1 matrix</h2>
  {pivot_html}

  <h2>Trend data (for CI history pages)</h2>
  {rows_for_table(trend.round(4))}

  <h2>Win counts</h2>
  <pre>{json.dumps(global_metrics["win_counts"], indent=2)}</pre>
</body>
</html>
"""
    return html


def main() -> int:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_jsonl(args.input)
    summary = build_summary(df, args.baseline_approach)
    global_metrics = compute_global_metrics(df, summary)
    checks = regression_checks(
        summary=summary,
        global_metrics=global_metrics,
        baseline_approach=args.baseline_approach,
        fail_on_f1_drop=args.fail_on_f1_drop,
        critical_projects=args.critical_projects,
        critical_drop_threshold=args.critical_drop_threshold,
    )

    summary.to_csv(outdir / "summary.csv", index=False)

    run_summary = {
        "status": checks["status"],
        "best_approach": global_metrics["best_approach"],
        "num_rows": global_metrics["num_rows"],
        "num_projects": global_metrics["num_projects"],
        "num_approaches": global_metrics["num_approaches"],
        "overall_success_rate": global_metrics["overall_success_rate"],
        "macro_by_approach": global_metrics["macro_by_approach"].round(6).to_dict(orient="records"),
        "checks": checks["checks"],
    }
    with open(outdir / "run_summary.json", "w", encoding="utf-8") as f:
        json.dump(run_summary, f, indent=2)

    html = build_html(df, summary, global_metrics, checks, args.baseline_approach)
    with open(outdir / "dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote: {outdir / 'summary.csv'}")
    print(f"Wrote: {outdir / 'run_summary.json'}")
    print(f"Wrote: {outdir / 'dashboard.html'}")
    print(f"CI status: {checks['status'].upper()}")

    return 0 if checks["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

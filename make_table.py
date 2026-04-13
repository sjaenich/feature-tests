#!/usr/bin/env python3
import json
import os
import sys
import glob

PROJECT_ORDER = [
    "libcurl",
    "dbus",
    "dropbear",
    "expat",
    "libpcap",
    "nano",
    "ncurses",
    "pcre2",
    "xz",
    "sqlite",
    "libxml2",
]

FILE_SUFFIX = "_approach_history.json"


def fmt(x):
    if x is None:
        return "-"
    return f"{x:.2f}"


def extract_project_name(path):
    base = os.path.basename(path)
    if not base.endswith(FILE_SUFFIX):
        return None
    return base[:-len(FILE_SUFFIX)]


def load_entries(path):
    """
    Supports either:
    1. JSONL: one JSON object per line
    2. JSON array: [ {...}, {...}, ... ]
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    # Try full JSON first
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # Fall back to JSONL
    entries = []
    for lineno, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Skipping invalid JSON in {path}:{lineno}: {e}", file=sys.stderr)
    return entries


def parse_metrics(raw_entries, path):
    parsed = []
    for i, obj in enumerate(raw_entries, 1):
        event = obj.get("event", {})
        parsed.append({
            "approach": event.get("approach"),
            "precision": event.get("precision"),
            "recall": event.get("recall"),
            "f1": event.get("f1"),
            "success": event.get("success", True),
            "index": i,
        })
    return parsed


def build_project_rows(entries, project):
    """
    Interpret as:
      [initial(B1), filter(B1), initial(B2), filter(B2), ...]
    """
    if len(entries) % 2 != 0:
        print(
            f"Warning: {project} has an odd number of entries ({len(entries)}). "
            f"The last entry will be ignored.",
            file=sys.stderr,
        )

    rows = []
    for i in range(0, len(entries) - 1, 2):
        initial = entries[i]
        filtr = entries[i + 1]

        # Optional sanity check
        init_name = str(initial.get("approach", "")).lower()
        filt_name = str(filtr.get("approach", "")).lower()

        if "initial" not in init_name:
            print(
                f"Warning: {project} entry {i+1} does not look like an initial run "
                f"(approach={initial.get('approach')!r})",
                file=sys.stderr,
            )
        if "filter" not in filt_name:
            print(
                f"Warning: {project} entry {i+2} does not look like a filter run "
                f"(approach={filtr.get('approach')!r})",
                file=sys.stderr,
            )

        bin_idx = i // 2 + 1
        rows.append({
            "bin": f"B{bin_idx}",
            "initial": initial,
            "filter": filtr,
        })

    return rows


def build_latex_table(project_data):
    lines = []
    lines.append(r"\begin{table*}[t]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\begin{tabular}{llccc|ccc}")
    lines.append(r"\toprule")
    lines.append(r"Project & Bin & \multicolumn{3}{c}{Initial} & \multicolumn{3}{c}{Filter} \\")
    lines.append(r"& & Prec & Rec & F1 & Prec & Rec & F1 \\")
    lines.append(r"\midrule")
    lines.append("")

    ordered_projects = [p for p in PROJECT_ORDER if p in project_data]
    ordered_projects += sorted(set(project_data) - set(PROJECT_ORDER))

    first = True
    for project in ordered_projects:
        rows = project_data[project]
        if not rows:
            continue

        if not first:
            lines.append(r"\midrule")
        first = False

        lines.append(rf"\texttt{{{project}}}")
        for row in rows:
            init = row["initial"]
            filt = row["filter"]
            lines.append(
                f"& {row['bin']} "
                f"& {fmt(init['precision'])} & {fmt(init['recall'])} & {fmt(init['f1'])} "
                f"& {fmt(filt['precision'])} & {fmt(filt['recall'])} & {fmt(filt['f1'])} \\\\"
            )
        lines.append("")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\caption{Per-binary macro recovery results (3 binaries per project).}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    pattern = os.path.join(directory, f"*{FILE_SUFFIX}")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No files matching {pattern}", file=sys.stderr)
        sys.exit(1)

    project_data = {}

    for path in files:
        project = extract_project_name(path)
        if not project:
            continue

        raw_entries = load_entries(path)
        parsed_entries = parse_metrics(raw_entries, path)
        rows = build_project_rows(parsed_entries, project)
        project_data[project] = rows

    latex = build_latex_table(project_data)
    print(latex)


if __name__ == "__main__":
    main()

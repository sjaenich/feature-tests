#!/usr/bin/env python3
import json
import glob
import os
import sys

FILE_SUFFIX = "_string_metrics.json"

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
    "libssh2",
    "openssl",
    "rsync",
]


def load_entries(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    # First try normal JSON
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # Fallback: JSONL
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


def extract_project_name(path):
    base = os.path.basename(path)
    if not base.endswith(FILE_SUFFIX):
        return None
    return base[:-len(FILE_SUFFIX)]


def latex_escape(text):
    return (
        str(text)
        .replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def collect_project_data(directory):
    pattern = os.path.join(directory, f"*{FILE_SUFFIX}")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No files found matching {pattern}", file=sys.stderr)
        sys.exit(1)

    project_data = {}

    for path in files:
        project = extract_project_name(path)
        if not project:
            continue

        raw_entries = load_entries(path)
        rows = []

        for idx, obj in enumerate(raw_entries, 1):
            event = obj.get("event", {})

            rows.append({
                "bin": f"B{idx}",
                "binary_strings": event.get("binary_strings", "-"),
                "source_code_strings": event.get("source_code_strings", "-"),
                "negative_string_count": event.get("negative_string_count", "-"),
                "gt_macros": event.get("number of Macros in GT", "-"),
            })

        project_data[project] = rows

    return project_data


def build_latex_table(project_data):
    lines = []
    lines.append(r"\begin{table*}[t]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\begin{tabular}{llrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Project & Bin & Binary Strings & Source Strings & Negative Strings & GT Macros \\")
    lines.append(r"\midrule")

    ordered_projects = [p for p in PROJECT_ORDER if p in project_data]
    ordered_projects += sorted(set(project_data.keys()) - set(PROJECT_ORDER))

    first_project = True
    for project in ordered_projects:
        rows = project_data[project]
        if not rows:
            continue

        if not first_project:
            lines.append(r"\midrule")
        first_project = False

        lines.append(rf"\texttt{{{latex_escape(project)}}}")

        for row in rows:
            lines.append(
                f"& {row['bin']} "
                f"& {row['binary_strings']} "
                f"& {row['source_code_strings']} "
                f"& {row['negative_string_count']} "
                f"& {row['gt_macros']} \\\\"
            )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\caption{Per-binary string statistics and ground-truth macro counts.}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "string_metrics_table.tex"

    project_data = collect_project_data(directory)
    latex = build_latex_table(project_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex + "\n")

    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()

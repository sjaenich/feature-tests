#!/usr/bin/env bash
# Count macro-guarded strings and origins in FlagRecovery-style logs.
# Requires Bash and Python 3 (standard library only).
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Error: python3 is required.' >&2
    exit 1
fi

exec python3 - "$@" <<'PY'
import argparse
import ast
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


class LogError(Exception):
    pass


def literal(text, location):
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError) as exc:
        raise LogError(f"{location}: invalid Python literal: {exc}") from exc


def macro_names(condition, location):
    """Find Boolean macro references; return None when the log truncated the PC."""
    # Normalize C Boolean syntax for AST parsing. This is name extraction,
    # not evaluation: precedence changes cannot change the collected names.
    expression = condition.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", " not ", expression).strip()
    expression = re.sub(r"\bdefined\s+([A-Za-z_]\w*)", r"defined(\1)", expression)
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise LogError(f"{location}: unsupported presence condition {condition!r}") from exc
    operators = {"And", "Or", "Not", "Xor", "Implies", "If", "BoolVal", "defined"}
    allowed = (
        ast.Expression, ast.Name, ast.Load, ast.Constant,
        ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Invert, ast.UAdd, ast.USub,
        ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
        ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift,
    )
    function_nodes = set()
    truncated = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in operators:
                raise LogError(f"{location}: unsupported presence condition {condition!r}")
            function_nodes.add(id(node.func))
        elif not isinstance(node, allowed):
            raise LogError(f"{location}: unsupported presence condition {condition!r}")
        elif isinstance(node, ast.Constant):
            if node.value is Ellipsis:
                truncated = True
            elif not isinstance(node.value, (bool, int, float)):
                raise LogError(f"{location}: unsupported presence condition {condition!r}")
    if truncated:
        # Ellipsis is the pretty-printer's omitted expression, not a Boolean
        # constant. Neither its names nor its full structure can be recovered.
        return None
    names = set()

    def collect(node):
        # Counting convention requested by the user: comparison predicates
        # are accepted but do not contribute macro references. Keep separate
        # Boolean references in mixed conditions, e.g. And(FLAG, XML_GE == 1).
        if isinstance(node, ast.Compare):
            return
        if isinstance(node, ast.Name) and id(node) not in function_nodes:
            names.add(node.id)
        for child in ast.iter_child_nodes(node):
            collect(child)

    collect(tree)
    return names


def read_constraint(lines, start, prefix, limit, path):
    block = lines[start][len(prefix):]
    end = start
    while True:
        # The PC may itself contain ==. Locate the equality immediately
        # before InBinary instead of splitting at the first comparison.
        match = re.fullmatch(r'(.*?)==\s*InBinary\(".*",\s*(\d+)\)\s*', block, re.S)
        if match:
            return int(match[2]), " ".join(match[1].split()), end
        end += 1
        if end >= limit:
            raise LogError(f"{path}:{start + 1}: incomplete InBinary constraint")
        block += "\n" + lines[end]


def analyze(path, strict=False):
    lines = path.read_text(encoding="utf-8").splitlines()
    dumps = []
    for n, line in enumerate(lines):
        if line.startswith("IndexSet:"):
            entries = literal(line.split(":", 1)[1].strip(), f"{path}:{n + 1}")
            if not isinstance(entries, (list, tuple)):
                raise LogError(f"{path}:{n + 1}: IndexSet must be a list of pairs")
            index = {}
            for entry in entries:
                if (not isinstance(entry, (list, tuple)) or len(entry) != 2
                        or not isinstance(entry[0], str) or type(entry[1]) is not int
                        or entry[1] < 1):
                    raise LogError(f"{path}:{n + 1}: invalid IndexSet entry {entry!r}")
                text, origin = entry
                if origin in index:
                    raise LogError(f"{path}:{n + 1}: duplicate origin ID {origin}")
                index[origin] = text
            dumps.append((n, index))
    if not dumps:
        raise LogError(f"{path}: no IndexSet dump found")
    limit, index = dumps[0]
    if any(other != index for _, other in dumps[1:]):
        raise LogError(f"{path}: IndexSet changes between dumps; split the log into runs")

    # IDs come from IndexSet and explicit InBinary constraints, never from
    # counting log lines. Some runs allocate IDs without a corresponding row.
    records = {}
    constraints = {}
    normal_pcs = defaultdict(Counter)
    condition_names = {}
    normal = re.compile(
        r"String and PC SourceStringEntry\(content=(.*), "
        r"line_number=(\d+), macro=(True|False)\) (.*)"
    )
    n = 0
    while n < limit:
        line = lines[n]
        location = f"{path}:{n + 1}"
        if line.startswith("String and PC "):
            match = normal.fullmatch(line)
            if not match:
                raise LogError(f"{location}: unsupported SourceStringEntry format")
            text = literal(match[1], location)
            condition = match[4]
            while condition.count("(") > condition.count(")"):
                n += 1
                if n >= limit:
                    raise LogError(f"{location}: incomplete presence condition")
                condition += " " + lines[n].strip()
            condition = " ".join(condition.split())
            condition_names[condition] = macro_names(condition, location)
            normal_pcs[text][condition] += 1
        elif line.startswith(("resolved ", "Added to solver ", "Not added to solver ")):
            prefix = next(p for p in ("resolved ", "Added to solver ", "Not added to solver ")
                          if line.startswith(p))
            origin, condition, n = read_constraint(lines, n, prefix, limit, path)
            condition_names[condition] = macro_names(condition, location)
            resolved = prefix == "resolved "
            if origin in constraints and constraints[origin][:2] != (condition, resolved):
                raise LogError(f"{location}: conflicting constraints for ID {origin}")
            constraints[origin] = (condition, resolved, location)
        n += 1

    for origin, (condition, resolved, location) in constraints.items():
        if origin not in index:
            continue
        if not resolved:
            remaining = normal_pcs[index[origin]]
            if remaining[condition] < 1:
                raise LogError(f"{location}: solver condition or source text disagrees "
                               f"with IndexSet ID {origin}")
            remaining[condition] -= 1
        names = condition_names[condition]
        records[origin] = ("truncated presence condition (...)" if names is None else condition, names)

    grouped = defaultdict(list)
    for origin, text in index.items():
        grouped[text].append(origin)
    for text, origins in grouped.items():
        unmatched = [origin for origin in origins if origin not in records]
        if not unmatched:
            continue
        remaining = normal_pcs[text]
        if sum(remaining.values()) < len(unmatched):
            for origin in unmatched:
                records[origin] = ("missing presence conditions", None)
            continue
        if any(condition_names[pc] is None for pc, count in remaining.items() if count > 0):
            for origin in unmatched:
                records[origin] = ("truncated presence condition (...) among source candidates", None)
            continue
        candidates = {frozenset(condition_names[pc])
                      for pc, count in remaining.items() if count > 0}
        if len(candidates) != 1:
            for origin in unmatched:
                records[origin] = ("ambiguous macro conditions", None)
            continue
        # Matching by text is safe only when all remaining candidates have
        # the same macro classification and names. Never guess among them.
        names = next(iter(candidates))
        for origin in unmatched:
            records[origin] = (None, names)
    unknown_ids = sorted(origin for origin in index if records[origin][1] is None)
    if strict and unknown_ids:
        reasons = "; ".join(sorted({records[origin][0] for origin in unknown_ids}))
        raise LogError(f"{path}: {reasons} for IDs {unknown_ids}; "
                       "run without --strict to report them as unknown")
    result_rows = []
    for text, origins in sorted(grouped.items()):
        origins.sort()
        guarded = [origin for origin in origins if records[origin][1]]
        unknown = [origin for origin in origins if records[origin][1] is None]
        names = sorted({name for origin in origins for name in (records[origin][1] or ())})
        result_rows.append({
            "string_text": text,
            "origin_count": len(origins),
            "origin_ids": ";".join(map(str, origins)),
            "macro_guarded_origin_count": len(guarded),
            "macro_guarded_origin_ids": ";".join(map(str, guarded)),
            "macros": ";".join(names),
            "unguarded_origin_count": len(origins) - len(guarded) - len(unknown),
            "unknown_origin_count": len(unknown),
            "unknown_origin_ids": ";".join(map(str, unknown)),
            "unknown_reason": "; ".join(sorted({records[origin][0] for origin in unknown})),
        })
    return result_rows, len(index), len(dumps)


def report(path, rows, occurrences, dumps):
    guarded = [r for r in rows if r["macro_guarded_origin_count"]]
    guarded_occurrences = sum(r["macro_guarded_origin_count"] for r in rows)
    single = sum(r["origin_count"] == 1 for r in rows)
    guarded_single = sum(r["origin_count"] == 1 for r in guarded)
    mixed = sum(r["unguarded_origin_count"] > 0 for r in guarded)
    unknown = sum(r["unknown_origin_count"] for r in rows)
    unknown_texts = [r for r in rows if r["unknown_origin_count"]]
    percentage = 100 * guarded_occurrences / occurrences if occurrences else 0
    print(f"File: {path}")
    print(f"IndexSet dumps: {dumps} (counted once)")
    print(f"Source occurrences: {occurrences}")
    print(f"Distinct string texts: {len(rows)}")
    qualifier = " (confirmed)" if unknown else ""
    print(f"Macro-guarded occurrences{qualifier}: {guarded_occurrences} ({percentage:.2f}%)")
    print(f"Macro-guarded distinct strings{qualifier}: {len(guarded)}")
    print(f"Unguarded occurrences: {occurrences - guarded_occurrences - unknown}")
    print(f"Unknown occurrences: {unknown}")
    print("Counting rule: references inside comparisons (e.g. XML_GE == 1) are excluded.")
    if unknown:
        additional_texts = sum(not r["macro_guarded_origin_count"] for r in unknown_texts)
        print(f"Possible macro-guarded total: {guarded_occurrences}–{guarded_occurrences + unknown} "
              f"occurrences; {len(guarded)}–{len(guarded) + additional_texts} distinct strings")
    print()
    print(f"{'Distinct strings':<30} {'One origin':>12} {'Multiple origins':>18} {'Total':>8}")
    print(f"{'All indexed strings':<30} {single:>12} {len(rows)-single:>18} {len(rows):>8}")
    print(f"{'With a macro-guarded occurrence':<30} {guarded_single:>12} "
          f"{len(guarded)-guarded_single:>18} {len(guarded):>8}")
    print(f"Strings with both guarded and unguarded origins: {mixed}")
    if unknown:
        print("\nUnknown entries (not counted as guarded or unguarded):")
        for row in unknown_texts:
            print(f"  IDs {row['unknown_origin_ids']}: {row['string_text']!r} "
                  f"[{row['unknown_reason']}]")
        print("The guarded row above includes only strings with a confirmed guarded origin. "
              "Macro names inside string text are not treated as presence conditions.")


def main():
    parser = argparse.ArgumentParser(
        description="Count macro-guarded strings and origins in FlagRecovery-style logs.",
        epilog=("An origin is an IndexSet ID with exactly matching string text. "
                "A guarded occurrence has a symbolic macro outside comparisons in its presence condition; "
                "constant True/False conditions and macro expansion alone do not count. "
                "Comparisons such as XML_GE == 1 are accepted but their names are "
                "excluded from the count. And(FLAG, XML_GE == 1) counts only FLAG. "
                "Arithmetic/bitwise expressions and Boolean operators are supported "
                "and are never evaluated. "
                "All indexed origins count, regardless of the current build flags. "
                "Repeated identical IndexSets are counted once. IDs may have gaps. "
                "Explicit InBinary constraints identify guarded and resolved origins; "
                "other origins are matched by text only when macro classification "
                "is unambiguous. Missing, ambiguous, or truncated (...) conditions "
                "are reported as unknown; "
                "use --strict to fail instead. Macro names embedded inside string text "
                "are not presence-condition evidence. "
                "Log literals are parsed as data and never executed."),
    )
    parser.add_argument("--csv-dir", type=Path, help="also export one per-string CSV per log")
    parser.add_argument("--strict", action="store_true",
                        help="fail if any indexed origin cannot be classified")
    parser.add_argument("logs", nargs="+", type=Path, help="input log files")
    args = parser.parse_args()
    try:
        if args.csv_dir and len({p.name for p in args.logs}) != len(args.logs):
            raise LogError("CSV input basenames must be unique")
        results = [(path, *analyze(path, strict=args.strict)) for path in args.logs]
        if args.csv_dir:
            args.csv_dir.mkdir(parents=True, exist_ok=True)
        for i, (path, rows, occurrences, dumps) in enumerate(results):
            if i:
                print("\n" + "-" * 72 + "\n")
            report(path, rows, occurrences, dumps)
            if args.csv_dir:
                output = args.csv_dir / (path.name + ".strings.csv")
                # Exclusive creation prevents overwriting previous results.
                with output.open("x", encoding="utf-8", newline="") as stream:
                    fields = ["string_text", "origin_count", "origin_ids",
                              "macro_guarded_origin_count", "macro_guarded_origin_ids", "macros",
                              "unguarded_origin_count", "unknown_origin_count",
                              "unknown_origin_ids", "unknown_reason"]
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                print(f"CSV: {output}")
    except (LogError, OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


sys.exit(main())
PY


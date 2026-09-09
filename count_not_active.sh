#!/usr/bin/env bash
# Count each "Not active removed" list under its logged iteration.
# Requires Bash and Python 3; no third-party packages.
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
from pathlib import Path


ITERATION = re.compile(r'^\s*===\s*Iteration\s+(\d+)\s*===\s*$', re.I)
REMOVED = re.compile(r'^\s*Not active removed\b\s*:?\s*(.*)$', re.I)
FIELDS = ['file', 'section', 'iteration', 'list_number', 'log_line',
          'entries', 'unique_occurrences', 'distinct_strings', 'status']


class LogError(Exception):
    pass


def read_list(lines, start, path):
    """Parse Python list literals as data, including lists wrapped across lines."""
    text = REMOVED.match(lines[start])[1]
    end = start
    while True:
        try:
            value = ast.literal_eval(text)
            break
        except SyntaxError as exc:
            incomplete = not text.strip() or 'never closed' in exc.msg or 'unexpected EOF' in exc.msg
            if not incomplete or end + 1 >= len(lines):
                raise LogError(f'{path}:{start + 1}: malformed or truncated removed list') from exc
            end += 1
            if ITERATION.match(lines[end]) or REMOVED.match(lines[end]):
                raise LogError(f'{path}:{start + 1}: incomplete removed list before line {end + 1}')
            text += '\n' + lines[end]
        except (ValueError, TypeError) as exc:
            raise LogError(f'{path}:{start + 1}: removed list is not a data literal') from exc
    if not isinstance(value, list):
        raise LogError(f'{path}:{start + 1}: expected a list after "Not active removed"')
    entries = []
    for item in value:
        if isinstance(item, str):
            entries.append((item, None))
        elif (isinstance(item, (tuple, list)) and len(item) == 2
              and isinstance(item[0], str) and type(item[1]) is int):
            entries.append(tuple(item))
        else:
            raise LogError(f'{path}:{start + 1}: expected strings or (string, ID) pairs; got {item!r}')
    return entries, end


def analyze(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    sections = []
    current = None
    n = 0
    while n < len(lines):
        header = ITERATION.match(lines[n])
        if header:
            current = {'iteration': header[1], 'header_line': n + 1, 'lists': []}
            sections.append(current)
        elif REMOVED.match(lines[n]):
            if current is None:
                current = {'iteration': 'preamble', 'header_line': '', 'lists': []}
                sections.append(current)
            start = n
            entries, n = read_list(lines, n, path)
            current['lists'].append({
                'list_number': len(current['lists']) + 1,
                'log_line': start + 1,
                'entries': len(entries),
                'unique_occurrences': len(set(entries)),
                'distinct_strings': len({text for text, _ in entries}),
                'status': 'logged',
            })
        n += 1
    if not sections:
        raise LogError(f'{path}: no iteration headers or "Not active removed" lists found')
    rows = []
    for number, section in enumerate(sections, 1):
        records = section['lists'] or [{
            'list_number': '', 'log_line': '', 'entries': '',
            'unique_occurrences': '', 'distinct_strings': '', 'status': 'not logged',
        }]
        for record in records:
            rows.append(dict(file=str(path), section=number,
                             iteration=section['iteration'], **record))
    return rows


def report(path, rows):
    print(f'File: {path}')
    print(f"{'Section':>7} {'Iteration':>10} {'List':>5} {'Log line':>9} "
          f"{'Entries':>9} {'Unique occurrences':>20} {'Distinct texts':>16}  Status")
    for row in rows:
        def display(key):
            return str(row[key]) if row[key] != '' else '-'
        print(f"{display('section'):>7} {display('iteration'):>10} {display('list_number'):>5} "
              f"{display('log_line'):>9} {display('entries'):>9} "
              f"{display('unique_occurrences'):>20} {display('distinct_strings'):>16}  {row['status']}")


def main():
    parser = argparse.ArgumentParser(
        description='Count strings in each "Not active removed" list, grouped by iteration.',
        epilog=('Entries counts every list item, including repeated items. Unique occurrences '
                'deduplicates exact (string, ID) pairs; distinct texts ignores IDs. '
                'Lists containing plain strings are also supported. Each list is reported '
                'separately, since repeated lists may be snapshots of the same strings. '
                'An absent list is "not logged", whereas an explicit [] counts as zero. '
                'Section distinguishes repeated iteration numbers in concatenated runs. '
                'Only "Not active removed" lists count; log contents are never executed.'),
    )
    parser.add_argument('--csv', type=Path, help='also write the complete table to a new CSV file')
    parser.add_argument('logs', type=Path, nargs='+', help='one or more input log files')
    args = parser.parse_args()
    try:
        results = [(path, analyze(path)) for path in args.logs]
        if args.csv:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            with args.csv.open('x', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                for _, rows in results:
                    writer.writerows(rows)
        for i, (path, rows) in enumerate(results):
            if i:
                print()
            report(path, rows)
        print('\nEntries includes duplicates; unique occurrences deduplicates (text, ID); '
              'distinct texts deduplicates text. Lists are reported separately, not summed.')
        if args.csv:
            print(f'CSV: {args.csv}')
    except (LogError, OSError, UnicodeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


sys.exit(main())
PY


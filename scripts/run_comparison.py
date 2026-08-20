#!/usr/bin/env python3

from __future__ import annotations
from evaluation.binary_similarity import BinarySimilarityCalculator, BinarySimilarityResult
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------


ITERATION_RE = re.compile(
    r"_(?P<number>\d+)(?:\.[^.]+)?$"
)

# Examples:
#
# ("OPENSSL_NO_ARIA", "True")
# {"OPENSSL_NO_ARIA": true}
# OPENSSL_NO_ARIA=True
# CONFIG_FEATURE_X=0
MACRO_VALUE_RE = re.compile(
    r"""["']?
        (?P<macro>[A-Z][A-Z0-9_]+)
        ["']?
        \s*(?:,|:|=)\s*
        ["']?
        (?P<value>True|False|true|false|1|0)
        ["']?
    """,
    re.VERBOSE,
)

DEFINE_RE = re.compile(
    r"^\s*#\s*define\s+"
    r"(?P<macro>[A-Z][A-Z0-9_]+)\b"
)

UNDEF_RE = re.compile(
    r"^\s*(?:"
    r"#\s*undef|"
    r"/\*\s*#\s*undef"
    r")\s+"
    r"(?P<macro>[A-Z][A-Z0-9_]+)\b"
)

# Finds absolute paths containing "bundle".
BUNDLE_PATH_RE = re.compile(
    r"""(?P<path>
        /[^\s"'(),;:]*
        bundle
        [^\s"'(),;:]*
    )""",
    re.VERBOSE | re.IGNORECASE,
)


class LibraryLogComparison:
    def __init__(
        self,
        library_name: str,
        logs_root: str | Path,
        similarity_script: str | Path,
        *,
        binary_name: str | None = None,
        timeout: float | None = None,
        show_progress: bool = True,
    ):
        self.library_name = library_name
        self.binary_name = binary_name
        self.logs_root = Path(logs_root).expanduser().resolve()
        self.logs_directory = self._resolve_logs_directory()

        self.similarity_calculator = BinarySimilarityCalculator(
            similarity_script,
            timeout=timeout,
            show_progress=show_progress,
        )

    def run(self) -> BinarySimilarityResult:
        iterations = self.discover_iterations()

        first_iteration = min(iterations)
        last_iteration = max(iterations)

        print(f"Library:         {self.library_name}")
        print(f"Logs:            {self.logs_directory}")
        print(f"First iteration: {first_iteration}")
        print(f"Last iteration:  {last_iteration}")

        first_log = self.read_iteration(
            iterations[first_iteration]
        )
        last_log = self.read_iteration(
            iterations[last_iteration]
        )
        
        ground_truth_binary = self.find_ground_truth_binary(
            first_log
        )
        macro_config = self.parse_macro_config(last_log)

        print(f"Ground truth:    {ground_truth_binary}")
        print(f"Macros parsed:   {len(macro_config)}")

        for macro, value in sorted(macro_config):
            print(f"  {macro}={value}")



        raise KeyError
        print()
        print("Building candidate binary...")

        candidate_binary = self.build_candidate(macro_config)

        print(f"Candidate:       {candidate_binary}")
        print()
        print("Calculating similarity...")

        return self.similarity_calculator.calculate(
            ground_truth_binary,
            candidate_binary,
        )

    def _resolve_logs_directory(self) -> Path:
        candidates = [
            self.logs_root / self.library_name,
        ]

        if not self.library_name.startswith("lib"):
            candidates.append(
                self.logs_root / f"lib{self.library_name}"
            )

        for candidate in candidates:
            if candidate.is_dir():
                return candidate.resolve()

        raise NotADirectoryError(
            "Could not find the library log directory. Checked:\n"
            + "\n".join(f"  {path}" for path in candidates)
        )

    def discover_iterations(self) -> dict[int, list[Path]]:
        """
        Supports numbered files:

            library_0.log
            library_1.log
            library_2.log

        and numbered directories:

            library_0/
            library_1/
            library_2/
        """
        iterations: dict[int, list[Path]] = {}

        for path in self.logs_directory.iterdir():
            match = ITERATION_RE.search(path.name)

            if not match:
                continue

            number = int(match.group("number"))
            iterations.setdefault(number, []).append(path)

        if not iterations:
            raise RuntimeError(
                f"No numbered iterations found in "
                f"{self.logs_directory}. Expected names ending in "
                f"_0, _1, _2, etc."
            )

        return iterations

    @staticmethod
    def read_iteration(paths: list[Path]) -> str:
        parts: list[str] = []

        for path in sorted(paths):
            if path.is_file():
                parts.append(
                    path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                )
                continue

            if not path.is_dir():
                continue

            for child in sorted(path.rglob("*")):
                if not child.is_file():
                    continue

                try:
                    parts.append(
                        child.read_text(
                            encoding="utf-8",
                            errors="replace",
                        )
                    )
                except OSError:
                    continue

        if not parts:
            raise RuntimeError(
                "No readable log content found in:\n"
                + "\n".join(f"  {path}" for path in paths)
            )

        return "\n".join(parts)

    def find_ground_truth_binary(
        self,
        log_text: str,
    ) -> Path:
        candidates: list[Path] = []
        referenced_but_missing: list[Path] = []

        for match in BUNDLE_PATH_RE.finditer(log_text):
            raw_path = match.group("path").rstrip(".]}")
            path = Path(raw_path).expanduser()

            if path.is_file():
                resolved = path.resolve()

                if resolved not in candidates:
                    candidates.append(resolved)
            else:
                referenced_but_missing.append(path)

        if not candidates:
            message = (
                "No existing ground-truth binary with 'bundle' in its "
                "path was found in the first iteration."
            )

            if referenced_but_missing:
                message += "\nReferenced but missing paths:\n"
                message += "\n".join(
                    f"  {path}"
                    for path in referenced_but_missing[-10:]
                )

            raise FileNotFoundError(message)

        if self.binary_name:
            matching = [
                path
                for path in candidates
                if path.name == self.binary_name
                or self.binary_name in path.name
            ]

            if not matching:
                raise FileNotFoundError(
                    f"No ground-truth binary matching "
                    f"{self.binary_name!r} was found.\n"
                    f"Bundle candidates:\n"
                    + "\n".join(
                        f"  {path}" for path in candidates
                    )
                )

            candidates = matching

        else:
            # Prefer shared libraries when no filename was supplied.
            shared_libraries = [
                path
                for path in candidates
                if ".so" in path.name
                or path.suffix in {".dylib", ".dll"}
            ]

            if shared_libraries:
                candidates = shared_libraries

        # The last path normally belongs to the completed build.
        return candidates[-1]

    @staticmethod
    def parse_macro_config(
        log_text: str,
    ) -> set[tuple[str, str]]:
        """
        Return macros in the format:

            {
                ("SOME_MACRO", "True"),
                ("OTHER_MACRO", "False"),
            }

        The log is processed in order. If a macro appears multiple times,
        its last value wins.
        """
        macros: dict[str, bool] = {}

        for line in log_text.splitlines():
            # Handle multiple ("MACRO", "True") pairs on one line.
            for match in MACRO_VALUE_RE.finditer(line):
                raw_value = match.group("value").lower()

                macros[match.group("macro")] = (
                    raw_value in {"true", "1"}
                )

            undef_match = UNDEF_RE.match(line)

            if undef_match:
                macros[undef_match.group("macro")] = False
                continue

            define_match = DEFINE_RE.match(line)

            if define_match:
                macros[define_match.group("macro")] = True

        if not macros:
            raise RuntimeError(
                "No macro configuration could be parsed from the "
                "last iteration."
            )

        return {
            (
                macro,
                "True" if enabled else "False",
            )
            for macro, enabled in macros.items()
        }

    def build_candidate(
        self,
        macro_config: set[tuple[str, str]],
    ) -> Path:
        """
        Connect this method to the existing buildroot class.

        macro_config is a set of (macro_name, "True"|"False") tuples.
        """

        # Change this import only if your module has another location.
        from buildroot import buildroot

        builder = buildroot()

        # Change this call only if the existing build method has a different
        # signature.
        result = builder.build(
            library_name=self.library_name,
            macro_config=macro_config,
        )

        candidate = self._extract_result_path(result)

        if not candidate.is_file():
            raise FileNotFoundError(
                f"Buildroot did not produce the expected binary: "
                f"{candidate}"
            )

        return candidate.resolve()

    def _extract_result_path(self, result: Any) -> Path:
        """
        Accept a direct path or a small selection of common result formats.
        """
        if isinstance(result, (str, Path)):
            return Path(result).expanduser()

        if isinstance(result, dict):
            keys = [
                "binary",
                "binary_path",
                "output_binary",
                "output_path",
            ]

            for key in keys:
                value = result.get(key)

                if value:
                    return Path(value).expanduser()

        attributes = [
            "binary",
            "binary_path",
            "output_binary",
            "output_path",
        ]

        for attribute in attributes:
            value = getattr(result, attribute, None)

            if value:
                return Path(value).expanduser()

        raise TypeError(
            "The Buildroot build method did not return a binary path. "
            "Update build_candidate() to obtain the generated binary "
            "from your Buildroot implementation."
        )


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read a macro configuration from the final feature-test "
            "iteration, rebuild the library with Buildroot, and compare "
            "the result with the ground-truth binary from the first "
            "iteration."
        )
    )

    parser.add_argument(
        "library",
        help=(
            "Library/project name, for example libopenssl, libz, "
            "libcurl or libpng"
        ),
    )

    parser.add_argument(
        "--logs-root",
        default=(
            "/workspaces/RevEng/Tools/"
            "feature-tests/logs"
        ),
        help=(
            "Parent directory containing the library log directories"
        ),
    )

    parser.add_argument(
        "--binary-name",
        help=(
            "Expected binary filename. Use this when the project name "
            "and produced binary differ, for example "
            "'libopenssl --binary-name libcrypto.so'"
        ),
    )

    parser.add_argument(
        "--similarity-script",
        default="/home/vscode/binary_similarity.sh",
        help="Path to the Ghidra/BinDiff similarity shell script",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=3600,
        help="Maximum similarity-calculation time in seconds",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not stream Ghidra and BinDiff progress",
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    try:
        comparison = LibraryLogComparison(
            library_name=arguments.library,
            logs_root=arguments.logs_root,
            binary_name=arguments.binary_name,
            similarity_script=arguments.similarity_script,
            timeout=arguments.timeout,
            show_progress=not arguments.quiet,
        )

        result = comparison.run()

    except KeyboardInterrupt:
        print("\n[!] Interrupted", file=sys.stderr)
        return 130

    except Exception as error:
        print(f"[!] {error}", file=sys.stderr)
        return 1

    print()
    print("Comparison result")
    print("-----------------")
    print(f"Similarity: {result.similarity_percent:.4f}%")

    if result.confidence_percent is not None:
        print(f"Confidence: {result.confidence_percent:.4f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
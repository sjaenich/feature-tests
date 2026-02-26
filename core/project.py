from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Project:
    name: str
    source_dir: Path
    build_dir: Path
    include_dir: Path
    metadata: dict | None = None


@dataclass
class BuildResult:
    success: bool
    log_file: Path
    binary_paths: list[Path]


@dataclass
class RecoveryResult:
    flags: set[str]
    raw_output: Path
    runtime_sec: float


@dataclass
class ComparisonResult:
    precision: float
    recall: float
    f1: float
    tp: set[str]
    fp: set[str]
    fn: set[str]


@dataclass
class ExperimentResult:
    project: str
    build_success: bool
    config_found: bool
    precision: Optional[float]
    recall: Optional[float]
    f1: Optional[float]
    notes: str = ""
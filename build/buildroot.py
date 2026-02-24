import subprocess
import time
from pathlib import Path
from typing import List

from core.project import Project, BuildResult


class BuildrootBuildManager:
    """
    Build a single Buildroot package and extract produced binaries.
    """

    def __init__(
        self,
        buildroot_dir: Path,
        output_base: Path,
    ):
        self.buildroot_dir = buildroot_dir
        self.output_base = output_base

    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
    def _run(self, cmd, cwd, log_file: Path):
        with log_file.open("a") as f:
            return subprocess.run(
                cmd,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=self.timeout,
                check=False,
            )

    def _ensure_clean_build(self, pkg: str, log_file: Path)
        self._run(
            ["make", pkg + "-dirclean"],
            self.buildroot_dor,
            log_file,
        )

    def _ensure_defconfig(self, out_dir: Path, log_file: Path):
        if not (out_dir / ".config").exists():
            self._run(
                ["make",  "defconfig"],
                self.buildroot_dir,
                log_file,
            )

    def _discover_binaries(self, out_dir: Path) -> List[Path]:
        target_dir = out_dir / "target"
        if not target_dir.exists():
            return []

        bins = []
        for p in target_dir.rglob("*"):
            try:
                if p.is_file() and (p.stat().st_mode & 0o111):
                    bins.append(p)
            except FileNotFoundError:
                pass
        return bins

    # ---------------------------------------------------------
    # main API
    # ---------------------------------------------------------
    def build(self, project: Project) -> BuildResult:
        """
        project.name MUST be the Buildroot package name.
        """
        pkg = project.name

        out_dir = self.output_base / pkg
        out_dir.mkdir(parents=True, exist_ok=True)

        log_file = out_dir / "buildroot.log"

        start = time.time()

        # ensure config
        self._ensure_defconfig(out_dir, log_file)

        self._ensure_clean_build(pkg, log_file)

        # build the specific package
        cmd = [
            "make",
            f"{pkg}",
        ]

        res = self._run(cmd, self.buildroot_dir, log_file)
        success = res.returncode == 0

        # discover binaries
        binaries = self._discover_binaries(out_dir) if success else []

        duration = time.time() - start
        with log_file.open("a") as f:
            f.write(f"\n=== BUILD TIME: {duration:.2f}s ===\n")

        return BuildResult(success=success,
            log_file=log_file,
            binary_paths=binaries,
        )
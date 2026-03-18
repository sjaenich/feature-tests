import subprocess
import time
import os
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
        timeout: int = 300,
    ):
        self.buildroot_dir = buildroot_dir
        self.output_base = output_base
        self.timeout = timeout
    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
    def _run(self, cmd, cwd, log_file: Path, env=None):

        if env is None:
            env = os.environ.copy()


        with log_file.open("a") as f:
            return subprocess.run(
                cmd,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=self.timeout,
                check=False,
                env=env,
            )

    def _ensure_clean_build(self, pkg: str, log_file: Path):
        self._run(
            ["make", pkg + "-dirclean"],
            self.buildroot_dir,
            log_file,
        )

    def _ensure_defconfig(self, out_dir: Path, log_file: Path):
        if not (out_dir / ".config").exists():
            self._run(
                ["make",  "defconfig"],
                self.buildroot_dir,
                log_file,
            )

    def _discover_binaries(self, target_dir: Path, pkg: str) -> List[Path]:
        
        if not target_dir.exists():
            return []

        pkg_lower = pkg.lower()

        bins = []
        for p in target_dir.rglob("*"):
            try:
                if (
                    p.is_file()
                    and (p.stat().st_mode & 0o111)
                    and pkg_lower in p.name.lower() and ".so" in p.name.lower()
                ):
                    bins.append(p)
            except OSError:
                pass

        return bins

    # ---------------------------------------------------------
    # main API
    # ---------------------------------------------------------
    def build(self, project: Project) -> BuildResult:
        
        pkg = project.name
        
        out_dir = self.buildroot_dir / "output/build/"

        log_file = out_dir / Path("buildroot_" + pkg + ".log")
        
        start = time.time()

        # ensure config
        # self._ensure_defconfig(self.buildroot_dir, log_file)

        self._ensure_clean_build(pkg, log_file)

        # build the specific package
        cmd = [
            "make",
            f"{pkg}",
        ]

        env = os.environ.copy()

        env["MY_REAL_COMPILER"]=f"{"/workspaces/RevEng/buildroot-2025.02.4/output/host/bin/gcc-13.real"}"
        env["MY_EXTRA_FLAGS"]= project.metadata["cflags"]

        res = self._run(cmd, self.buildroot_dir, log_file, env)
        success = res.returncode == 0
        # success = True

        # matches = list(out_dir.glob(f"{pkg}-*"))
        # # matches = [Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ffmpeg-n6.1.2-27-ge16ff06adb/libavcodec")]
        # print("Output dir:", out_dir)
        # if not matches:
        #     raise FileNotFoundError(f"No build dir for {pkg}")
        # target_dir = matches[0]

        # self.output_base = target_dir

        # discover binaries
        # binaries = self._discover_binaries(target_dir, pkg) if success else []
        binaries = [project.metadata["binary"]]
        duration = time.time() - start
        with log_file.open("a") as f:
            f.write(f"\n=== BUILD TIME: {duration:.2f}s ===\n")

        return BuildResult(success=success,
            log_file=log_file,
            binary_paths=binaries,
        )
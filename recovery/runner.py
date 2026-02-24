import subprocess
import time
from pathlib import Path

from core.project import Project, RecoveryResult


class FlagRecoveryRunner:
    def __init__(self, tool_path: Path):
        self.tool_path = tool_path

    def run(self, project: Project, binary: Path) -> RecoveryResult:
        output_file = project.build_dir / "recovery.txt"
        start = time.time()

        res = subprocess.run(
            [str(self.tool_path), str(binary)],
            stdout=output_file.open("w"),
            stderr=subprocess.STDOUT,
            check=False,
        )

        runtime = time.time() - start

        # VERY naive parser — replace with your format
        flags: set[str] = set()
        if output_file.exists():
            for line in output_file.read_text().splitlines():
                flags.add(line.strip())

        return RecoveryResult(flags, output_file, runtime)

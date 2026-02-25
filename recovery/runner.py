import subprocess
import time
from pathlib import Path

import FlagRecovery
from core.project import Project, RecoveryResult


class FlagRecoveryRunner:
    def __init__(self, tool_path: Path):
        self.tool_path = tool_path

    def run(self, project: Project, binary: Path) -> RecoveryResult:
        output_file = project.build_dir / "recovery.txt"
        start = time.time()

        frr = FlagRecovery(project.files, binary, project.library_dir, project.config_h)
        macros = frr.run()

        runtime = time.time() - start       

        return RecoveryResult(macros, output_file, runtime)

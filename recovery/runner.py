import subprocess
import time
from pathlib import Path
from compiler_provenance.flag_recovery import FlagRecovery
from core.project import Project, RecoveryResult


class FlagRecoveryRunner:
    def __init__(self):
        pass

    def run(self, project: Project, binary: Path, config_h) -> RecoveryResult:
        output_file = project.build_dir / "recovery.txt"
        start = time.time()

        frr = FlagRecovery(project.source_dir, binary, config_h, project.name, project.include_dir)
        macros = frr.run()

        runtime = time.time() - start       

        return RecoveryResult(macros, output_file, runtime)

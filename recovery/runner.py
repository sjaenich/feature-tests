import subprocess
import time
from pathlib import Path
from compiler_provenance.flag_recovery import FlagRecovery
from core.project import Project, RecoveryResult


class FlagRecoveryRunner:
    def __init__(self):
        self.binary_strings = None
        self.source_code_strings = None
        

    def run(self, project: Project, binary: Path, config_h,stage) -> RecoveryResult:
        output_file = project.build_dir / "recovery.txt"
        start = time.time()
        extra_include = project.metadata["include"]
        frr = FlagRecovery(project.source_dir, binary, config_h, project.name, project.include_dir, extra_include)
        macros = frr.run(stage)

        self.binary_strings = frr.binary_strings.strings
        self.source_code_strings = frr.SourceStrings

        runtime = time.time() - start       

        return RecoveryResult(macros, output_file, runtime, frr)

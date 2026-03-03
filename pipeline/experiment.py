from core.project import ExperimentResult, Project
from pathlib import Path

class ExperimentRunner:
    def __init__(
        self,
        build_manager,
        locator,
        recovery,
        truth_extractor,
        comparator,
    ):
        self.build_manager = build_manager
        self.locator = locator
        self.recovery = recovery
        self.truth_extractor = truth_extractor
        self.comparator = comparator

    def run_project(self, project: Project) -> ExperimentResult:
        build_res = self.build_manager.build(project)
        if not build_res.success:
            return ExperimentResult(
                project.name, False, False, None, None, None, "build failed"
            )

        config_h = self.locator.locate(project, project.source_dir)
        config_h = Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ffmpeg-n6.1.2-27-ge16ff06adb/config.h")
        if not config_h:
            return ExperimentResult(
                project.name, True, False, None, None, None, "config.h not found"
            )

        gt = self.truth_extractor.extract(config_h)

        if not build_res.binary_paths:
            return ExperimentResult(
                project.name, True, True, None, None, None, "no binaries"
            )
        print(build_res.binary_paths)
        rec = self.recovery.run(project, build_res.binary_paths[0], config_h)
        print("Rec flags:", rec.flags)
        print("GT flags:", gt)
        cmp_res = self.comparator.compare(rec.flags, gt)

        return ExperimentResult(
            project.name,
            True,
            True,
            cmp_res.precision,
            cmp_res.recall,
            cmp_res.f1,
        )

from core.project import ExperimentResult, Project


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

        config_h = self.locator.locate(project)
        if not config_h:
            return ExperimentResult(
                project.name, True, False, None, None, None, "config.h not found"
            )

        gt = self.truth_extractor.extract(config_h)

        if not build_res.binary_paths:
            return ExperimentResult(
                project.name, True, True, None, None, None, "no binaries"
            )

        rec = self.recovery.run(project, build_res.binary_paths[0])
        cmp_res = self.comparator.compare(rec.flags, gt)

        return ExperimentResult(
            project.name,
            True,
            True,
            cmp_res.precision,
            cmp_res.recall,
            cmp_res.f1,
        )

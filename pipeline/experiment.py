from core.project import ExperimentResult, Project
from pathlib import Path
from truth.config_truth import GroundTruthExtractor
import logging
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
        build_res = self.build_manager.build(project, self.truth_extractor)
        if not build_res.success:
            return ExperimentResult(
                project.name, False, False, None, None, None, "build failed"
            )

        config_h = self.locator.locate(project, project.source_dir)
        config_h = project.metadata.get("config_h", None)
        if not config_h:
            return ExperimentResult(
                project.name, True, False, None, None, None, "config.h not found"
            )

        gt = self.truth_extractor.extract(config_h, project.name, project.source_dir)


        if not build_res.binary_paths:
            return ExperimentResult(
                project.name, True, True, None, None, None, "no binaries"
            )
        print(build_res.binary_paths)
        rec = self.recovery.run(project, build_res.binary_paths[0], config_h)
        print("Rec flags:", rec.flags)
        print("GT flags:", gt)
        cmp_res = self.comparator.compare(rec.flags, gt)


        with open(f"/workspaces/RevEng/{project.name}_stripped_strings.txt", "r") as f:
            unique_strings = list(set(line.strip() for line in f if line.strip()))
            string_count = len(unique_strings)

        logger =logging.getLogger("telemetry")
        logger.info({ 
            "project": project.name,
            "negative_string_count": string_count,
            "precision": cmp_res.precision,
            "recall": cmp_res.recall,
            "f1": cmp_res.f1,
        })


        approach_logger = logging.getLogger("approach")
        approach_logger.info({
            "project": project.name,
            "success": True,
            "precision": cmp_res.precision,
            "recall": cmp_res.recall,
            "f1": cmp_res.f1,
            "approach": rec.recovery_obj.approach,
        })

        return ExperimentResult(
            project.name,
            True,
            True,
            cmp_res.precision,
            cmp_res.recall,
            cmp_res.f1,
        )

from pathlib import Path

from core.project import Project
from build.buildroot import BuildrootBuildManager
from locate.config_locator import ConfigLocator
from recovery.runner import FlagRecoveryRunner
from truth.config_truth import GroundTruthExtractor
from evaluation.comparator import ResultComparator
from pipeline.experiment import ExperimentRunner


def main():
    project = Project(
        name="libcurl",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libcurl-7.71.1/lib"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libcurl-7.71.1/lib"),
    )
    print("*** Running experiment for project:", project.name, "***")
    runner = ExperimentRunner(
        build_manager=BuildrootBuildManager(project.build_dir, project.build_dir),
        locator=ConfigLocator(),
        recovery=FlagRecoveryRunner(Path("/path/to/your/tool")),
        truth_extractor=GroundTruthExtractor(),
        comparator=ResultComparator(),
    )
    print("Running experiment...")
    result = runner.run_project(project)
    print(result)


if __name__ == "__main__":
    main()

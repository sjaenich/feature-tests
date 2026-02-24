from pathlib import Path

from core.project import Project
from build.autotools import AutotoolsBuildManager
from locate.config_locator import ConfigLocator
from recovery.runner import FlagRecoveryRunner
from truth.config_truth import GroundTruthExtractor
from evaluation.comparator import ResultComparator
from pipeline.experiment import ExperimentRunner


def main():
    project = Project(
        name="demo",
        source_dir=Path("/path/to/project"),
        build_dir=Path("/tmp/ff_eval/demo"),
    )

    runner = ExperimentRunner(
        build_manager=AutotoolsBuildManager(),
        locator=ConfigLocator(),
        recovery=FlagRecoveryRunner(Path("/path/to/your/tool")),
        truth_extractor=GroundTruthExtractor(),
        comparator=ResultComparator(),
    )

    result = runner.run_project(project)
    print(result)


if __name__ == "__main__":
    main()

from pathlib import Path
from core.project import Project


class ConfigLocator:
    CANDIDATES = [
        "config.h",
        "configuration.h",
    ]

    def locate(self, project: Project) -> Path | None:
        # search build + source
        for root in [project.build_dir, project.source_dir]:
            for name in self.CANDIDATES:
                matches = list(root.rglob(name))
                if matches:
                    return matches[0]
        return None

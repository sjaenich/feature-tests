from pathlib import Path
from core.project import Project


class ConfigLocator:
    CANDIDATES = [
        "config.h",
        "configuration.h",
        "confdef.h",
    ]

    def locate(self, project: Project, output_base: Path | None = None) -> Path | None:
        patterns = set(self.CANDIDATES)

        # also allow *_<name> and *-<name>
        for name in self.CANDIDATES:
            patterns.add(f"*_{name}")
            patterns.add(f"*-{name}")
            patterns.add(f"*{name}")  # optional broad match

        for root in [output_base]:
            for pattern in patterns:
                for p in root.rglob(pattern):
                    if p.is_file():
                        print(f"Located config file: {p}")
                        return p
        return None
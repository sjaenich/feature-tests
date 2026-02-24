import re
from pathlib import Path


DEFINE_RE = re.compile(r"#define\s+(\w+)\s+1")


class GroundTruthExtractor:
    def extract(self, config_h: Path) -> set[str]:
        flags: set[str] = set()

        text = config_h.read_text(errors="ignore")
        for m in DEFINE_RE.finditer(text):
            flags.add(m.group(1))

        return flags

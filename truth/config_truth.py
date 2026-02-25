import re
from pathlib import Path


DEFINE_RE = re.compile(r"#define\s+(\w+)\s+1")


class GroundTruthExtractor:
    def extract(self, config_h: Path) -> set[(str,str)]:
        flags: set[(str,str)] = set()


        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+1\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        
        with open(str(config_h), "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # print(line)
                match = DEFINE_BOOL_RE.match(line)
                if match:
                    macro_name = match.group(1)
                    flags.add((macro_name,"True"))
                    
                m_undef = UNDEF_RE.match(line)        
                if m_undef:
                    macro_name = m_undef.group(1)
                    flags.add((macro_name,"False"))
                        
        return flags

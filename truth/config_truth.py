import random
import shutil
import subprocess
import re
from pathlib import Path


class GroundTruthExtractor:
    def extract(self, config_h: Path, name: str, src_dir: Path) -> set[(str,str)]:
        
        flags = self.modify_config_h(config_h, name)
        
        flags = self.remove_dead_macros(config_h, src_dir, flags)


        # flags.add(("SQLITE_ENABLE_FTS5", "True"))
        # flags.add(("SQLITE_ENABLE_JSON1", "True"))
        # flags.add(("SQLITE_ENABLE_FTS3", "True"))
        # flags.add(("SQLITE_ENABLE_STAT4", "True"))
        # flags.add(("SQLITE_ENABLE_RTREE", "True"))
        # flags.add(("SQLITE_ENABLE_JSON1", "True"))
        # flags.add(("SQLITE_ENABLE_GEOPOLY", "True"))
        # flags.add(("SQLITE_ENABLE_MATH_FUNCTIONS", "True"))
        # flags.add(("SQLITE_ENABLE_FTS4", "False"))
        # flags.add(("SQLITE_ENABLE_SESSION", "False"))
        # flags.add(("SQLITE_ENABLE_MEMSYS3", "False"))
        # flags.add(("SQLITE_ENABLE_MEMSYS5", "False"))





    
        # flags = self.get_llm_groundtruth()

        
        return flags


    # def _extract_macros(self, config_h: Path) -> set[(str,str)]:
    #     flags: set[(str,str)] = set()


    #     DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
    #     UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        
    #     with open(str(config_h), "r", encoding="utf-8", errors="ignore") as f:
    #         for line in f:
    #             # print(line)
    #             match = DEFINE_BOOL_RE.match(line)
    #             if match:
    #                 macro_name = match.group(1)
    #                 flags.add((macro_name,"True"))
                    
    #             m_undef = UNDEF_RE.match(line)        
    #             if m_undef:
    #                 macro_name = m_undef.group(1)
    #                 flags.add((macro_name,"False"))
                        
    #     return flags

    def modify_config_h(self, config_h, name: str) -> set[(str,str)]:
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = "/workspaces/RevEng/header/other_defines/other_defines" + name + ".h"
        flags = set()    
        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
            open(out_path, "w", encoding="utf-8") as out:
            out.write("/* Auto-extracted non-boolean defines */\n\n")
            for line in f:
                print(line.rstrip())
                handled = False
                match = DEFINE_BOOL_RE.match(line)
                if match:
                    macro_name = match.group(1)
                    flags.add((macro_name,"True"))
                    handled = True
                m_undef = UNDEF_RE.match(line)
                if m_undef:
                    macro_name = m_undef.group(1)                    
                    handled = True
                    flags.add((macro_name,"False"))
                if not handled:
                    m_other = DEFINE_OTHER_RE.match(line)
                    if m_other:
                        out.write(line)
            
        destination = "/workspaces/RevEng/header/libraries/" + name + ".h"
        shutil.move(path, destination)   

        return flags



    def remove_dead_macros(self, config_h: Path, src_dir: Path, macros) -> set[str]:
        
        unused = []

        for (macro, _) in macros:
            
            try:
                res = subprocess.check_output([
                    "grep", "-Rqw",
                    "--include=*.c",
                    "--include=*.h",
                    "--include=*.cpp",
                    "--include=*.hpp",
                    "--include=*.cc",
                    "--exclude=config.h",
                    macro,
                    src_dir
                ])
                
            except subprocess.CalledProcessError:
                unused.append(macro)
                print("Macro %s is unused." % macro)
        new_macros = set()
        for m in macros:
            if m[0] not in unused:
                new_macros.add(m)   

        return new_macros        




        # macros we want to experiment with
    FEATURE_MACROS = {
        "SQLITE_ENABLE_FTS3": [0, 1],
        "SQLITE_ENABLE_FTS4": [0, 1],
        "SQLITE_ENABLE_FTS5": [0, 1],
        "SQLITE_ENABLE_RTREE": [0, 1],
        "SQLITE_ENABLE_JSON1": [0, 1],
        "SQLITE_ENABLE_SESSION": [0, 1],
        "SQLITE_ENABLE_GEOPOLY": [0, 1],
        "SQLITE_ENABLE_UPDATE_DELETE_LIMIT": [0, 1],
        "SQLITE_ENABLE_MEMSYS3": [0, 1],
        "SQLITE_ENABLE_MEMSYS5": [0, 1],
        "SQLITE_ENABLE_MATH_FUNCTIONS": [0, 1],
    }


    def generate_random_config():
        """Random configuration of macros"""
        return {m: random.choice(v) for m, v in FEATURE_MACROS.items()}


    def write_config_header(config):
        """Write sqlite_config.h"""
        BUILD_DIR.mkdir(exist_ok=True)

        with open(CONFIG_HEADER, "w") as f:
            f.write("#ifndef SQLITE_CONFIG_H\n#define SQLITE_CONFIG_H\n\n")
            for macro, val in config.items():
                f.write(f"#define {macro} {val}\n")
            f.write("\n#endif\n")

        
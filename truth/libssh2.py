from random import random
from sys import flags
import random

from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path


class Libssh2GroundTruth(GroundTruthExtractor):
    def __init__(self):
        self.flags = set()
        self.flags.add(("LIBSSH2_HAVE_ZLIB", "True"))
        self.flags.add(("LIBSSH2_OPENSSL", "True"))
        self.flags.add(("LIBSSH2_LIBGCRYPT", "False"))
        self.flags.add(("LIBSSH2_MBEDTLS", "False"))
        self.flags.add(("LIBSSH2_WINCNG", "False"))


    def mix(self):
        
        flags = set_to_dict(self.flags)
         # Randomize ZLIB independently
        flags["LIBSSH2_HAVE_ZLIB"] = random.choice([True, False])

         # Choose exactly one crypto backend
        backends = [
            "LIBSSH2_OPENSSL",
            "LIBSSH2_LIBGCRYPT",
            "LIBSSH2_MBEDTLS",
            "LIBSSH2_WINCNG",
        ]

        chosen = random.choice(backends)

        for b in backends:
            flags[b] = (b == chosen)

        self.flags = dict_to_set(flags)

    def extract(self, config_h, name, src_dir):
        
        flags = set()

        # Common libssh2 config macros (boolean-style)
        print("Adding known libssh2 macros to ground truth")
        flags.update(self.flags)
        
     
        # Remove unused macros based on source usage
        flags = self.remove_dead_macros(src_dir, flags)
        print("Remaining macros after removing unused ones:", flags)
        only_flags = {flag for (flag, _) in flags}
        print("Only flag names:", only_flags)
        flags = self.modify_config_h(config_h, name, only_flags)
        print("Final set of macros after modifying config.h:", flags)
        return flags








    def modify_config_h(self, config_h, name: str, flags: set[str]):
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*#undef\s+([A-Z0-9_]+)\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        updated_flags = set()
        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:

            out.write("/* Auto-extracted non-boolean defines */\n\n")

            for line in f:
                handled = False

                match = DEFINE_BOOL_RE.match(line)
                print("DEF MATCH", line, match)
                if match:
                    macro_name = match.group(1)
                    if macro_name in flags:
                        updated_flags.add((macro_name, "True"))
                        dest.write(line)
                        handled = True

                m_undef = UNDEF_RE.match(line)
                print("UNDEF RE MATCH:", line, m_undef)
                if m_undef:
                    macro_name = m_undef.group(1)
                    print("MACRO NAME", macro_name)
                    if macro_name in flags:
                        updated_flags.add((macro_name, "False"))
                        dest.write(line)
                        handled = True

                if not handled:
                    m_other = DEFINE_OTHER_RE.match(line)
                    if m_other:
                        out.write(line)

        shutil.move(path, f"/workspaces/RevEng/header/libraries/{name}.old.h")

        return updated_flags


    def remove_dead_macros(self, src_dir: Path, macros):
        unused = []

        for (macro, _) in macros:
            try:
                subprocess.check_output([
                    "grep", "-Rqw",
                    "--include=*.c",
                    "--include=*.h",
                    "--include=*.cpp",
                    "--include=*.hpp",
                    "--include=*.cc",
                    "--exclude=libssh2_config.h",
                    macro,
                    str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)
                print(f"Macro {macro} is unused.")

        return {m for m in macros if m[0] not in unused}

# LIBSSH2_LIBGCRYPT
# LIBSSH2_MBEDTLS
# LIBSSH2_WINCNG
# LIBSSH2_THREADING
# LIBSSH2DEBUG
# LIBSSH2_HAVE_ZLIB
# )
def dict_to_set(flags_dict):
    return {(k, str(v)) for k, v in flags_dict.items()}

def set_to_dict(flags_set):
    return {k: (v == "True") for k, v in flags_set}
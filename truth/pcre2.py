from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class Pcre2GroundTruth(GroundTruthExtractor):

    def __init__(self):
          # --- PCRE2 10.44 Configure-Controllable Flags ---
        self.flags = set()
        # JIT Support (--enable-jit)
        # This is a major performance flag that adds an entire compiler backend.
        self.flags.add(("SUPPORT_JIT", "False"))
        
        # Library Bit-Widths (--enable-pcre2-8, --enable-pcre2-16, --enable-pcre2-32)
        self.flags.add(("SUPPORT_PCRE2_8", "True"))
        self.flags.add(("SUPPORT_PCRE2_16", "False"))
        self.flags.add(("SUPPORT_PCRE2_32", "False"))
        
        # Unicode Support (--enable-unicode)
        # If disabled, PCRE2 only handles ASCII/EBCDIC.
        self.flags.add(("SUPPORT_UNICODE", "True"))
        
        # Security & Recursion Limits (--enable-stack-for-recursion)
        self.flags.add(("PCRE2_DEBUG", "False"))
        
        # Feature Extensions
        # --enable-pcre2grep-libz, --enable-pcre2grep-libbz2
        self.flags.add(("SUPPORT_LIBZ", "False"))
        self.flags.add(("SUPPORT_LIBBZ2", "False"))
        self.flags.add(("SUPPORT_LIBREADLINE", "False"))
        self.flags.add(("SUPPORT_LIBEDIT", "False"))
        # Character Tables (--enable-ebcdic)
        self.flags.add(("EBCDIC", "False"))
        self.flags.add(("EBCDIC_NL25", "False"))
        self.flags.add(("SUPPORT_VALGRIND","False"))


    def extract(self, config_h, name, src_dir):
        flags = self.flags  

        # Strip out macros that aren't actually present in the source files
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        flags = self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        # Matches non-boolean defines like PCRE2_MAJOR or heap limit values
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* PCRE2 10.44 - User-Controllable Feature Flags */\n\n")
            
            for line in f:
                handled = False
                
                match = DEFINE_BOOL_RE.match(line)
                if match:
                    macro_name = match.group(1)
                    if macro_name in flags:
                        updated_flags.add((macro_name, "True"))
                        dest.write(line)
                        handled = True

                m_undef = UNDEF_RE.match(line)
                if m_undef:
                    macro_name = m_undef.group(1)
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

    def remove_dead_macros(self, src_dir: Path, macros) -> set:
        unused = []
        for (macro, _) in macros:
            try:
                # PCRE2 is C only
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class NanoGroundTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()
        # --- GNU nano Configure-Controllable Flags ---
        
        # Feature Stripping (--enable-tiny)
        # This is the "Master Flag" that disables almost everything else below.
        self.flags.add(("NANO_TINY", "True"))
        
        # High-Level Features
        self.flags.add(("ENABLE_NANORC", "False"))      # --disable-nanorc
        self.flags.add(("ENABLE_COLOR", "False"))       # --disable-color (Syntax highlighting)
        self.flags.add(("ENABLE_SPELLER", "False"))     # --disable-speller
        self.flags.add(("ENABLE_HELP", "False"))        # --disable-help
        self.flags.add(("ENABLE_JUSTIFY", "False"))     # --disable-justify
        self.flags.add(("ENABLE_HISTORIES", "False"))   # --disable-histories (Search/position history)
        self.flags.add(("ENABLE_TABCOMP", "False"))     # --disable-tabcomp
        self.flags.add(("ENABLE_WRAPPING", "False"))    # --disable-wrapping
        self.flags.add(("ENABLE_BROWSER", "False"))     # --disable-browser (File browser)
        self.flags.add(("ENABLE_NLS","False"))
        self.flags.add(("ENABLE_WORDCOMPLETION","False"))
        # Input/Output & Encoding
        self.flags.add(("ENABLE_UTF8", "False"))        # --disable-utf8
        self.flags.add(("ENABLE_MULTIBUFFER", "False")) # --disable-multibuffer (Open multiple files)
        self.flags.add(("ENABLE_LINENUMBERS", "False")) # --disable-linenumbers
        self.flags.add(("ENABLE_MOUSE", "False"))       # --disable-mouse
        
        # Operating System / Environment
        self.flags.add(("HAVE_LIBMAGIC", "False"))      # --with-libmagic (For file type detection)
        # self.flags.add(("HAVE_ZLIB_H", "False"))        # --enable-zlib
        
        # Security/Logic
        self.flags.add(("ENABLE_OPERATINGDIR", "False")) # --enable-operatingdir=DIR

    def extract(self, config_h, name, src_dir):
        flags = self.flags
 

        # Filter out macros not used in the source code
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+(ENABLE_[A-Z_]+|[A-Z_][A-Z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* GNU nano - User-Controllable Feature Flags */\n\n")
            
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
                # Nano is pure C
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
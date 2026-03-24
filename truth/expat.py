from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class ExpatGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        flags = set()
        
        # --- Expat 2.7.1 Configure-Controllable Flags ---
        
        # Encoding Support (--the most fundamental choice)
        # If XML_UNICODE is defined, Expat uses UTF-16 internally (2-byte chars).
        # Otherwise, it uses UTF-8 (1-byte chars).
    
        
        # Feature Toggles (--disable-dtd, --disable-ns)
        flags.add(("XML_DTD", "True"))            # Support for Data Type Definitions
        flags.add(("XML_NS", "True"))      
        flags.add(("XML_GE", "True"))       # Support for XML Namespaces
        
        # Security & Entropy (--with-getrandom, --with-sys-getrandom)
        # These control how Expat seeds its hash salt to prevent HashDoS.
        flags.add(("XML_DEV_URANDOM", "True"))
        flags.add(("HAVE_GETRANDOM", "True"))
        flags.add(("HAVE_SYSCALL_GETRANDOM", "True"))
        flags.add(("HAVE_ARC4RANDOM_BUF", "True"))
        flags.add(("HAVE_ARC4RANDOM", "False"))
        
        # Memory & Context (--with-context-bytes)
        # Determines how much prefix context is kept for error reporting.
        
        flags.add(("XML_ATTR_INFO", "False"))     # Track byte offsets for attributes

        # Filter out macros not used in the actual source code
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        # Expat uses standard #define MACRO 1/0 or /* #undef MACRO */
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        # Catch versioning and numeric defines (like XML_CONTEXT_BYTES)
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+(XML_[A-Z_]+|[A-Z_][A-Z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* Expat 2.7.1 - User-Controllable Feature Flags */\n\n")
            
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
                # Expat is pure C
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
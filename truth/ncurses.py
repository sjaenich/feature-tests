from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class NcursesGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        flags = set()
        
        # --- ncurses 6.4 Configure-Controllable Flags ---
        
        # Wide Character Support (--enable-widec)
        # This is the most critical flag; it changes 'ncurses' to 'ncursesw'
        flags.add(("USE_WIDEC_SUPPORT", "True"))
        
        # Threading Support (--with-pthread / --enable-reentrant)
        flags.add(("USE_REENTRANT", "True"))
        flags.add(("HAVE_LIBPTHREAD", "True"))
        
        # Terminal Database Options (--with-terminfo-dirs / --enable-termcap)
        flags.add(("USE_TERMCAP", "False"))
        flags.add(("USE_GETCAP", "False"))
        flags.add(("HAVE_TERMINFO_CURSES_H", "True"))
        
        # Extension Support (--disable-ext-funcs / --disable-ext-colors)
        # 256-color support and extended mouse functions
        flags.add(("NCURSES_EXT_FUNCS", "True"))
        flags.add(("NCURSES_EXT_COLORS", "True"))
        flags.add(("NCURSES_MOUSE_VERSION", "2")) # Usually an integer, but often checked
        
        # Trace and Debugging (--with-trace)
        flags.add(("USE_TRACE", "False"))
        
        # Mouse and Screen support
        flags.add(("NCURSES_EXT_PUTWIN", "True"))
        flags.add(("NCURSES_NO_PADDING", "False"))
        
        # Fallback support (--enable-fallback-archs)
        flags.add(("HAVE_FALLBACKS", "False"))

        # Clean up based on source usage
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        # ncurses config.h can be quite messy with many commented sections
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+(NCURSES_[A-Za-z_][A-Za-z0-9_]*|[A-Z_][A-Z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* ncurses 6.4 - Feature Configuration Flags */\n\n")
            
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
                # ncurses is pure C
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
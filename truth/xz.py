from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class LiblzmaFeatureTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()
              # --- liblzma / XZ Utils Configure-Controllable Flags ---
        
        # Threading Support (--enable-threads)
        self.flags.add(("MYTHREAD_POSIX", "True"))
        self.flags.add(("MYTHREAD_WIN95", "False"))
        self.flags.add(("MYTHREAD_VISTA", "False"))
        
        # Integrity Checks (--enable-checks=...)
        # These are usually all enabled, but can be manually toggled.
        self.flags.add(("HAVE_CHECK_CRC32", "True"))
        self.flags.add(("HAVE_CHECK_CRC64", "True"))
        self.flags.add(("HAVE_CHECK_SHA256", "True"))
        
    
        
        # Match Finders (--enable-match-finders=...)
        # hc3, hc4, bt2, bt3, bt4 are the standard set.
        self.flags.add(("HAVE_MF_HC3", "True"))
        self.flags.add(("HAVE_MF_HC4", "True"))
        self.flags.add(("HAVE_MF_BT2", "True"))
        self.flags.add(("HAVE_MF_BT3", "True"))
        self.flags.add(("HAVE_MF_BT4", "True"))
        
        # Encoders/Decoders (--enable-encoders, --enable-decoders)
        # These are the big ones for reducing binary size.
        self.flags.add(("HAVE_DECODERS", "True"))
        self.flags.add(("HAVE_ENCODERS","True"))
        self.flags.add(("HAVE_ENCODER_LZMA1", "True"))
        self.flags.add(("HAVE_ENCODER_LZMA2", "True"))
        self.flags.add(("HAVE_DECODER_LZMA1", "True"))
        self.flags.add(("HAVE_DECODER_LZMA2", "True"))
        archs = ["X86", "ARM", "ARM64", "ARMTHUMB", "POWERPC", "IA64", "SPARC", "RISCV"]
        for arch in archs:
            self.flags.add((f"HAVE_ENCODER_{arch}", "True"))
            self.flags.add((f"HAVE_DECODER_{arch}", "True"))

        # Add core filters and LZMA
        for tech in ["LZMA1", "LZMA2", "DELTA"]:
            self.flags.add((f"HAVE_ENCODER_{tech}", "True"))
            self.flags.add((f"HAVE_DECODER_{tech}", "True"))
        
        # Small-footprint mode (--enable-small)
        self.flags.add(("HAVE_SMALL", "False"))


    def extract(self, config_h, name, src_dir):
        flags = self.flags
        
  

        # Filter based on actual source presence
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        flags = self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* liblzma - User-Controllable Feature Flags */\n\n")
            
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
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
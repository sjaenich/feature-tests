from sys import flags

from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
import random
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



    import random

    def mix(self):
        # Convert set of tuples back to a working dictionary
        flags = {k: v == "True" for k, v in self.flags}
        
        # 1. CORE SELECTION: Bit-widths
        # PCRE2 must have at least one of 8, 16, or 32-bit enabled.
        # We'll pick a random combination but ensure it's not all False.
        bit_widths = ["SUPPORT_PCRE2_8", "SUPPORT_PCRE2_16", "SUPPORT_PCRE2_32"]
        for bw in bit_widths:
            flags[bw] = random.choice([True, False])
        
        if not any(flags[bw] for bw in bit_widths):
            # Fallback: force 8-bit if the dice rolled all False
            flags["SUPPORT_PCRE2_8"] = True

        # 2. DEPENDENCY: JIT Support
        # JIT can only be True if at least one bit-width is enabled (guaranteed above).
        # However, JIT is hardware-dependent.
        flags["SUPPORT_JIT"] = random.choice([True, False])

        # 3. DEPENDENCY: Unicode & Unicode Properties
        # SUPPORT_UNICODE_PROPERTIES requires SUPPORT_UNICODE to be True.
        # flags["SUPPORT_UNICODE"] = random.choice([True, False])
        # if flags["SUPPORT_UNICODE"]:
            # flags["SUPPORT_UNICODE_PROPERTIES"] = random.choice([True, False])
        # else:
            # flags["SUPPORT_UNICODE_PROPERTIES"] = False

        # 4. INDEPENDENT FEATURES: Greedy randomization
        # These don't usually break the build if toggled.
        independents = [
            "PCRE2_DEBUG", "EBCDIC", "EBCDIC_NL25", 
        ]





        for key in independents:
            if key in flags:
                flags[key] = random.choice([True, False])


        flags["SUPPORT_UNICODE"] = random.choice([True, False])
        # flags["SUPPORT_UNICODE"] = False
        if flags["SUPPORT_UNICODE"]:
            # flags["SUPPORT_UNICODE_PROPERTIES"] = random.choice([True, False])
            flags["EBCDIC"] = False
        # else:
            # flags["SUPPORT_UNICODE_PROPERTIES"] = False



        flags["SUPPORT_LIBZ"] = False
        flags["SUPPORT_LIBBZ2"] = False
        flags["SUPPORT_LIBREADLINE"] = False
        flags["SUPPORT_LIBEDIT"] = False
        flags["SUPPORT_VALGRIND"] = False

        # 5. MUTUAL EXCLUSION: Stack vs Heap
        # If using stack for recursion is False, it defaults to heap.
        if "HAVE_STACK_FOR_RECURSION" in flags:
            flags["HAVE_STACK_FOR_RECURSION"] = random.choice([True, False])

        # Convert back to your set of tuples format (String "True"/"False")
        self.flags = {(k, str(v)) for k, v in flags.items()}
        



    def clean_conflicts(self):
        flags = {k: v == "True" for k, v in self.flags}


        if flags["EBCDIC"]:
            flags["SUPPORT_UNICODE"] = False
            
        self.flags = {(k, str(v)) for k, v in flags.items()}




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
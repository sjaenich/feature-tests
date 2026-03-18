from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path


class FlacGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        
        flags = set()

        # Common FLAC / autotools-style macros
        flags.add(("HAVE_OGG", "False"))
        flags.add(("HAVE_STDINT_H", "True"))
        flags.add(("HAVE_STDLIB_H", "True"))
        flags.add(("HAVE_STRING_H", "True"))
        flags.add(("HAVE_MEMORY_H", "True"))
        flags.add(("HAVE_STRINGS_H", "True"))
        flags.add(("HAVE_SYS_TYPES_H", "True"))
        flags.add(("HAVE_SYS_STAT_H", "True"))
        flags.add(("HAVE_UNISTD_H", "True"))
        flags.add(("HAVE_INTTYPES_H", "True"))

        # FLAC-specific feature toggles
        flags.add(("FLAC__HAS_OGG", "False"))
        flags.add(("FLAC__CPU_X86_64", "False"))
        flags.add(("FLAC__CPU_IA32", "False"))
        flags.add(("FLAC__HAS_X86INTRIN", "False"))
        flags.add(("FLAC__USE_AVX", "False"))
        flags.add(("FLAC__USE_SSE", "False"))
        flags.add(("FLAC__USE_SSE2", "False"))
        flags.add(("FLAC__USE_SSE3", "False"))
        flags.add(("FLAC__USE_SSSE3", "False"))
        flags.add(("FLAC__USE_SSE4_1", "False"))
        flags.add(("FLAC__USE_SSE4_2", "False"))
        flags.add(("FLAC__USE_AVX2", "False"))
        flags.add(("FLAC__HAS_ASM", "False"))

        # Remove unused macros
        flags = self.remove_dead_macros(src_dir, flags)

        only_flags = {flag for (flag, _) in flags}

        self.modify_config_h(config_h, name, only_flags)
        
        return flags


    def modify_config_h(self, config_h, name: str, flags: set[str]):
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:

            out.write("/* Auto-extracted non-boolean defines */\n\n")

            for line in f:
                handled = False

                match = DEFINE_BOOL_RE.match(line)
                if match:
                    macro_name = match.group(1)
                    if macro_name in flags:
                        flags.add((macro_name, "True"))
                        dest.write(line)
                        handled = True

                m_undef = UNDEF_RE.match(line)
                if m_undef:
                    macro_name = m_undef.group(1)
                    if macro_name in flags:
                        flags.add((macro_name, "False"))
                        dest.write(line)
                        handled = True

                if not handled:
                    m_other = DEFINE_OTHER_RE.match(line)
                    if m_other:
                        out.write(line)

        shutil.move(path, f"/workspaces/RevEng/header/libraries/{name}.old.h")

        return flags


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
                    "--exclude=config.h",
                    macro,
                    str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)
                print(f"Macro {macro} is unused.")

        return {m for m in macros if m[0] not in unused}



# | Configure Flag                           | Macro(s) Affected      | Description                                              |
# | ---------------------------------------- | ---------------------- | -------------------------------------------------------- |
# | `--disable-asm` / `--enable-asm`         | `FLAC__NO_ASM`         | Disable or enable assembly optimizations                 |
# | `--disable-ogg` / `--enable-ogg`         | `FLAC__HAS_OGG`        | Enable Ogg FLAC support                                  |
# | `--disable-shared` / `--enable-shared`   | `FLAC__SHARED` (build) | Build shared library                                     |
# | `--disable-static` / `--enable-static`   | `FLAC__STATIC` (build) | Build static library                                     |
# | `--enable-debug`                         | `FLAC__DEBUGGING`      | Enable debugging                                         |
# | `--enable-asserts` / `--disable-asserts` | `FLAC__ASSERTIONS`     | Enable runtime assertions                                |
# | `--enable-threads` / `--disable-threads` | `FLAC__THREADS`        | Enable multi-threading support                           |
# | `--with-sysroot` / environment overrides | `FLAC__CPU_*`          | Platform-specific optimizations (conditionally compiled) |

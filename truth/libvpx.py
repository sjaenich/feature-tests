from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil


class LibvpxGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        
        flags = set()
        flags.add(("CONFIG_DEBUG", "False"))
        flags.add(("CONFIG_SIZE_LIMIT", "False"))
        flags.add(("CONFIG_ALWAYS_ADJUST_BPM", "False"))
        flags.add(("CONFIG_VP8_ENCODER", "False"))
        flags.add(("CONFIG_VP8_DECODER", "True"))
        flags.add(("CONFIG_VP9_ENCODER", "False"))
        flags.add(("CONFIG_VP9_DECODER", "True"))
        flags.add(("CONFIG_INTERNAL_STATS", "False"))
        flags.add(("CONFIG_POSTPROC", "False"))
        flags.add(("CONFIG_VP9_POSTPROC", "False"))
        flags.add(("CONFIG_MULTITHREAD", "True"))
        flags.add(("CONFIG_VP9_HIGHBITDEPTH", "False"))
        flags.add(("CONFIG_SHARED", "True"))
        flags.add(("CONFIG_STATIC", "False"))
        flags.add(("CONFIG_SMALL", "False"))
        flags.add(("CONFIG_POSTPROC_VISUALIZER", "False"))
        flags.add(("CONFIG_OS_SUPPORT", "True"))
        flags.add(("CONFIG_UNIT_TESTS", "False"))
        flags.add(("CONFIG_WEBM_IO", "False"))
        flags.add(("CONFIG_LIBYUV", "False"))
        flags.add(("CONFIG_DEQUANT_TOKENS", "False"))
        flags.add(("CONFIG_DC_RECON", "False"))
        flags.add(("CONFIG_RUNTIME_CPU_DETECT", "False"))

        flags = self.remove_dead_macros(src_dir,flags)

        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)

        flags = self.modify_config_h(config_h,name, only_flags)
        
        return flags



    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set[(str,str)]:
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = "/workspaces/RevEng/header/other_defines/other_defines" + name + ".h"
        destination = "/workspaces/RevEng/header/libraries/" + name + ".h"
        updated_flags = set()
        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
            open(destination, "w", encoding="utf-8") as dest, \
            open(out_path, "w", encoding="utf-8") as out:
            out.write("/* Auto-extracted non-boolean defines */\n\n")
            for line in f:
                print(line.rstrip())
                handled = False
                match = DEFINE_BOOL_RE.match(line)
                if match:
                    macro_name = match.group(1)
                    print("LINE", line, macro_name)
                    if macro_name in flags:
                        updated_flags.add((macro_name,"True"))
                        dest.write(line)
                        handled = True
                m_undef = UNDEF_RE.match(line)
                if m_undef:
                    macro_name = m_undef.group(1)                    
                    if macro_name in flags:
                        handled = True
                        updated_flags.add((macro_name,"False"))
                        dest.write(line)
                if not handled:
                    m_other = DEFINE_OTHER_RE.match(line)
                    if m_other:
                        out.write(line)
            
        
        shutil.move(path, "/workspaces/RevEng/header/libraries/" + name + ".old.h")   

        return updated_flags



    def remove_dead_macros(self, src_dir: Path, macros) -> set[str]:
        
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
# Configure Flag,Macro (C/C++),Purpose
# --enable-external-build,CONFIG_EXTERNAL_BUILD,"Use external build system (e.g., MSBuild)"
# --enable-install-docs,CONFIG_INSTALL_DOCS,Build and install Doxygen documentation
# --enable-install-bins,CONFIG_INSTALL_BINS,Build and install sample binaries
# --enable-install-libs,CONFIG_INSTALL_LIBS,Build and install static/shared libraries
# --enable-install-srcs,CONFIG_INSTALL_SRCS,Install library source code
# --enable-debug,CONFIG_DEBUG,Enable debug symbols and extra assertions
# --enable-gprof,CONFIG_GPROF,Enable profiling with gprof
# --enable-gcov,CONFIG_GCOV,Enable code coverage with gcov
# --enable-size-limit,CONFIG_SIZE_LIMIT,Limit max resolution (prevents DoS)
# --enable-vp8-encoder,CONFIG_VP8_ENCODER,VP8 Encoder support
# --enable-vp8-decoder,CONFIG_VP8_DECODER,VP8 Decoder support
# --enable-vp9-encoder,CONFIG_VP9_ENCODER,VP9 Encoder support
# --enable-vp9-decoder,CONFIG_VP9_DECODER,VP9 Decoder support
# --enable-internal-stats,CONFIG_INTERNAL_STATS,"Collect encoder statistics (PSNR, etc.)"
# --enable-postproc,CONFIG_POSTPROC,Enable post-processing filters
# --enable-vp9-postproc,CONFIG_VP9_POSTPROC,Specific post-processing for VP9
# --enable-multithread,CONFIG_MULTITHREAD,Support for multi-threaded operation
# --enable-vp9-highbitdepth,CONFIG_VP9_HIGHBITDEPTH,Enable 10/12-bit support for VP9
# --enable-shared,CONFIG_SHARED,Build shared libraries (.so / .dll)     
# --enable-static,CONFIG_STATIC,Build static libraries (.a / .lib)
# --enable-small,CONFIG_SMALL,Optimize for binary size over speed
# --enable-postproc-visualizer,CONFIG_POSTPROC_VISUALIZER,Visual debugging of macroblocks/motion
# --enable-os-support,CONFIG_OS_SUPPORT,Enable OS-specific features
# --enable-unit-tests,CONFIG_UNIT_TESTS,Build GTest unit tests
# --enable-webm-io,CONFIG_WEBM_IO,Simple WebM container I/O support
# --enable-libyuv,CONFIG_LIBYUV,Link against libyuv for conversions
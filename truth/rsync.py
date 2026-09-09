import random
from .config_truth import GroundTruthExtractor, dict_to_set, set_to_dict
import subprocess
import re
import shutil
from pathlib import Path

class RsyncGroundTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()

                # CPU / Algorithm Optimizations
        self.flags.add(("USE_ROLL_SIMD", "False"))  

        # --- Crypto & Checksums (--with-openssl) ---

        self.flags.add(("USE_OPENSSL", "True"))           # enables OpenSSL EVP usage

        # --- Compression Support ---

        self.flags.add(("SUPPORT_LZ4", "False"))           # --enable-lz4
        self.flags.add(("SUPPORT_ZSTD", "False"))          # --enable-zstd

        # --- Filesystem Metadata ---

        self.flags.add(("SUPPORT_ACLS", "False"))          # --enable-acl-support / --disable-acl-support
        self.flags.add(("SUPPORT_XATTRS", "True"))        # --enable-xattr-support / --disable-xattr-support

        # --- Networking & Encoding ---

        self.flags.add(("INET6", "True"))                 # --enable-ipv6
        # self.flags.add(("ICONV_OPTION", "False"))  


    def mix (self):
        flags = set_to_dict(self.flags)
                
        for key in flags:
            flags[key] = random.choice([True, False])

        flags["SUPPORT_LZ4"] = False
        flags["SUPPORT_ZSTD"] = False
        flags["SUPPORT_ACLS"] = False
        
        
        self.flags = dict_to_set(flags)
        



    def extract(self, config_h, name, src_dir):
        flags = self.flags

        # --disable-iconv (note: not HAVE_ICONV)

        # Clean up based on source usage to avoid "dead" configuration tracking
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
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
            
            out.write(f"/* rsync - User-Controllable Feature Flags */\n\n")
            
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

        # shutil.move(path, f"/workspaces/RevEng/header/libraries/{name}.old.h")
        return updated_flags

    def remove_dead_macros(self, src_dir: Path, macros) -> set:
        unused = []
        for (macro, _) in macros:
            try:
                # rsync is C only
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
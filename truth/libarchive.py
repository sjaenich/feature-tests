from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class LibarchiveGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        flags = set()
        
        # --- libarchive 3.7.9 Manual Feature Flags ---
        # These control high-level library capabilities and codec inclusion.
        
        flags.add(("HAVE_LIBBZ2", "True"))
        flags.add(("HAVE_LIBLZMA", "True"))
        flags.add(("HAVE_LIBZSTD", "False"))
        flags.add(("HAVE_LZ4_H", "False"))
        flags.add(("HAVE_LIBLZ4", "True"))
        flags.add(("HAVE_ACL","False"))
        
        # Crypto/Security Backends (Usually a manual choice)
        flags.add(("HAVE_LIBCRYPTO", "True")) 
        flags.add(("HAVE_LIBEXPAT", "True")) # OpenSSL
        flags.add(("HAVE_LIBNETTLE", "False"))
        flags.add(("HAVE_LIBMBEDTLS", "False"))
        
        # Specific Format Logic
        flags.add(("ARCHIVE_CRYPTO_MD5_OPENSSL", "True"))
        # flags.add(("ARCHIVE_ACL_FREEBSD", "False"))
        # flags.add(("ARCHIVE_ACL_LIBACL", "True"))
        # flags.add(("ARCHIVE_ACL_SUNOS", "False"))
        # Strip out macros that aren't referenced in the source files
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
            
            out.write(f"/* libarchive 3.7.9 - Manual Feature Selection Only */\n\n")
            
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
                # libarchive is almost entirely C, but search .cc just in case
                subprocess.check_output([
                    "grep", "-Rqw", 
                    "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}



# | Configure Flag                             | Macro(s) Affected | Description                        |
# | `--enable-xml2` / `--disable-xml2`         | `HAVE_LIBXML2`    | Enable libxml2 support (e.g., xar) |
# | ------------------------------------------ | ----------------- | ---------------------------------- |
# | `--with-zlib` / `--without-zlib`           | `HAVE_LIBZ`       | Enable/disable zlib (gzip) support |
# | `--with-bz2` / `--without-bz2`             | `HAVE_LIBBZ2`     | Enable/disable bzip2 support       |
# | `--with-lzma` / `--without-lzma`           | `HAVE_LIBLZMA`    | Enable/disable xz/lzma support     |
# | `--with-lz4` / `--without-lz4`             | `HAVE_LIBLZ4`     | Enable/disable lz4 support         |
# | `--with-zstd` / `--without-zstd`           | `HAVE_LIBZSTD`    | Enable/disable zstd support        |
# | `--with-openssl` / `--without-openssl`     | `HAVE_OPENSSL`    | Use OpenSSL for crypto             |
# | `--with-nettle` / `--without-nettle`       | `HAVE_NETTLE`     | Use nettle crypto backend          |
# | `--with-libgcrypt` / `--without-libgcrypt` | `HAVE_LIBGCRYPT`  | Use libgcrypt backend              |
# | `--enable-acl` / `--disable-acl`           | `HAVE_ACL`        | Enable POSIX ACL support           |
# | `--enable-xattr` / `--disable-xattr`       | `HAVE_XATTR`      | Enable extended attributes         |
# | `--enable-iconv` / `--disable-iconv`       | `HAVE_ICONV`      | Enable character set conversion    |
# | `--enable-expat` / `--disable-expat`       | `HAVE_LIBEXPAT`   | Enable expat XML support           |

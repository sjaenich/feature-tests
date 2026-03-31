from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class TcpdumpFeatureTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()
        print("THIS WORKED WELL")
        # --- tcpdump Configure-Controllable Flags ---
        
        # Security Sandboxing (--with-sandbox)
        # These are mutually exclusive based on the OS.
        self.flags.add(("HAVE_CAP_NG_H", "False"))      # Linux libcap-ng
        self.flags.add(("HAVE_CASPER", "False"))       # FreeBSD Casper
                
        # Privilege Dropping (--with-user, --with-chroot)
        self.flags.add(("WITH_USER", "False"))
        self.flags.add(("WITH_CHROOT", "False"))
        
        # Protocol Support Toggles
        # Some builds disable SMI (SNMP) or Crypto to reduce size/attack surface
        self.flags.add(("USE_LIBSMI", "False"))       # --with-smi
        self.flags.add(("HAVE_LIBCRYPTO", "False"))     # --with-crypto (OpenSSL)
        self.flags.add(("HAVE_OS_PROTO_H", "False"))
        
        # IPv6 Support (--enable-ipv6)
        self.flags.add(("HAVE_OS_IPV6_SUPPORT", "True"))
        
        # SMB Printing (--enable-smb)
        self.flags.add(("ENABLE_SMB", "False"))
        
        # Local Networking Headers
        self.flags.add(("HAVE_PCAP_DEBUG", "False"))
        self.flags.add(("HAVE_PCAP_LIST_DATALINKS", "True"))



    def extract(self, config_h, name, src_dir):
        flags = self.flags

        # Clean up based on source usage
        flags = self.remove_dead_macros(src_dir, flags)
        print("First iteration", flags)
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        flags = self.modify_config_h(config_h, name, only_flags)
        print("Second iteration", flags)
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
            
            out.write(f"/* tcpdump - User-Controllable Feature Flags */\n\n")
            
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
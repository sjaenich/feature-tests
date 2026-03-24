from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class LibpcapGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        flags = set()
        
        # --- libpcap Configure-Controllable Flags ---
        
        # Packet Capture Backends (--with-pcap=...)
        # These are usually autodetected but can be forced.
        flags.add(("ENABLE_REMOTE", "False"))     # Linux
        flags.add(("HAVE_OPENSSL", "False"))          # BSD/macOS
        flags.add(("HAVE_SOLARIS", "False"))
        
        # Specialized Link Layer Support
        flags.add(("PCAP_SUPPORT_BT", "False"))    # --enable-usb
        flags.add(("PCAP_SUPPORT_BT_MONITOR", "False")) # --enable-bluetooth
        flags.add(("PCAP_SUPPORT_DBUS", "False")) # --enable-netfilter
        flags.add(("PCAP_SUPPORT_DPDK", "False"))        # --enable-rdma
        flags.add(("PCAP_SUPPORT_LINUX_USBMON", "True"))        # --enable-dbus
        flags.add(("PCAP_SUPPORT_NETFILTER", "True"))   
        flags.add(("PCAP_SUPPORT_NETMAP", "False"))        
        flags.add(("PCAP_SUPPORT_RDMANIFF", "False"))      
        # Remote Capture Support (--enable-remote)
        flags.add(("HAVE_REMOTE", "False"))
        flags.add(("HAVE_RPCAPD", "False"))
        
        # IPv6 Support (--enable-ipv6)
        flags.add(("INET6", "True"))
    
        
        flags.add(("YYDEBUG", "False"))
        
        # Dag/Septel/Myricom High-Speed Cards
        flags.add(("HAVE_DAG_API", "False"))
        flags.add(("HAVE_SNF_API", "False"))
    
        # Filter out macros not used in the source code
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        # libpcap uses standard #define MACRO 1/0 or /* #undef MACRO */
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
            
            out.write(f"/* libpcap - User-Controllable Feature Flags */\n\n")
            
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
                # libpcap is C only
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
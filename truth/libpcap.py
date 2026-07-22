from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class LibpcapGroundTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()
                # --- libpcap Configure-Controllable Flags ---
        
        # Packet Capture Backends (--with-pcap=...)
        # These are usually autodetected but can be forced.
        # self.flags.add(("ENABLE_REMOTE", "False"))     # Linux
        # self.flags.add(("HAVE_OPENSSL", "False"))          # BSD/macOS
        # self.flags.add(("HAVE_SOLARIS", "False"))
        
        # Specialized Link Layer Support
        self.flags.add(("PCAP_SUPPORT_BT", "False"))    # --enable-usb
        self.flags.add(("PCAP_SUPPORT_BT_MONITOR", "False")) # --enable-bluetooth
        self.flags.add(("PCAP_SUPPORT_DBUS", "False")) # --enable-netfilter
        self.flags.add(("PCAP_SUPPORT_DPDK", "False"))        # --enable-rdma
        self.flags.add(("PCAP_SUPPORT_LINUX_USBMON", "True"))        # --enable-dbus
        self.flags.add(("PCAP_SUPPORT_NETFILTER", "True"))   
        self.flags.add(("PCAP_SUPPORT_NETMAP", "False"))        
        # self.flags.add(("PCAP_SUPPORT_RDMANIFF", "False"))      
        # Remote Capture Support (--enable-remote)
        # self.flags.add(("HAVE_REMOTE", "False"))
        # self.flags.add(("HAVE_RPCAPD", "False"))
        
        # IPv6 Support (--enable-ipv6)
        self.flags.add(("INET6", "True"))
    
        
        self.flags.add(("YYDEBUG", "False"))
        
        # Dag/Septel/Myricom High-Speed Cards
        self.flags.add(("HAVE_DAG_API", "False"))
        self.flags.add(("HAVE_SNF_API", "False"))


    def extract(self, config_h, name, src_dir):
        flags = self.flags
        
        # Filter out macros not used in the source code
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        flags = self.modify_config_h(config_h, name, only_flags)
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
        print("Move config", path)
        shutil.move(path, f"/workspaces/RevEng/header/libraries/{name}.old.h")
        if config_h.exists():
            print("CONFIG EXISTS", config_h)
        else:
            print("CONFIG DOES NOT EXIST", config_h)
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
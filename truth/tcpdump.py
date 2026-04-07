from .config_truth import GroundTruthExtractor
import subprocess
import re
import random
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



    def mix(self):
        # Convert set of tuples to a dictionary for easier logic
        flags = {k: v == "True" for k, v in self.flags}
        
        # 1. MUTUAL EXCLUSION: Security Sandboxing
        # You generally only use one sandbox type per OS.
        # On Linux, you'd use cap-ng; on FreeBSD, Casper.
        sandbox_options = ["HAVE_CAP_NG_H", "HAVE_CASPER"]
        
        # Pick at most one sandbox, or none.
        for opt in sandbox_options:
            flags[opt] = False
        
        # chosen_sandbox = random.choice(sandbox_options + [None])
        # if chosen_sandbox:
        #     flags[chosen_sandbox] = True

        # 2. DEPENDENCY: Privilege Dropping
        # It makes little sense to have a CHROOT without a USER to drop to.
        flags["WITH_USER"] = random.choice([True, False])
        if flags["WITH_USER"]:
            flags["WITH_CHROOT"] = random.choice([True, False])
        else:
            # If we aren't dropping to a user, we usually don't chroot.
            flags["WITH_CHROOT"] = False

        # 3. FEATURE TOGGLES: Protocol Support
        # These are independent but affect the binary size/capabilities.
        proto_flags = [
        # IPsec/crypto support
            "ENABLE_SMB",       # SMB printer
            "HAVE_OS_IPV6_SUPPORT"
        ]
        for key in proto_flags:
            if key in flags:
                flags[key] = random.choice([True, False])

    

        flags["USE_LIBSMI"]= False
        flags["HAVE_LIBCRYPTO"] = False
        flags["ENABLE_SMB"] = False

        flags["WITH_USER"] = False
        flags["WITH_CHROOT"] = False
        flags["HAVE_CAP_NG_H"] = False
        flags["HAVE_CASPER"] = False

        # 4. LOW-LEVEL/DEBUG FLAGS
        # PCAP_DEBUG is usually kept False unless you want a very noisy binary.
        flags["HAVE_PCAP_DEBUG"] = False
        # random.choice([True, False])
        
        # Essential capabilities are usually kept True to ensure a working tool.
        flags["HAVE_PCAP_LIST_DATALINKS"] = True 

        # Convert back to set of tuples with string "True"/"False"
        self.flags = {(k, str(v)) for k, v in flags.items()}
        print("tcpdump Flags after dependency-aware mixing:", self.flags)





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
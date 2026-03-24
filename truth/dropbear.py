from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path

class DropbearGroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        flags = set()
        
        # --- Dropbear Feature Macros (from default_options.h) ---
        
        # Protocol Features
        flags.add(("DROPBEAR_X11FWD", "False"))       # X11 Forwarding
        flags.add(("DROPBEAR_AGENTFWD", "True"))     # Agent Forwarding
        flags.add(("DROPBEAR_SFTPSERVER", "True"))   # SFTP Server support
        
        # Authentication Methods
        flags.add(("DROPBEAR_PASSWORD_AUTH", "True"))
        flags.add(("DROPBEAR_PUBKEY_AUTH", "True"))
        
        
        # Encryption Algorithms (Ciphers)
        flags.add(("DROPBEAR_AES128", "True"))
        flags.add(("DROPBEAR_AES256", "True"))
        flags.add(("DROPBEAR_CHACHA20POLY1305", "True"))
        flags.add(("DROPBEAR_3DES", "False"))        # Usually disabled for security
        
        # Message Authentication Codes (MACs)
        flags.add(("DROPBEAR_SHA1_MAC", "False"))
        flags.add(("DROPBEAR_SHA2_256_MAC", "True"))
        flags.add(("DROPBEAR_ENABLE_GCM_MODE", "False"))
        
        # Key Exchange (KEX)
        flags.add(("DROPBEAR_CURVE25519", "True"))
        flags.add(("DROPBEAR_ECDH", "True"))
        flags.add(("DROPBEAR_DH_GROUP14_SHA1", "False"))
        flags.add(("DROBPBEAR_DH_GROUP14_SHA256","False"))
        
        # Server Options
        flags.add(("DO_HOST_LOOKUP", "False"))


        # Filter out macros not used in the source code
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        # Dropbear uses #define MACRO 1/0 style
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        # Catch port numbers and path strings (like DROPBEAR_PATH_SSH_PROGRAM)
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+(DROPBEAR_[A-Z_]+|[A-Z_][A-Z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* Dropbear SSH - Feature Toggles */\n\n")
            
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
                # Dropbear is C only
                subprocess.check_output([
                    "grep", "-Rqw", "--include=*.c", "--include=*.h", 
                    macro, str(src_dir)
                ])
            except subprocess.CalledProcessError:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
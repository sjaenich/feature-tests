from sys import flags
import random
from .config_truth import GroundTruthExtractor, dict_to_set, set_to_dict
import subprocess
import re
import shutil
from pathlib import Path

class DbusGroundTruth(GroundTruthExtractor):
    def __init__(self):
        self.flags = set()
        self.flags.add(("HAVE_UNIX_FD_PASSING", "True"))
        self.flags.add(("DBUS_ENABLE_STATS", "True"))
        
        # Security & Mandatory Access Control (--enable-selinux, --enable-apparmor)
        self.flags.add(("HAVE_SELINUX", "False"))
        self.flags.add(("HAVE_APPARMOR", "False"))

        
        # Authentication Mechanisms (--enable-checks)
        # These determine which 'AUTH' commands are accepted during the handshake
        self.flags.add(("DBUS_DISABLE_CHECKS", "False"))
        self.flags.add(("DBUS_DISABLE_ASSERT", "True"))
        
        # System Integration (--with-systemdsystemunitdir)
        self.flags.add(("DBUS_ENABLE_CHECKS", "True"))
        self.flags.add(("HAVE_MONOTONIC_CLOCK", "True"))
        
        # Resource Limits & Debugging
        self.flags.add(("DBUS_ENABLE_ASSERT", "False"))
        self.flags.add(("DBUS_ENABLE_EMBEDDED_TESTS", "False"))
        self.flags.add(("NDEBUG", "True")) 


    def mix(self):
        flags = set_to_dict(self.flags)

        # --- Step 1: randomize independent flags ---
        independent = [
            "HAVE_UNIX_FD_PASSING",
            "DBUS_ENABLE_STATS",
            # "HAVE_SELINUX",
            "HAVE_APPARMOR",
            "HAVE_MONOTONIC_CLOCK",
        ]

        for key in independent:
            if key in flags:
                flags[key] = random.choice([True, False])

        # --- Step 2: randomize base control flags ---
        flags["NDEBUG"] = random.choice([True, False])
        flags["DBUS_ENABLE_EMBEDDED_TESTS"] = random.choice([True, False])
        flags["DBUS_DISABLE_CHECKS"] = random.choice([True, False])
        flags["DBUS_DISABLE_ASSERT"] = random.choice([True, False])

        # --- Step 3: enforce dependencies ---

        # Assertions: ENABLE = not DISABLE
        flags["DBUS_ENABLE_ASSERT"] = not flags["DBUS_DISABLE_ASSERT"]

        # Checks: ENABLE = not DISABLE
        flags["DBUS_ENABLE_CHECKS"] = not flags["DBUS_DISABLE_CHECKS"]

        # NDEBUG implies assertions disabled
        if flags["NDEBUG"]:
            flags["DBUS_DISABLE_ASSERT"] = True
            flags["DBUS_ENABLE_ASSERT"] = False

        # Embedded tests require debug + checks + asserts
        if flags["DBUS_ENABLE_EMBEDDED_TESTS"]:
            flags["NDEBUG"] = False
            flags["DBUS_DISABLE_ASSERT"] = False
            flags["DBUS_ENABLE_ASSERT"] = True
            flags["DBUS_DISABLE_CHECKS"] = False
            flags["DBUS_ENABLE_CHECKS"] = True

        # --- Step 4: write back ---
        self.flags = dict_to_set(flags)



    def extract(self, config_h, name, src_dir):
        print("DID THIS WORK", self.flags)
        flags = self.flags
        
        # --- D-Bus Configure-Controllable Flags ---
        
        # Transport Mechanisms (--enable-unix-fds, --enable-tcp-transport)


        # Filter based on actual source usage
        flags = self.remove_dead_macros(src_dir, flags)
        print("Remaining macros after removing unused ones:", flags)
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        flags = self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        # Matches DBUS_ specific constants and paths
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+(DBUS_[A-Z_]+|[A-Z_][A-Z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* D-Bus - User-Controllable Feature Flags */\n\n")
            
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
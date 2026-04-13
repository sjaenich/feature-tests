from sys import flags
import random
from .config_truth import GroundTruthExtractor, dict_to_set, set_to_dict
import subprocess
import re
import shutil
from pathlib import Path


class LibopensslGroundTruth(GroundTruthExtractor):
    def __init__(self):
        self.flags = set()

        # Only user-controllable OpenSSL feature macros that materially affect libssl.
        # These are negative feature macros: True means the feature is disabled.
        self.flags.add(("OPENSSL_NO_PSK", "False"))
        self.flags.add(("OPENSSL_NO_SRP", "False"))
        self.flags.add(("OPENSSL_NO_OCSP", "False"))
        self.flags.add(("OPENSSL_NO_CT", "False"))
        self.flags.add(("OPENSSL_NO_NEXTPROTONEG", "False"))
        self.flags.add(("OPENSSL_NO_SRTP", "False"))
        self.flags.add(("OPENSSL_NO_DTLS", "False"))
        self.flags.add(("OPENSSL_NO_TLS1_3", "False"))
        self.flags.add(("OPENSSL_NO_COMP", "True"))  # often disabled by default in practice

        # Optional but still libssl-relevant. Uncomment if you want a wider search space.
        self.flags.add(("OPENSSL_NO_EC", "False"))
        self.flags.add(("OPENSSL_NO_DH", "False"))

    def mix(self):
        f = set_to_dict(self.flags)

        independent = [
            "OPENSSL_NO_PSK",
            "OPENSSL_NO_SRP",
            "OPENSSL_NO_OCSP",
            "OPENSSL_NO_CT",
            "OPENSSL_NO_NEXTPROTONEG",
            "OPENSSL_NO_SRTP",
            "OPENSSL_NO_DTLS",
            "OPENSSL_NO_TLS1_3",
            "OPENSSL_NO_COMP",
            "OPENSSL_NO_EC",
            "OPENSSL_NO_DH",
        ]

        for key in independent:
            if key in f:
                f[key] = random.choice([True, False])

        # Conservative dependency handling:
        # SRTP is DTLS-oriented in libssl, so if DTLS is disabled,
        # treating SRTP as disabled avoids inconsistent combinations.
        if f.get("OPENSSL_NO_DTLS", False):
            f["OPENSSL_NO_SRTP"] = True

        self.flags = dict_to_set(f)

    def extract(self, config_h, name, src_dir):
        flags = self.flags

        # Restrict to macros that actually appear in libssl-relevant code.
        flags = self.remove_dead_macros(src_dir, flags)

        only_flags = {flag for (flag, _) in flags}
        flags = self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        DEFINE_RE = re.compile(r'^\s*#\s*define\s+([A-Z0-9_]+)\b')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#\s*undef\s+([A-Z0-9_]+)\s*\*/\s*$')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"

        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:

            out.write("/* OpenSSL/libssl - User-Controllable Feature Flags */\n\n")

            for line in f:
                handled = False

                m_def = DEFINE_RE.match(line)
                if m_def:
                    macro_name = m_def.group(1)
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
                    # Keep other preprocessor definitions elsewhere for inspection.
                    if line.lstrip().startswith("#define"):
                        out.write(line)

        shutil.move(path, f"/workspaces/RevEng/header/libraries/{name}.old.h")
        return updated_flags

    def remove_dead_macros(self, src_dir: Path, macros) -> set:
        """
        Keep only macros referenced from libssl-relevant source.
        We search ssl/ plus public OpenSSL headers, not the whole source tree.
        """
        search_roots = [
            src_dir / "ssl",
            src_dir / "include",
        ]

        unused = []

        for (macro, _) in macros:
            found = False
            for root in search_roots:
                if not root.exists():
                    continue
                try:
                    subprocess.check_output([
                        "grep", "-Rqw",
                        "--include=*.c", "--include=*.h",
                        macro, str(root)
                    ])
                    found = True
                    break
                except subprocess.CalledProcessError:
                    pass

            if not found:
                unused.append(macro)

        return {m for m in macros if m[0] not in unused}
from sys import flags
import random
from .config_truth import GroundTruthExtractor, dict_to_set, set_to_dict
import subprocess
import re
import shutil
from pathlib import Path


class OpensslGroundTruth(GroundTruthExtractor):
    def __init__(self):
        self.flags = set()

        # Only user-controllable OpenSSL feature macros that materially affect libcrypto.
        # These are negative feature macros: True means the feature is disabled.
        self.flags.add(("OPENSSL_NO_ARIA", "False"))
        self.flags.add(("OPENSSL_NO_BF", "False"))
        self.flags.add(("OPENSSL_NO_CAMELLIA", "False"))
        self.flags.add(("OPENSSL_NO_CAST", "False"))
        self.flags.add(("OPENSSL_NO_DES", "False"))
        self.flags.add(("OPENSSL_NO_IDEA", "False"))
        self.flags.add(("OPENSSL_NO_MD4", "False"))
        self.flags.add(("OPENSSL_NO_OCB", "False"))
        self.flags.add(("OPENSSL_NO_RC2", "False"))
        self.flags.add(("OPENSSL_NO_RC4", "False"))
        self.flags.add(("OPENSSL_NO_SCRYPT", "False"))
        self.flags.add(("OPENSSL_NO_SEED", "False"))
        self.flags.add(("OPENSSL_NO_SIPHASH", "False"))
        self.flags.add(("OPENSSL_NO_SM2", "False"))
        self.flags.add(("OPENSSL_NO_SM3", "False"))
        self.flags.add(("OPENSSL_NO_SM4", "False"))
        self.flags.add(("OPENSSL_NO_WHIRLPOOL", "False"))

        # Optional wider crypto search space:
        self.flags.add(("OPENSSL_NO_BLAKE2", "False"))
        self.flags.add(("OPENSSL_NO_CHACHA", "False"))
        self.flags.add(("OPENSSL_NO_POLY1305", "False"))
        self.flags.add(("OPENSSL_NO_CMAC", "False"))
        self.flags.add(("OPENSSL_NO_CMP", "False"))
        self.flags.add(("OPENSSL_NO_CMS", "False"))
        self.flags.add(("OPENSSL_NO_EC", "False"))
        self.flags.add(("OPENSSL_NO_DH", "False"))
        self.flags.add(("OPENSSL_NO_DSA", "False"))

    def mix(self):
        f = set_to_dict(self.flags)

        independent = [
            "OPENSSL_NO_ARIA",
            "OPENSSL_NO_BF",
            "OPENSSL_NO_CAMELLIA",
            "OPENSSL_NO_CAST",
            "OPENSSL_NO_DES",
            "OPENSSL_NO_IDEA",
            "OPENSSL_NO_MD4",
            "OPENSSL_NO_OCB",
            "OPENSSL_NO_RC2",
            "OPENSSL_NO_RC4",
            "OPENSSL_NO_SCRYPT",
            "OPENSSL_NO_SEED",
            "OPENSSL_NO_SIPHASH",
            "OPENSSL_NO_SM2",
            "OPENSSL_NO_SM3",
            "OPENSSL_NO_SM4",
            "OPENSSL_NO_WHIRLPOOL",
            "OPENSSL_NO_BLAKE2",
            "OPENSSL_NO_CHACHA",
            "OPENSSL_NO_POLY1305",
            "OPENSSL_NO_CMAC",
            "OPENSSL_NO_CMP",
            "OPENSSL_NO_CMS",
            "OPENSSL_NO_EC",
            "OPENSSL_NO_DH",
            "OPENSSL_NO_DSA",
        ]

        for key in independent:
            if key in f:
                f[key] = random.choice([True, False])

        # Conservative dependency handling for the SM family:
        # disabling SM3 usually makes SM2 much less meaningful.
        if f.get("OPENSSL_NO_SM3", False):
            f["OPENSSL_NO_SM2"] = True

        self.flags = dict_to_set(f)

    def extract(self, config_h, name, src_dir):
        flags = self.flags

        # Restrict to macros that actually appear in libcrypto-relevant code.
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

            out.write("/* OpenSSL/libcrypto - User-Controllable Feature Flags */\n\n")

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
                    if line.lstrip().startswith("#define"):
                        out.write(line)

        shutil.move(path, f"/workspaces/RevEng/header/libraries/{name}.old.h")
        return updated_flags

    def remove_dead_macros(self, src_dir: Path, macros) -> set:
        """
        Keep only macros referenced from libcrypto-relevant source.
        Search crypto/ plus public headers, not the whole OpenSSL tree.
        """
        search_roots = [
            src_dir / "crypto",
            src_dir / "include",
            src_dir / "providers",  # optional but often relevant in OpenSSL 3.x
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
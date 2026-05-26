from .config_truth import GroundTruthExtractor
import subprocess
import re
import shutil
from pathlib import Path
import random

class LibcurlGroundTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()        
        # self.flags.add(("CURL_DISABLE_FTP", "False"))
        # self.flags.add(("CURL_DISABLE_HTTP", "False"))
        # self.flags.add(("CURL_DISABLE_LDAP", "True"))
        # self.flags.add(("CURL_DISABLE_TELNET", "True"))
        # self.flags.add(("CURL_DISABLE_DICT", "True"))
        # self.flags.add(("CURL_DISABLE_FILE", "False"))
        # self.flags.add(("CURL_DISABLE_TFTP", "True"))
        # self.flags.add(("CURL_DISABLE_SMTP", "False"))
        # self.flags.add(("CURL_DISABLE_POP3", "False"))
        # self.flags.add(("CURL_DISABLE_IMAP", "False"))
        # self.flags.add(("CURL_DISABLE_SMB", "False"))
        # self.flags.add(("CURL_DISABLE_GOPHER", "True"))
        # self.flags.add(("CURL_DISABLE_MQTT", "False")) # Added in 7.70.0
        
        # # Feature Toggles
        # self.flags.add(("CURL_DISABLE_COOKIES", "False"))
        # self.flags.add(("CURL_DISABLE_CRYPTO_AUTH", "False"))
        # self.flags.add(("CURL_DISABLE_VERBOSE_STRINGS", "True"))
        # self.flags.add(("CURL_DISABLE_PROXY", "False"))
        
        # # TLS Backend Selection (Usually only one is True)
        # self.flags.add(("USE_OPENSSL", "True"))
        # self.flags.add(("USE_GNUTLS", "False"))
        # self.flags.add(("USE_NSS", "False"))
        # self.flags.add(("USE_MBEDTLS", "False"))
        # self.flags.add(("USE_WOLFSSL", "False"))
        
        # # Library Features
        # self.flags.add(("USE_NGHTTP2", "False"))   # HTTP/2 support
        # self.flags.add(("USE_LIBIDN2", "False"))   # International Domain Names
        # self.flags.add(("USE_LIBSSH2", "False"))   # SCP/SFTP support
        # self.flags.add(("USE_LIBZ", "True"))      # Gzip decompression
        
        # # System/Security Logic
        # self.flags.add(("USE_ARES", "False"))     # C-Ares for async DNS
        # self.flags.add(("USE_THREADS_POSIX", "False"))
        

        self.flags.add(('CURL_DISABLE_PROXY', 'False'))
        self.flags.add(('CURL_DISABLE_IMAP', 'False'))
        self.flags.add(('CURL_DISABLE_POP3', 'False'))
        self.flags.add(('USE_NGHTTP2', 'False'))
        self.flags.add(('CURL_DISABLE_DICT','True'))
        self.flags.add(('CURL_DISABLE_SMB', 'True'))
        self.flags.add(('USE_GNUTLS', 'True'))
        self.flags.add(('CURL_DISABLE_VERBOSE_STRINGS', 'True'))
        self.flags.add(('CURL_DISABLE_CRYPTO_AUTH', 'False')) 
        self.flags.add(('CURL_DISABLE_GOPHER', 'True'))
        self.flags.add(('USE_OPENSSL', 'True'))
        self.flags.add(('CURL_DISABLE_FILE', 'False'))
        self.flags.add(('USE_ARES', 'False'))
        self.flags.add(('USE_THREADS_POSIX', 'False'))
        self.flags.add(('CURL_DISABLE_LDAP', 'True'))
        self.flags.add(('CURL_DISABLE_COOKIES', 'False'))
        self.flags.add(('CURL_DISABLE_TELNET', 'True'))
        self.flags.add(('USE_WOLFSSL', 'False'))
        self.flags.add(('CURL_DISABLE_RTSP', 'False'))
        self.flags.add(('CURL_DISABLE_TFTP', 'False'))
        self.flags.add(('CURL_DISABLE_SMTP', 'False'))
        self.flags.add(('USE_LIBSSH2', 'True'))
        self.flags.add(('CURL_DISABLE_HTTP', 'False'))
        self.flags.add(('USE_MBEDTLS', 'False'))
        self.flags.add(('CURL_DISABLE_FTP', 'False'))
        self.flags.add(('CURL_DISABLE_HTTP_AUTH', 'False'))
        self.flags.add(('CURL_DISABLE_LDAPS', 'True'))
        self.flags.add(('HAVE_LIBZ', 'True'))
        self.flags.add(('HAVE_LIBSSL', 'True'))
        self.flags.add(('NTLM_WB_ENABLED', 'True'))
        self.flags.add(("ENABLE_IPV6", "True"))


        # {('CURL_DISABLE_DICT', 'True'), ('CURL_DISABLE_FTP', 'False'), ('CURL_DISABLE_TFTP', 'False'), ('NTLM_WB_ENABLED', 'True'), ('CURL_DISABLE_LDAP', 'True'), ('USE_LIBSSH2', 'True'), ('CURL_DISABLE_FILE', 'False'), ('CURL_DISABLE_RTSP', 'False'), ('ENABLE_IPV6', 'True'), ('HAVE_LIBZ', 'True'), ('USE_GNUTLS', 'True'), ('CURL_DISABLE_PROXY', 'False'), ('CURL_DISABLE_CRYPTO_AUTH', 'False'), ('CURL_DISABLE_COOKIES', 'False'), ('CURL_DISABLE_SMTP', 'False'), ('CURL_DISABLE_GOPHER', 'True'), ('CURL_DISABLE_TELNET', 'True'), ('CURL_DISABLE_POP3', 'False'), ('CURL_DISABLE_VERBOSE_STRINGS', 'True'), ('USE_GNUTLS_PRIORITY_SET_DIRECT', 'False'), ('CURL_DISABLE_IMAP', 'False'), ('CURL_DISABLE_HTTP', 'False'), ('USE_ARES', 'True')}





    def mix(self):
        
        flags = set()
        # Randomize ZLIB independently
        toggle_flags = [
            "CURL_DISABLE_FTP", "CURL_DISABLE_HTTP", "CURL_DISABLE_FILE",
            "CURL_DISABLE_SMTP", "CURL_DISABLE_POP3", "CURL_DISABLE_IMAP",
            "CURL_DISABLE_SMB", "CURL_DISABLE_MQTT", "CURL_DISABLE_COOKIES",
            "CURL_DISABLE_CRYPTO_AUTH", "CURL_DISABLE_VERBOSE_STRINGS",
            "CURL_DISABLE_PROXY", "USE_LIBZ" 
        ]
        
        # Legacy/Obscure protocols you might want to keep disabled more often
        heavy_disable_flags = [
            "CURL_DISABLE_LDAP", "CURL_DISABLE_TELNET", 
            "CURL_DISABLE_DICT", "CURL_DISABLE_TFTP", "CURL_DISABLE_GOPHER"
        ]

        # Mutually Exclusive (Pick exactly one)
        tls_backends = [
            "USE_OPENSSL", "USE_GNUTLS", "USE_NSS", "USE_MBEDTLS", "USE_WOLFSSL"
        ]


        for flag in toggle_flags:
            value = random.choice(["True", "False"])
            flags.add((flag, value))

        # 2. Randomize legacy protocols (weighted towards "True" to keep them disabled)
        for flag in heavy_disable_flags:
            value = random.choices(["True", "False"], weights=[0.8, 0.2])[0]
            flags.add((flag, value))

        # 3. Pick exactly one TLS backend
        
        flags.add(("USE_OPENSSL", "True"))
            

        # 4. System Logic (e.g., POSIX threads usually True on Linux)
        flags.add(("USE_THREADS_POSIX", "False"))

        flags.add(("USE_NGHTTP2", "False"))
        flags.add(("USE_LIBIDN2", "False"))
        flags.add(("USE_LIBSSH2","False"))
        flags.add(("USE_ARES", "False"))


        self.flags = flags

        self.flags.add(("USE_GNUTLS", "False"))
        self.flags.add(("USE_NSS", "False"))
        self.flags.add(("USE_MBEDTLS", "False"))
        self.flags.add(("USE_WOLFSSL", "False"))




    def extract(self, config_h, name, src_dir):
        flags = self.flags
        
        # Filter out macros not used in the actual source code
        flags = self.remove_dead_macros(src_dir, flags)
        
        only_flags = set()
        for (flag, _) in flags:
            only_flags.add(flag)
            
        self.modify_config_h(config_h, name, only_flags)
        return flags

    def modify_config_h(self, config_h, name: str, flags: set[str]) -> set:
        # libcurl uses #define MACRO 1 or /* #undef MACRO */
        DEFINE_BOOL_RE = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+(?:0|1)\s*$')
        UNDEF_RE = re.compile(r'^\s*/\*\s*#undef\s+([A-Z0-9_]+)\s*\*/\s*$')
        # Matches CURL_ and USE_ constants
        DEFINE_OTHER_RE = re.compile(r'^\s*#define\s+(CURL_[A-Z_]+|USE_[A-Z_]+|[A-Z_][A-Z0-9_]*)\b(?!\s*\()')

        path = str(config_h)
        out_path = f"/workspaces/RevEng/header/other_defines/other_defines_{name}.h"
        destination = f"/workspaces/RevEng/header/libraries/{name}.h"
        
        updated_flags = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as f, \
             open(destination, "w", encoding="utf-8") as dest, \
             open(out_path, "w", encoding="utf-8") as out:
            
            out.write(f"/* libcurl 7.71.1 - User-Controllable Feature Flags */\n\n")
            
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
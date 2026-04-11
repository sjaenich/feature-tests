from .config_truth import GroundTruthExtractor
import random 



class Libxml2GroundTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()
        self.flags.add(("LIBXML_C14N_ENABLED", "True"))
        self.flags.add(("LIBXML_CATALOG_ENABLED", "True"))
        self.flags.add(("LIBXML_DEBUG_ENABLED", "True")) 
    

        self.flags.add(("LIBXML_FTP_ENABLED", "False"))
        self.flags.add(("LIBXML_HISTORY_ENABLED", "False"))

        self.flags.add(("LIBXML_HTML_ENABLED", "True"))
        self.flags.add(("LIBXML_HTTP_ENABLED", "False"))

        self.flags.add(("LIBXML_ICONV_ENABLED", "True"))
        self.flags.add(("LIBXML_ICU_ENABLED", "False"))
        self.flags.add(("LIBXML_ISO8859X_ENABLED", "True"))

        self.flags.add(("LIBXML_LZMA_ENABLED", "False"))

        self.flags.add(("LIBXML_MODULES_ENABLED", "True"))

        self.flags.add(("LIBXML_OUTPUT_ENABLED", "True"))
        self.flags.add(("LIBXML_PATTERN_ENABLED", "True"))
        self.flags.add(("LIBXML_PUSH_ENABLED", "True"))

        self.flags.add(("LIBXML_PYTHON_ENABLED", "True"))

        self.flags.add(("LIBXML_READER_ENABLED", "True"))
        self.flags.add(("LIBXML_REGEXP_ENABLED", "True"))

        self.flags.add(("LIBXML_SAX1_ENABLED", "True"))

        self.flags.add(("LIBXML_SCHEMAS_ENABLED", "True"))
        self.flags.add(("LIBXML_RELAXNG_ENABLED", "True"))

        self.flags.add(("LIBXML_SCHEMATRON_ENABLED", "True"))

        self.flags.add(("LIBXML_THREAD_ENABLED", "True"))
        self.flags.add(("LIBXML_THREAD_ALLOC_ENABLED", "False"))

        self.flags.add(("LIBXML_TREE_ENABLED", "True"))

        self.flags.add(("LIBXML_VALID_ENABLED", "True"))

        self.flags.add(("LIBXML_WRITER_ENABLED", "True"))

        self.flags.add(("LIBXML_XINCLUDE_ENABLED", "True"))
        self.flags.add(("LIBXML_XPATH_ENABLED", "True"))

        self.flags.add(("LIBXML_XPTR_ENABLED", "True"))
        self.flags.add(("LIBXML_XPTR_LOCS_ENABLED", "False"))

        self.flags.add(("LIBXML_ZLIB_ENABLED", "False"))

        self.flags.add(("LIBXML_MINIMUM_ENABLED", "False"))
        self.flags.add(("LIBXML_LEGACY_ENABLED", "False"))

        self.flags.add(("LIBXML_TLS_ENABLED", "False"))


    def mix(self):
        # 1. Convert set of tuples (String) to a working dictionary (Bool)
        flags = {k: (v == "True") for k, v in self.flags}
        
        # 2. CORE PROTECTION
        # Without TREE and OUTPUT, the library is essentially useless and 
        # many other modules will fail to link.
        flags["LIBXML_TREE_ENABLED"] = True
        flags["LIBXML_OUTPUT_ENABLED"] = True
        
        # 3. HIERARCHICAL MIXING (Top-Down)
        
        # --- Level 1: XPath ---
        # XPath is the most common parent dependency.
        flags["LIBXML_XPATH_ENABLED"] = random.choice([True, False])
        
        if not flags["LIBXML_XPATH_ENABLED"]:
            # If XPath is off, these MUST be off
            flags["LIBXML_XPTR_ENABLED"] = False
            flags["LIBXML_XPTR_LOCS_ENABLED"] = False
            flags["LIBXML_SCHEMAS_ENABLED"] = False
            flags["LIBXML_SCHEMATRON_ENABLED"] = False
            flags["LIBXML_RELAXNG_ENABLED"] = False
            flags["LIBXML_C14N_ENABLED"] = False
        else:
            # If XPath is on, we can roll for its children
            flags["LIBXML_XPTR_ENABLED"] = random.choice([True, False])
            flags["LIBXML_SCHEMAS_ENABLED"] = random.choice([True, False])
            flags["LIBXML_RELAXNG_ENABLED"] = random.choice([True, False])
            flags["LIBXML_C14N_ENABLED"] = random.choice([True, False])
            
            # XPointer Locations specifically need XPointer
            if flags["LIBXML_XPTR_ENABLED"]:
                flags["LIBXML_XPTR_LOCS_ENABLED"] = random.choice([True, False])
            else:
                flags["LIBXML_XPTR_LOCS_ENABLED"] = False

        # --- Level 2: Regexp ---
        # Schemas and Schematron require the Regexp engine.
        flags["LIBXML_REGEXP_ENABLED"] = random.choice([True, False])
        if not flags["LIBXML_REGEXP_ENABLED"]:
            flags["LIBXML_SCHEMAS_ENABLED"] = False
            flags["LIBXML_SCHEMATRON_ENABLED"] = False
        else:
            # If Regexp is on AND XPath is on, we can enable Schematron
            if flags["LIBXML_XPATH_ENABLED"]:
                flags["LIBXML_SCHEMATRON_ENABLED"] = random.choice([True, False])

        # 4. STANDALONE FEATURES
        # These are generally safe to toggle independently.
        independents = [
            "LIBXML_HTML_ENABLED", "LIBXML_PUSH_ENABLED", "LIBXML_READER_ENABLED", 
            "LIBXML_WRITER_ENABLED", "LIBXML_SAX1_ENABLED", "LIBXML_XINCLUDE_ENABLED",
            "LIBXML_CATALOG_ENABLED", "LIBXML_DEBUG_ENABLED", "LIBXML_MODULES_ENABLED",
            "LIBXML_HTTP_ENABLED", "LIBXML_FTP_ENABLED", "LIBXML_VALID_ENABLED"
        ]
        for key in independents:
            if key in flags:
                flags[key] = random.choice([True, False])

        # 5. EXTERNAL LIBRARIES (Safety)
        # Only set to True if you are sure they are in your Buildroot environment.
        flags["LIBXML_ZLIB_ENABLED"] = False  # Avoid 'undefined reference to inflate'
        flags["LIBXML_LZMA_ENABLED"] = False
        flags["LIBXML_ICONV_ENABLED"] = True  # Usually safe on Linux/ARM

        # 6. Convert back to set of tuples for the rest of your pipeline
        self.flags = {(k, str(v)) for k, v in flags.items()}



    def extract(self, config_h, name, src_dir):
        flags = self.flags


        return flags
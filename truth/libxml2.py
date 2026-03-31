from .config_truth import GroundTruthExtractor




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


    def extract(self, config_h, name, src_dir):
        flags = self.flags


        return flags
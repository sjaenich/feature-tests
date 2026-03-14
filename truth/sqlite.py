from .config_truth import GroundTruthExtractor


class SqliteGroundTruth(GroundTruthExtractor):

    def extract(self, config_h, name, src_dir):
        flags = self.modify_config_h(config_h, name)
        
        flags = set()
        flags.add(("SQLITE_ENABLE_FTS5", "True"))
        flags.add(("SQLITE_ENABLE_JSON1", "True"))
        flags.add(("SQLITE_ENABLE_FTS3", "True"))
        flags.add(("SQLITE_ENABLE_STAT4", "True"))
        flags.add(("SQLITE_ENABLE_RTREE", "True"))
        flags.add(("SQLITE_ENABLE_JSON1", "True"))
        flags.add(("SQLITE_ENABLE_GEOPOLY", "True"))
        flags.add(("SQLITE_ENABLE_MATH_FUNCTIONS", "True"))
        flags.add(("SQLITE_ENABLE_FTS4", "False"))
        flags.add(("SQLITE_ENABLE_SESSION", "False"))
        flags.add(("SQLITE_ENABLE_MEMSYS3", "False"))
        flags.add(("SQLITE_ENABLE_MEMSYS5", "False"))



        return flags
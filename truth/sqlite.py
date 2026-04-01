import re

from .config_truth import GroundTruthExtractor, dict_to_set, set_to_dict
import random

class SqliteGroundTruth(GroundTruthExtractor):

    def __init__(self):
        self.flags = set()
        self.flags.add(("SQLITE_ENABLE_FTS5", "True"))
        self.flags.add(("SQLITE_ENABLE_JSON1", "True"))
        self.flags.add(("SQLITE_ENABLE_FTS3", "True"))
        self.flags.add(("SQLITE_ENABLE_STAT4", "True"))
        self.flags.add(("SQLITE_ENABLE_RTREE", "True"))
        self.flags.add(("SQLITE_ENABLE_JSON1", "True"))
        self.flags.add(("SQLITE_ENABLE_GEOPOLY", "True"))
        self.flags.add(("SQLITE_ENABLE_MATH_FUNCTIONS", "True"))
        self.flags.add(("SQLITE_ENABLE_FTS4", "False"))
        self.flags.add(("SQLITE_ENABLE_SESSION", "False"))
        self.flags.add(("SQLITE_ENABLE_MEMSYS3", "False"))
        self.flags.add(("SQLITE_ENABLE_MEMSYS5", "False"))





    def mix_cflags(self, project):
        flags = set_to_dict(self.flags)
    
        
        print("Flags after mixing:", flags)

        # 2. Parse existing cflags into a set
        cflags_str = project.metadata.get("cflags", "")
        cflag_tokens = set(cflags_str.split())

        # Remove all existing -D<FLAG> entries for our flags
        for key in flags:
            pattern = re.compile(rf"-D{re.escape(key)}(=.+)?")
            cflag_tokens = {tok for tok in cflag_tokens if not pattern.fullmatch(tok)}

        # 3. Rebuild flags based on new values
        for key, value in flags.items():
            if value:
                cflag_tokens.add(f"-D{key}")
            # if False → do not add (effectively disabled)

        # 4. Write back
        project.metadata["cflags"] = " ".join(sorted(cflag_tokens))
        
    
        return project.metadata["cflags"]
        




    def extract(self, config_h, name, src_dir):
        flags = self.modify_config_h(config_h, name)
        
        flags = self.flags




        return flags
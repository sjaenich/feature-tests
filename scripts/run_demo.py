from contextlib import redirect_stdout
from pathlib import Path
from multiprocessing import Pool

from core.project import Project
from build.buildroot import BuildrootBuildManager
from locate.config_locator import ConfigLocator
from recovery.runner import FlagRecoveryRunner
from truth.config_truth import GroundTruthExtractor
from evaluation.comparator import ResultComparator
from pipeline.experiment import ExperimentRunner
from truth.sqlite import SqliteGroundTruth
from truth.libvpx import LibvpxGroundTruth
from truth.alsalib import AlsaLibGroundTruth
from truth.rsync import RsyncGroundTruth
from truth.dbus import DbusGroundTruth
from truth.dropbear import DropbearGroundTruth
from truth.expat import ExpatGroundTruth
from truth.flac import FlacGroundTruth
from truth.libarchive import LibarchiveGroundTruth
from truth.libpcap import LibpcapGroundTruth
from truth.libssh2 import Libssh2GroundTruth
from truth.libxml2 import Libxml2GroundTruth
from truth.libxslt import LibxsltFeatureTruth
from truth.nano import NanoGroundTruth
from truth.ncurses import NcursesGroundTruth
from truth.pcre2 import Pcre2GroundTruth
from truth.xz import LiblzmaFeatureTruth
from truth.tcpdump import TcpdumpFeatureTruth


    # for project in projects:
    #     log_file = f"{project.name}.log"
    #     # try:
    #     with open(log_file, "w") as f, redirect_stdout(f):

    #         print("*** Running experiment for project:", project.name, "***")
    #         runner = ExperimentRunner(
    #                     build_manager=BuildrootBuildManager(project.build_dir, project.source_dir),
    #                     locator=ConfigLocator(),
    #                     recovery=FlagRecoveryRunner(), 
    #                     truth_extractor=SqliteGroundTruth(),
    #                     comparator=ResultComparator(),
    #                     )
    #         print("Running experiment...")
    #         result = runner.run_project(project)
    #         print(result)
    #     # except Exception as e:
            # print(f"Error processing project {project.name}: {e}")
def run_project_safe(project):
    # try:
    result = run_project(project)
    return {
            "project": project.name,
            "status": "ok",
            "result": result,
    }
    # except Exception as e:
        # return {
            # "project": project.name,
            # "status": "error",
            # "error": str(e),
        # }



def run_project(project):
    log_file = f"{project.name}.log"

        
    groundtruth_map = {
        "libvpx": LibvpxGroundTruth,
        "rsync": RsyncGroundTruth,
        "alsa-lib": AlsaLibGroundTruth,
        "dbus": DbusGroundTruth,
        "drobpear": DropbearGroundTruth,
        "expat": ExpatGroundTruth,
        "flac": FlacGroundTruth,
        "libarchive": LibarchiveGroundTruth,
        "libpcap": LibpcapGroundTruth,
        "libssh2": Libssh2GroundTruth,
        "libxml2": Libxml2GroundTruth,
        "libxslt": LibxsltFeatureTruth,
        "nano": NanoGroundTruth,
        "ncurses": NcursesGroundTruth,
        "pcre2": Pcre2GroundTruth,
        "tcpdump": TcpdumpFeatureTruth,
        "xz": LiblzmaFeatureTruth
        # add more projects here
    }

    # Fallback (optional)
    default_gt = GroundTruthExtractor

    # Select the correct GroundTruth class
    gt_class = groundtruth_map.get(project.name.lower(), default_gt)
 
    # print("This is the gt_class", gt_class)

    with open(log_file, "w") as f, redirect_stdout(f):
        print("*** Running experiment for project:", project.name, "***")

        runner = ExperimentRunner(
            build_manager=BuildrootBuildManager(project.build_dir, project.source_dir),
            locator=ConfigLocator(),
            recovery=FlagRecoveryRunner(),
            truth_extractor=gt_class(), 
            comparator=ResultComparator(),
        )

        print("Running experiment...")
        result = runner.run_project(project)
        print(result)

    return project.name



if __name__ == "__main__":
    projects = [
    # Project(
    #     name = "alsa-lib",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/src/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/include/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/src/.libs/libasound.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/include/config.h"),
    #               "cflags": ""},
    # )
    # # ,
    # Project(
    #     name = "dbus",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus/.libs/libdbus-1.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/config.h"),
    #                "cflags": ""},
    # )
    # ,
    # Project(
    #     name = "dropbear",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2025.88/src"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2025.88/src"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2025.88/dropbearmulti"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2025.88/default_options_guard.h"),
    #               "cflags": ""},
    # )

    # ,
    # Project(
    #     name = "expat",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/lib/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/lib/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/lib/.libs/libexpat.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/expat_config.h"),
    #               "cflags": ""},
    # )    

    # ,
    # Project(
    #     name = "flac",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/src/libFLAC/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/src/libFLAC/include/private/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/src/libFLAC/.libs/libFLAC.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/config.h"),
    #                "cflags": ""},
    # )


    # ,
    # Project(
    #     name = "libpcap",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/libpcap.so.1.10.5"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/config.h"),
    #                "cflags": ""},
    # )  


    # ,
    # Project(
    #     name = "nano",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/src/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/src/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/src/nano"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/config.h"),
    #               "cflags": ""},
    # )  

    # ,
    # Project(
    #     name = "ncurses",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/ncurses/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/ncurses/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/lib/libncurses.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/include/ncurses_cfg.h"),
    #               "cflags":""},
    # )  

   
    
    # ,
    # Project(
    #     name = "pcre2",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/pcre2-10.44/src/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/pcre2-10.44/src/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/pcre2-10.44/.libs/libpcre2-8.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/pcre2-10.44/src/config.h"),
    #                "cflags": ""},
    # )  



    # ,
    # Project(
    #     name = "rsync",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/rsync"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/config.h"),
    #                "cflags": ""
    #               },
    # )  


    # ,
    # Project(
    #     name = "tcpdump",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/tcpdump"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/config.h"),
    #                "cflags": ""
    #               },
    # )  
    # ,
    # Project(
    #     name = "xz",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/src/liblzma/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/src/liblzma/common/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/src/liblzma/.libs/liblzma.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/config.h"),
    #                "cflags": ""}
    # )  

    # ,
    # Project(
    #     name="sqlite",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/sqlite-3.48.0/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/sqlite-3.48.0/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/sqlite-3.48.0/sqlite3"),
    #               "config_h": Path("/workspaces/RevEng/header/libraries/sqlite.h"),
    #               "cflags": "-DSQLITE_ENABLE_FTS5 -DSQLITE_ENABLE_JSON1 -DSQLITE_ENABLE_FTS3 -DSQLITE_ENABLE_STAT4 -DSQLITE_ENABLE_RTREE -DSQLITE_ENABLE_JSON1 -DSQLITE_ENABLE_GEOPOLY -DSQLITE_ENABLE_MATH_FUNCTIONS"
    #               }
    # )

    # ,
    # Project(
    #     name="libxml2",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxml2-2.13.8/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxml2-2.13.8/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxml2-2.13.8/.libs/libxml2.so"),
    #               "config_h": Path("/workspaces/RevEng/header/libraries/libxml2.h"),
    #               "cflags": ""
    #               }
    # )


    # ,
    # Project(
    #     name="libxslt",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxslt-1.1.42/libxslt/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxslt-1.1.42/libxslt/.libs/libxslt.so"),
    #                 "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxslt-1.1.42/config.h"),
    #                 "cflags": ""
    #                 }
    # )   

    # ,
    # Project(
    #     name="libssh2",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libssh2-1.11.0/src/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libssh2-1.11.0/src/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libssh2-1.11.0/src/.libs/libssh2.so"),
    #                 "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libssh2-1.11.0/src/libssh2_config.h"),
    #                 "cflags": ""
    #                 }
    # )   
    # ,


    
    # Project(
    #     name="libvpx",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libvpx-1.15.0/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libvpx-1.15.0"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libvpx-1.15.0/libvpx.so"),
    #                 "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libvpx-1.15.0/vpx_config.h"),
    #                 "cflags": ""
    #                 }
    # ),

    # Project(
    #     name="libarchive",
    #     source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libarchive-3.7.9/libarchive/"),
    #     build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
    #     include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libarchive-3.7.9/libarchive/"),
    #     metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libarchive-3.7.9/.libs/libarchive.so"),
    #               "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libarchive-3.7.9/config.h"),
    #                 "cflags": ''
    #               }
    # )




    ]



    with Pool(processes=10) as p:
        for res in p.imap_unordered(run_project_safe, projects):
            if res["status"] == "ok":
                print(f"✅ {res['project']} done")
            else:
                print(f"❌ {res['project']} failed: {res['error']}")
from pathlib import Path

from core.project import Project
from build.buildroot import BuildrootBuildManager
from locate.config_locator import ConfigLocator
from recovery.runner import FlagRecoveryRunner
from truth.config_truth import GroundTruthExtractor
from evaluation.comparator import ResultComparator
from pipeline.experiment import ExperimentRunner


def main():

    project = Project(
        name = "alsa-lib",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/include/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/src/.libs/libasound.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/alsa-lib-1.2.13/include/config.h")},
    )
    
    project = Project(
        name = "dbus",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus/.libs/libdbus-1.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dbus-1.14.10/dbus/config.h")},
    )
    
    project = Project(
        name = "dropbear",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2020.88/src"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2020.88/src"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2020.88/dropbearmulti"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/dropbear-2020.88/config.h")},
    )

    project = Project(
        name = "expat",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/lib/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/lib/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/lib/.libs/libexpat.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/expat-2.7.1/expat_config.h")},
    )    

    project = Project(
        name = "flac",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/src/libFLAC/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/src/libFLAC/include/private/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/src/libFLAC/.libs/libFLAC.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/flac-1.4.3/config.h")},
    )    

    project = Project(
        name = "jansson",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/jansson-2.14/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/jansson-2.14/src/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/jansson-2.14/src/.libs/libjansson.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/jansson-2.14/jansson_private_config.h")},
    )  

    project = Project(
        name = "libpcap",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/libpcap.so.1.10.5"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcap-1.10.5/config.h")},
    )  

    project = Project(
        name = "librsync",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/librsync-2.3.4/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/librsync-2.3.4/src"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/librsync-2.3.4/librsync.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/librsync-2.3.4/src/config.h")},
    )  

    project = Project(
        name = "libxcrypt",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxcrypt-4.4.38/lib/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxcrypt-4.4.38/lib/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxcrypt-4.4.38/.libs/libcrypt.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libxcrypt-4.4.38/config.h")},
    )  

    project = Project(
        name = "nano",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/src/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/src/nano"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/nano-8.2/config.h")},
    )  

    project = Project(
        name = "ncurses",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/ncurses/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/ncurses/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/lib/libncurses.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ncurses-6.4-20230603/include/ncurses_cfg.h")},
    )  

    project = Project(
        name = "libnftables",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libnftables-1.1.0/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libnftables-1.1.0/include/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libnftables-1.1.0/src/.libs/libnftables.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libnftables-1.1.0/config.h")},
    )  
    
    
    project = Project(
        name = "libpcre2",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcre2-10.44/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcre2-10.44/src/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcre2-10.44/.libs/libpcre2-8.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpcre2-10.44/src/config.h")},
    )  

    project = Project(
        name = "libpopt",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpopt-1.19/src/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpopt-1.19/src/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpopt-1.19/src/.libs/libpopt.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/libpopt-1.19/config.h")},
    )  


    project = Project(
        name = "rsync",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/rsync"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/rsync-3.4.1/config.h")},
    )  


    project = Project(
        name = "tcpdump",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/tcpdump"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/tcpdump-4.99.5/config.h")},
    )  



    project = Project(
        name = "xz",
        source_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/src/liblzma"),
        build_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/"),
        include_dir=Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/src/liblzma/common/"),
        metadata={"binary": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/src/liblzma/.libs/liblzma.so"),
                  "config_h": Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/xz-5.6.4/config.h")},
    )  

    
    print("*** Running experiment for project:", project.name, "***")
    runner = ExperimentRunner(
        build_manager=BuildrootBuildManager(project.build_dir, project.source_dir),
        locator=ConfigLocator(),
        recovery=FlagRecoveryRunner(), 
        truth_extractor=GroundTruthExtractor(),
        comparator=ResultComparator(),
    )
    print("Running experiment...")
    result = runner.run_project(project)
    print(result)


if __name__ == "__main__":
    main()

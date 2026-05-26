import cmd
import subprocess
import time
import os
import re
from pathlib import Path
from typing import List
from truth.config_truth import GroundTruthExtractor
import shutil
from core.project import Project, BuildResult
from build.builderror import BuildErrorPresenceExtractor
from z3.z3 import *

class BuildrootBuildManager:
    """
    Build a single Buildroot package and extract produced binaries.
    """

    def __init__(
        self,
        buildroot_dir: Path,
        output_base: Path,
        timeout: int = 300,
    ):
        self.buildroot_dir = buildroot_dir
        self.output_base = output_base
        self.timeout = timeout
        self.stdout = None
        self.stderr = None
        
    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
    def _run(self, cmd, cwd, log_file: Path, env=None):

        if env is None:
            env = os.environ.copy()


        with log_file.open("a") as f:
            return subprocess.run(
                cmd,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=self.timeout,
                check=False,
                env=env,
            )

    def _ensure_clean_build(self, pkg: str, log_file: Path):
        self._run(
            ["make", pkg + "-dirclean"],
            self.buildroot_dir,
            log_file,
        )


    def _strip_library(self, project, log_file: Path):
        """
        Strip a compiled library using Buildroot's toolchain.
        """

        lib_path = project.metadata["binary"]

        
        
        
            

        strip = f"/workspaces/RevEng/buildroot-2025.02.4/output/host/bin/arm-buildroot-linux-gnueabihf-strip"

        if not lib_path.exists():
            raise FileNotFoundError(f"Library not found: {lib_path}")

        cmd = [str(strip), "--strip-unneeded", str(lib_path)]



        self._run(cmd, self.buildroot_dir, log_file)

        cmd = f"strings {str(lib_path)} >> /workspaces/RevEng/{project.name}_stripped_strings.txt"
        subprocess.run(cmd, shell=True)
        



    def _ensure_defconfig(self, out_dir: Path, log_file: Path):
        if not (out_dir / ".config").exists():
            self._run(
                ["make",  "defconfig"],
                self.buildroot_dir,
                log_file,
            )

    def _discover_binaries(self, target_dir: Path, pkg: str) -> List[Path]:
        
        if not target_dir.exists():
            return []

        pkg_lower = pkg.lower()

        bins = []
        for p in target_dir.rglob("*"):
            try:
                if (
                    p.is_file()
                    and (p.stat().st_mode & 0o111)
                    and pkg_lower in p.name.lower() and ".so" in p.name.lower()
                ):
                    bins.append(p)
            except OSError:
                pass

        return bins

    def _move_stripped_binary_and_config(self, project, log_file: Path, time):
        config_h = project.metadata.get("config_h", None)
        binary = project.metadata.get("binary", None)
        if not config_h or not binary:
            raise ValueError("Missing config_h or binary in project metadata")

        config_h = Path(config_h)
        binary = Path(binary)
        time = str(time)
        # Create a unique output directory per project
        output_dir = log_file.parent / f"{project.name}_{time}_bundle"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Define destination paths
        dst_config = output_dir / config_h.name
        dst_binary = output_dir / binary.name

        # Copy instead of move (preserves metadata like timestamps)
        shutil.copy2(config_h, dst_config)
        shutil.copy2(binary, dst_binary)
        return dst_binary



    def _toggle_post_configure_hooks(self,file_path: Path, uncomment: bool = True):
        """
        Comment or uncomment all lines matching *_POST_CONFIGURE_HOOKS += ...

        :param file_path: Path to the .mk file
        :param uncomment: True -> uncomment, False -> comment
        """
        pattern = re.compile(r'^\s*#?\s*([A-Z0-9_]+_POST_CONFIGURE_HOOKS\s*\+=.*)$')

        lines = file_path.read_text().splitlines()
        new_lines = []

        for line in lines:
            match = pattern.match(line)

            if match:
                content = match.group(1).strip()
                indent = len(line) - len(line.lstrip())

                if uncomment:
                    line = " " * indent + content
                else:
                    line = " " * indent + "# " + content

            new_lines.append(line)

        file_path.write_text("\n".join(new_lines) + "\n")


    def rebuild_with_macros(self, project, gt: GroundTruthExtractor, frr: FlagRecovery, build_res: BuildResult):
        for pc in build_res.error[0].presence_conditions:
            print("Adding negation of presence condition to solver:", pc, type(pc))
            frr.solver.add(Not(pc))
        
        if frr.solver.check() == sat:
            m = frr.solver.model()
            macros = set()
            for ms in m.decls():
                if str(ms).startswith("InBinary"):
                    continue    
                macros.add((str(ms), str(m[ms])))
                print("decl", m[ms], ms)
                
            gt.flags = macros 
            self.build(project, gt)
            return True
        else:
            print("Cannot be compiled we need to install the corresponding libraries")
            return False
    

    # ---------------------------------------------------------
    # main API
    # ---------------------------------------------------------
    def build(self, project: Project, gt: GroundTruthExtractor, iteration=None) -> BuildResult:
        
        pkg = project.name
        
        out_dir = self.buildroot_dir / "output/build/"

        log_file = out_dir / Path("buildroot_" + pkg + ".log")
        
        start = time.time()

        # ensure config
        # self._ensure_defconfig(self.buildroot_dir, log_file)
        self._ensure_clean_build(pkg, log_file)

        # Use random generation of groundtruth 
        # gt.mix()
        print("Ground truth flags for project", project.name, ":", gt.flags)
        # Hook the groundtruth flags into the build environment
        self.write_buildroot_hook_script(gt.flags, "/workspaces/RevEng/support/apply_" + project.name + "_truth.sh", project)

        self._toggle_post_configure_hooks(self.buildroot_dir / "package" / pkg / (pkg + ".mk"), uncomment=True)
        # build the specific package
        cmd = [
            "make",
            f"{pkg}",
        ]

        env = os.environ.copy()

        env["MY_REAL_COMPILER"]=f"{"/workspaces/RevEng/buildroot-2025.02.4/output/host/bin/gcc-13.real"}"
        env["MY_EXTRA_FLAGS"]= gt.mix_cflags(project)
            



        res = self._run(cmd, self.buildroot_dir, log_file, env)
        success = res.returncode == 0
        # success = True
        


        matches = list(out_dir.glob(f"{pkg}-*"))
        # # matches = [Path("/workspaces/RevEng/buildroot-2025.02.4/output/build/ffmpeg-n6.1.2-27-ge16ff06adb/libavcodec")]
        # print("Output dir:", out_dir)
        if not matches:
            raise FileNotFoundError(f"No build dir for {pkg}")
        target_dir = matches[0]

        # self.output_base = target_dir
        dst_binary = None
        # discover binaries
        binaries = self._discover_binaries(target_dir, pkg) if success else []
        if success:
            self._strip_library(project, log_file)
            if iteration == 1:
                dst_binary = self._move_stripped_binary_and_config(project, log_file, time.time())

        self._toggle_post_configure_hooks(self.buildroot_dir / "package" / pkg / (pkg + ".mk"), uncomment=False)

        if not success:
            extractor = BuildErrorPresenceExtractor(
                source_root=project.source_dir,
            )
            error = extractor.parse_log_file(log_file, project.source_dir)



  
        binaries = [project.metadata["binary"], dst_binary]
        duration = time.time() - start
        with log_file.open("a") as f:
            f.write(f"\n=== BUILD TIME: {duration:.2f}s ===\n")
        print(f"Build completed in {duration:.2f} seconds. Success: {success}. Binaries: {binaries}")
        # raise KeyError
        return BuildResult(success=success,
            log_file=log_file,
            binary_paths=binaries,
            error=error if not success else None
        )


    def write_buildroot_hook_script(self, ground_truth_flags, script_path, project):
        """
        Writes a shell script that uses sed to toggle specific macros 
        in the _config.h file.
        """
        with open(script_path, 'w') as f:
            f.write("#!/bin/sh\n")
            f.write("CONFIG_H=\""+ str(project.metadata.get("config_h", "")) +"\"\n")
            f.write("echo \"Updating macros in $CONFIG_H\"\n")

            for macro, value in ground_truth_flags:
                # if value == "True":
                # # Ensure the macro is defined as 1
                #     f.write(f"sed -i 's/.*{macro}.*/#define {macro} 1/' \"$CONFIG_H\"\n")
                # else:
                # # Ensure the macro is undefined/commented out
                #     f.write(f"sed -i 's/.*{macro}.*/#undef {macro}/' \"$CONFIG_H\"\n")
                if value == "True":
                    f.write(
                        f"sed -i 's@^#define[[:space:]]\\+{macro}.*@#define {macro} 1@' \"$CONFIG_H\"\n"
                    )
                    f.write(
                        f"sed -i 's@^/\\* #undef[[:space:]]\\+{macro} \\*/@#define {macro} 1@' \"$CONFIG_H\"\n"
                    )
                else:
                    f.write(
                        f"sed -i 's@^#define[[:space:]]\\+{macro}.*@/* #undef {macro} */@' \"$CONFIG_H\"\n"
                    )


        os.chmod(script_path, 0o755)


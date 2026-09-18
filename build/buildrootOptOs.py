from .buildroot import BuildrootBuildManager
from pathlib import Path
from .buildroot import *

class BuildrootOptOs(BuildrootBuildManager):
    def __init__(self, buildroot_dir, output_base, timeout = 300):
        super().__init__(buildroot_dir, output_base, timeout)
        self.optimization_level: str = "Os"

    def build(self, project: Project, gt: GroundTruthExtractor, iteration=None) -> BuildResult:
        pkg = project.name
        buildroot_dir = self.buildroot_dir
        if iteration == 1:
            self.buildroot_dir = Path("/workspaces/RevEng/buildroot-opt-Os/")
        
        out_dir = self.buildroot_dir / "output/build/"
        log_file = out_dir / Path("buildroot_" + pkg + ".log")

        start = time.time()

        config = project.metadata["config_h"]
        relative = config.relative_to(buildroot_dir)

        binary = project.metadata["binary"]
        relative_b = binary.relative_to(buildroot_dir)

        project.metadata["config_h"] = self.buildroot_dir / relative
        project.metadata["binary"] = self.buildroot_dir / relative_b
        # ensure config
        # self._ensure_defconfig(self.buildroot_dir, log_file)
        self._ensure_clean_build(pkg, log_file)

        # Use random generation of groundtruth
        # gt.mix()
        print("Ground truth flags for project", project.name, ":", gt.flags)

        # Hook the groundtruth flags into the build environment
        if project.name == "libopenssl":
            self.write_buildroot_hook_script_libopenssl(gt.flags, "/workspaces/RevEng/support/apply_" + project.name + "_truth.sh", project)
        elif project.name == "libxml2":
            self.write_buildroot_hook_script_libxml2(gt.flags, "/workspaces/RevEng/support/apply_" + project.name + "_truth.sh", project)
        else:
            self.write_buildroot_hook_script(gt.flags, "/workspaces/RevEng/support/apply_" + project.name + "_truth.sh", project)

        self._toggle_post_configure_hooks(self.buildroot_dir / "package" / pkg / (pkg + ".mk"), uncomment=True)

        # build the specific package
        cmd = [
            "make",
            f"{pkg}",
        ]

        env = os.environ.copy()
        env["MY_REAL_COMPILER"] = "/workspaces/RevEng/buildroot-2025.02.4/output/host/bin/gcc-13.real"
        env["MY_EXTRA_FLAGS"] = gt.mix_cflags(project)
        env["SOURCE_DATE_EPOCH"] = "1704067200"

        res = self._run(cmd, self.buildroot_dir, log_file, env)
        success = res.returncode == 0

        if not success:
            raise KeyError
        project.metadata["config_h"] = config

        matches = list(out_dir.glob(f"{pkg}-*"))
        if not matches:
            raise FileNotFoundError(f"No build dir for {pkg}")
        target_dir = matches[0]
        output_dir = None
        dst_binary = None
        binaries = self._discover_binaries(target_dir, pkg) if success else []
        if success:
            self._strip_library(project, log_file)
            if iteration == 1:
                output_dir = self._move_stripped_binary_and_config(project, log_file, time.time())
                self.bundle = output_dir
            dst_binary = self.bundle / "final_binary"
            shutil.copy2(project.metadata["binary"], dst_binary)

        self._toggle_post_configure_hooks(self.buildroot_dir / "package" / pkg / (pkg + ".mk"), uncomment=False)

        # os.remove(project.metadata.get("config_h", None))
        binaries = [project.metadata["binary"], dst_binary]
        duration = time.time() - start
        project.metadata["binary"] = binary
        with log_file.open("a") as f:
            f.write(f"\n=== BUILD TIME: {duration:.2f}s ===\n")

        print(f"Build completed in {duration:.2f} seconds. Success: {success}. Binaries: {binaries}")
        self.buildroot_dir = buildroot_dir

        return BuildResult(
            success=success,
            log_file=log_file,
            binary_paths=binaries,
            error="Rebuild Macros" if not success and iteration > 1 else None,
        )
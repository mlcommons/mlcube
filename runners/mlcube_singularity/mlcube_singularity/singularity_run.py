import logging
import typing as t
from pathlib import Path
from omegaconf import DictConfig, OmegaConf
import semver
from spython.utils.terminal import (
    get_singularity_version_info,
    check_install as check_singularity_installed,
)
from mlcube.errors import (ConfigurationError, ExecutionError)
from mlcube.shell import Shell
from mlcube.runner import Runner, RunnerConfig


__all__ = ["Config", "SingularityRun"]

from mlcube.validate import Validate

logger = logging.getLogger(__name__)


class Config(RunnerConfig):
    """Helper class to manage `singularity` environment configuration."""

    DEFAULT = OmegaConf.create(
        {
            "runner": "singularity",  # Name of this runner.
            "image": "${singularity.image}",  # Path to Singularity image, relative to ${image_dir}.
            "image_dir": "${runtime.workspace}/.image",  # Root image directory for the image.
            "singularity": "singularity",  # Executable file for singularity runtime.
            "build_args": "--fakeroot",  # Image build arguments.
            "run_args": "",  # Container run arguments, example: -C --net.
            # Sergey: there seems to be a better name for this parameter. Originally, the only source was a singularity
            # recipe (build file). Later, MLCube started to support other sources, such as docker images.
            "build_file": "Singularity.recipe",  # Source for the image build process.
            "--network": None,  # Networking options defined during MLCube container execution.
            "--security": None,  # Security options defined during MLCube container execution.
            "--nv": None,  # usage options defined during MLCube container execution.
            "--vm-ram": None,  # RAM options defined during MLCube container execution.
            "--vm-cpu": None  # CPU options defined during MLCube container execution.
        }
    )

    @staticmethod
    def merge(mlcube: DictConfig) -> None:
        """Merge current (mostly default) configuration with configuration from MLCube yaml file.
        Args:
            mlcube: Current MLCube configuration. Contains all fields from MLCube configuration file (YAML) including
                platform-specific configuration sections (docker/singularity). In addition, this dictionary contains
                'runtime' configuration (`root` and `workspace`), and `runner` configuration that contains default
                runner configuration (Singularity in this case) from system settings file (it is exact or modified
                version of `Config.DEFAULT` dictionary to account for user local environment).
        Idea is that if mlcube contains `singularity` section, then it means that we use it as is. Else, we can try
        to run this MLCube using information from `docker` section if it exists.
        """
        # The `runner` section will contain effective runner configuration. At this point, it may contain configuration
        # from system settings file.
        if 'runner' not in mlcube:
            mlcube['runner'] = {}

        # We need to merge with the user-provided configuration.
        s_cfg: t.Optional[DictConfig] = mlcube.get("singularity", None)
        if not s_cfg:
            # Singularity runner will try to use docker section. At this point, it will work as long as we assume we
            # pull docker images from a docker hub.
            logger.warning(
                "SingularityRun singularity configuration not found in MLCube file (singularity=%s).",
                str(s_cfg),
            )

            d_cfg = mlcube.get("docker", None)
            if not d_cfg:
                logger.warning(
                    "SingularityRun docker configuration not found too. Singularity runner will likely "
                    "fail to run."
                )
                return

            # The idea is that we can use the remote docker image as a source for the build process, automatically
            # generating an image name in a local environment. Key here is that the source has a scheme - `docker://`
            # The --fakeroot switch is useful and is supported in singularity version >= 3.5
            build_args = ""
            # There's no `singularity` section, so we do not know what singularity executable to use. Let's assume
            # it's just `singularity`.
            singularity = "singularity"
            try:
                SingularityRun.check_install(singularity)
                version: semver.VersionInfo = get_singularity_version_info()
                logger.info("SingularityRun singularity version %s", str(version))
                if version >= semver.VersionInfo(major=3, minor=5):
                    logger.info(
                        "SingularityRun will use --fakeroot CLI switch (version >= 3.5)."
                    )
                    build_args = "--fakeroot"
                else:
                    logger.warning(
                        "SingularityRun will not use --fakeroot CLI switch (version < 3.5)"
                    )
            except Exception as err:
                logger.warning(
                    "SingularityRun can't get singularity version (do you have singularity installed?). "
                    "Source=Config.merge. Exception=%s", str(err), exc_info=True
                )

            build_file = "docker://" + d_cfg["image"]
            if "tar_file" in d_cfg:
                build_file = "docker-archive:" + d_cfg["tar_file"]
            run_args = d_cfg.get("run_args", "")
            s_cfg = OmegaConf.create(
                dict(
                    image="".join(c for c in d_cfg["image"] if c.isalnum()) + ".sif",
                    build_file=build_file,
                    build_args=build_args,
                    run_args=run_args,
                    singularity=singularity,
                )
            )
            logger.info(
                f"SingularityRun singularity runner has converted docker configuration to singularity (%s).",
                str(OmegaConf.to_container(s_cfg)),
            )

        mlcube.runner = OmegaConf.merge(mlcube.runner, s_cfg)

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        validator = Validate(mlcube.runner, "runner")
        validator.check_unknown_keys(Config.DEFAULT.keys()).check_values(
            ["image", "image_dir", "singularity"], str, blanks=False
        )


class SingularityRun(Runner):

    CONFIG = Config

    @staticmethod
    def check_install(singularity_exec: str = "singularity") -> None:
        if not check_singularity_installed(software=singularity_exec):
            raise ExecutionError(
                f"{SingularityRun.__name__} runner failed to configure or to run MLCube.",
                "SingularityRun check_install returned false ('singularity --version' failed to run). MLCube cannot "
                "run singularity images unless this check passes. Singularity runner uses `check_install` function "
                "from singularity-cli python library (https://github.com/singularityhub/singularity-cli).",
                function='check_singularity_installed',
                args={'software': singularity_exec}
            )

    def _get_extra_args(self) -> str:
        """Temporary solution to take into account run arguments provided by users."""
        # Collect all parameters that start with '--' and have a non-None value.
        extra_args = [
            f'{key}={value}' for key, value in self.mlcube.runner.items() if key.startswith('--') and value is not None
        ]
        return ' '.join(extra_args)

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Optional[str]) -> None:
        super().__init__(mlcube, task)
        if self.mlcube.runner.singularity != 'singularity':
            logger.warning(
                "Singularity executable is not exactly 'singularity' (singularity=%s). The MLCube singularity runner "
                "will use this executable, however the version of the `spython` library that the runner uses (which is "
                "`0.2.1`) does not allow specifying a custom singularity executable when checking the singularity "
                "version. It's OK if `singularity` resolves to` %s`, in other cases this may cause issues.",
                self.mlcube.runner.singularity, self.mlcube.runner.singularity
            )
        try:
            # Check version and log a warning message if fakeroot is used with singularity version < 3.5
            version: semver.VersionInfo = get_singularity_version_info()
            logger.info("SingularityRun singularity version = %s", str(version))
            if version < semver.VersionInfo(major=3, minor=5) and "--fakeroot" in (
                self.mlcube.runner.build_args or ""
            ):
                logger.warning(
                    "SingularityRun singularity version < 3.5, and it probably does not support --fakeroot "
                    "parameter that is present in MLCube configuration."
                )
        except Exception as err:
            # It's correct to use `singularity` here, since the function that identifies the singularity version
            # does not allow specifying a custom singularity executable (at least in spython == 0.2.1).
            ver_cmd = f"singularity --version"
            try:
                self.check_install(self.mlcube.runner.singularity)
                msg = "The runner has been able to successfully run the singularity executable (which is "\
                      f"`{self.mlcube.runner.singularity}`). Most likely, the output of `{ver_cmd}` could not be "\
                      "parsed. Please, create an issue in MLCube repository and provide the output of "\
                      f"this command ({ver_cmd})"
            except:
                # And here we use the correct executable, since check_install supports user-provided executable.
                msg = f"The runner has not been able to run this command (`{self.mlcube.runner.singularity} --help`)." \
                      f"Please check that this executable is in PATH, or specify a custom path in ~/mlcube.yaml."
            logger.warning(
                "Singularity runner (cmd=%s) can't detect singularity version. %s. "
                "Source=SingularityRun.__init__. Exception=%s.", ver_cmd, msg, str(err), exc_info=True
            )

    def configure(self) -> None:
        """Build Singularity Image on a current host."""
        SingularityRun.check_install(self.mlcube.runner.singularity)

        s_cfg: DictConfig = self.mlcube.runner

        # Get full path to a singularity image. By design, we compute it relative to {mlcube.root}/workspace.
        image_file = Path(s_cfg.image_dir, s_cfg.image)
        if image_file.exists():
            logger.info(
                "SingularityRun SIF exists (%s) - no need to run the configure step.",
                image_file,
            )
            return

        # Make sure a directory to store image exists. If paths are like "/opt/...", the call may fail.
        image_file.parent.mkdir(parents=True, exist_ok=True)

        build_path = Path(
            self.mlcube.runtime.root
        )  # Let's assume that build context is the root MLCube directory
        recipe: str = s_cfg.build_file  # This is the recipe file, or docker image.
        if recipe.startswith("docker://") or recipe.startswith("docker-archive:"):
            # https://sylabs.io/guides/3.0/user-guide/build_a_container.html
            # URI beginning with docker:// to build from Docker Hub
            logger.info("SingularityRun building SIF from docker image (%s).", recipe)
        else:
            # This must be a recipe file. Make sure it exists.
            if not Path(build_path, recipe).exists():
                raise IOError(f"SIF recipe file does not exist (path={build_path}, file={recipe})")
            logger.info("Building SIF from recipe file (path=%s, file=%s).", build_path, recipe)
        try:
            Shell.run([
                'cd', str(build_path), ';', s_cfg.singularity, 'build', s_cfg.build_args, str(image_file), recipe
            ])
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Error occurred while building SIF image. See context for more details.",
                **err.context
            )

    def run(self) -> None:
        """ """
        image_file = Path(self.mlcube.runner.image_dir) / self.mlcube.runner.image
        if not image_file.exists():
            self.configure()
        else:
            SingularityRun.check_install(self.mlcube.runner.singularity)

        # Deal with user-provided workspace
        try:
            Shell.sync_workspace(self.mlcube, self.task)
        except Exception as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "Error occurred while syncing MLCube workspace. See context for more details.",
                error=str(err)
            )

        try:
            # The `task_args` list of strings contains task name at the first position.
            mounts, task_args, mounts_opts = Shell.generate_mounts_and_args(self.mlcube, self.task)
            if mounts_opts:
                for key, value in mounts_opts.items():
                    mounts[key]+=f':{value}'
            logger.info(f"mounts={mounts}, task_args={task_args}")
        except ConfigurationError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "Error occurred while generating mount points for singularity run command. See context for more "
                "details and check your MLCube configuration file.",
                error=str(err)
            )

        volumes = Shell.to_cli_args(mounts, sep=":", parent_arg="--bind")
        print(OmegaConf.to_container(self.mlcube.runner))
        run_args = self.mlcube.runner.run_args

        # Temporary solution
        extra_args = self._get_extra_args()
        if extra_args:
            run_args += " " + extra_args

        try:
            entrypoint: t.Optional[str] = self.mlcube.tasks[self.task].get('entrypoint', None)
            if entrypoint:
                logger.info(
                    "Using custom task entrypoint: task=%s, entrypoint='%s'",
                    self.task, self.mlcube.tasks[self.task].entrypoint
                )
                Shell.run([self.mlcube.runner.singularity, 'exec', run_args, volumes,
                           str(image_file), entrypoint, ' '.join(task_args[1:])])
            else:
                Shell.run([
                    self.mlcube.runner.singularity, 'run', run_args, volumes,
                    str(image_file), ' '.join(task_args)
                ])
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task (task={self.task}). See context for more details.",
                **err.context
            )

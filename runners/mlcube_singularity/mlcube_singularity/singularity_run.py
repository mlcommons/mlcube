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
            try:
                SingularityRun.check_install()
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
            except:
                logger.warning(
                    "SingularityRun can't get singularity version (do you have singularity installed?)."
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
                    singularity="singularity",
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
                "from singularity-cli python library (https://github.com/singularityhub/singularity-cli)."
            )

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: str) -> None:
        super().__init__(mlcube, task)
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
        except:
            logger.warning(
                "SingularityRun can't get singularity version (do you have singularity installed?)."
            )

    def configure(self) -> None:
        """Build Singularity Image on a current host."""
        SingularityRun.check_install()

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
            SingularityRun.check_install()

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
            mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
            logger.info(f"mounts={mounts}, task_args={task_args}")
        except ConfigurationError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "Error occurred while generating mount points for singularity run command. See context for more "
                "details and check your MLCube configuration file.",
                error=str(err)
            )

        volumes = Shell.to_cli_args(mounts, sep=":", parent_arg="--bind")
        try:
            Shell.run([self.mlcube.runner.singularity, 'run', volumes, str(image_file), ' '.join(task_args)])
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task (task={self.task}). See context for more details.",
                **err.context
            )

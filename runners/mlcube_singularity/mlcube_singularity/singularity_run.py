import logging
import typing as t
from pathlib import Path

from mlcube_singularity.singularity_client import Client
from omegaconf import DictConfig, OmegaConf

from mlcube.errors import ConfigurationError, ExecutionError
from mlcube.runner import Runner, RunnerConfig
from mlcube.shell import Shell
from mlcube.validate import Validate

__all__ = ["Config", "SingularityRun"]

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
            "--vm-cpu": None,  # CPU options defined during MLCube container execution.
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
        if "runner" not in mlcube:
            mlcube["runner"] = {}

        # We need to merge with the user-provided configuration.
        s_cfg: t.Optional[DictConfig] = mlcube.get("singularity", None)
        if not s_cfg:
            # Singularity runner will try to use docker section. At this point, it will work as long as we assume we
            # pull docker images from a docker hub.
            logger.warning(
                "Config.merge singularity configuration not found in MLCube file (singularity=%s).",
                str(s_cfg),
            )

            d_cfg = mlcube.get("docker", None)
            if not d_cfg:
                logger.warning(
                    "Config.merge docker configuration not found too. Singularity runner will likely "
                    "fail to run."
                )
                return

            # The idea is that we can use the remote docker image as a source for the build process, automatically
            # generating an image name in a local environment. Key here is that the source has a scheme - `docker://`
            # The --fakeroot switch is useful and is supported in singularity version >= 3.5
            build_args = ""
            # There's no `singularity` section, so we do not know what singularity executable to use. Several options
            # that we have: look at system settings file, check for singularity, check for apptainer, check for
            # sudo singularity, check for sudo apptainer.
            # Let's assume
            # it's just `singularity`.
            client = Client.from_env()
            if client.supports_fakeroot():
                logger.info(
                    "Config.merge will use --fakeroot CLI switch (CLI client seems to be supporting it)."
                )
                build_args = "--fakeroot"
            else:
                logger.warning(
                    "Config.merge will not use --fakeroot CLI switch (CLI client too old or version unknown)"
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
                    singularity=" ".join(client.singularity),
                )
            )
            logger.info(
                f"Config.merge singularity runner has converted docker configuration to singularity (%s).",
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

    def _get_extra_args(self) -> str:
        """Temporary solution to take into account run arguments provided by users."""
        # Collect all parameters that start with '--' and have a non-None value.
        extra_args = [
            f"{key}={value}"
            for key, value in self.mlcube.runner.items()
            if key.startswith("--") and value is not None
        ]
        return " ".join(extra_args)

    def __init__(
        self, mlcube: t.Union[DictConfig, t.Dict], task: t.Optional[str]
    ) -> None:
        super().__init__(mlcube, task)
        self.client = Client(self.mlcube.runner.singularity)

        # Check version and log a warning message if fakeroot is used with singularity version < 3.5
        if not self.client.supports_fakeroot() and "--fakeroot" in (
            self.mlcube.runner.build_args or ""
        ):
            logger.warning(
                "SingularityRun.__init__ singularity runtime (exec=%s, version=%s) does not probably "
                "support --fakeroot parameter that is present in MLCube configuration.",
                self.client.singularity,
                self.client.version,
            )

    def configure(self) -> None:
        """Build Singularity Image on a current host."""
        s_cfg: DictConfig = self.mlcube.runner
        self.client.build(
            self.mlcube.runtime.root,
            s_cfg.build_file,
            s_cfg.image_dir,
            s_cfg.image,
            s_cfg.build_args,
        )

    def run(self) -> None:
        """ """
        image_file = Path(self.mlcube.runner.image_dir) / self.mlcube.runner.image
        if not image_file.exists():
            self.configure()

        # Deal with user-provided workspace
        try:
            Shell.sync_workspace(self.mlcube, self.task)
        except Exception as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "Error occurred while syncing MLCube workspace. See context for more details.",
                error=str(err),
            )

        try:
            # The `task_args` list of strings contains task name at the first position.
            mounts, task_args, mounts_opts = Shell.generate_mounts_and_args(
                self.mlcube, self.task
            )
            if mounts_opts:
                for key, value in mounts_opts.items():
                    mounts[key] += f":{value}"
            logger.info(
                f"SingularityRun.run mounts=%s, task_args=%s", mounts, task_args
            )
        except ConfigurationError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "Error occurred while generating mount points for singularity run command. See context for more "
                "details and check your MLCube configuration file.",
                error=str(err),
            )

        volumes = Shell.to_cli_args(mounts, sep=":", parent_arg="--bind")
        run_args = self.mlcube.runner.run_args

        # Temporary solution
        extra_args = self._get_extra_args()
        if extra_args:
            run_args += " " + extra_args

        entrypoint: t.Optional[str] = self.mlcube.tasks[self.task].get(
            "entrypoint", None
        )
        if entrypoint:
            logger.info(
                "SingularityRun.run found custom task entrypoint: task=%s, entrypoint='%s'",
                self.task,
                self.mlcube.tasks[self.task].entrypoint,
            )
            # By contract, custom entry points do not accept task name as the first argument.
            task_args = task_args[1:]
        self.client.run(run_args, volumes, str(image_file), task_args, entrypoint)

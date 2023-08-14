import logging
import typing as t
from pathlib import Path

from mlcube_singularity.singularity_client import Client, DockerHubClient
from omegaconf import DictConfig, OmegaConf

from mlcube.errors import ConfigurationError, ExecutionError, MLCubeError
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
            "--mount_opts": "",  # Mount options for Singularity volumes.
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
            if key.startswith("--") and value is not None and key != "--mount_opts"
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
            build_dir=self.mlcube.runtime.root,
            recipe=s_cfg.build_file,
            image_dir=s_cfg.image_dir,
            image_name=s_cfg.image,
            build_args=s_cfg.build_args,
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

    def inspect(self, force: bool = False) -> t.Dict:
        s_cfg: DictConfig = self.mlcube.runner
        image_file = Path(s_cfg.image_dir, s_cfg.image)

        def _local_file_sha256sum(file_path: Path) -> str:
            """Compute sha256 hash sum of the local file."""
            _exit_code, _output = Shell.run_and_capture_output(
                ["sha256sum", file_path.as_posix()]
            )
            if _exit_code != 0:
                _output = _output.replace("\n", " ")
                raise MLCubeError(
                    f"SingularityRun.inspect failed to compute sha256 sum of the local file. File={file_path}, "
                    f"sha256sum_exitcode={_exit_code}, sha256sum_output={_output}"
                )
            return _output.split(" ")[0].strip()

        if not s_cfg.build_file:
            # The build specs do not exist. This probably means that the SIF file must exist.
            if not image_file.is_file():
                raise MLCubeError(
                    "The build file (build_file) that specifies how a SIF image is to be built is not specified or "
                    "empty. This means the SIF image must exist (image_dir=%s, image_name=%s) but it does not. "
                    "Inspection failed.",
                    s_cfg.image_dir,
                    s_cfg.image,
                )
            logger.debug(
                "SingularityRun.inspect: build file (%s) is not specified, but SIF image exists (%s) - will use it to "
                "compute hash.",
                s_cfg.build_file,
                image_file.as_posix(),
            )
            return {"hash": _local_file_sha256sum(image_file)}

        if s_cfg.build_file.startswith("docker-archive:"):
            # MLCube is distributed as docker save image (tar archive): I (sergey) guess we need to recover ID of the
            # original docker image from the tar archive.
            raise MLCubeError(
                "SingularityRun.inspect: docker archives not supported yet."
            )

        if s_cfg.build_file.startswith("docker:"):
            # MLCube is distributed as docker image: need to identify image ID of this image by querying the docker
            # registry (docker hub).
            # TODO: Current implementation makes an API call to docker registry. It's quite possible that the next call
            #       (e.g., configure) will pull a newer version of this image. Need to address this in subsequent
            #       patches.
            docker_hub = DockerHubClient(self.client)
            manifest = docker_hub.get_manifest(s_cfg.build_file)
            logger.debug(
                "SingularityRun.inspect build file is a docker image (%s) - I will consider it as a distribution "
                "format for this MLCube, and MLCube hash will be docker image ID. Image manifest: %s",
                s_cfg.build_file,
                manifest,
            )
            return {"hash": manifest["config"]["digest"][7:]}

        # Here, the recipe file (s_cfg.build_file) must point to a singularity image file. Is there an easy way to
        # validate it here?
        recipe_file = Path(self.mlcube.runtime.root, s_cfg.build_file)
        if not recipe_file.is_file():
            raise MLCubeError(
                f"SingularityRun.inspect: the build file ({s_cfg.build_file}) is specified, and it is assumed it is a "
                f"singularity definition file, but it does not exist ({recipe_file.as_posix()}). Can't identify how "
                "this MLCube is distributed."
            )

        if not image_file.is_file():
            if not force:
                raise MLCubeError(
                    f"SingularityRun.inspect: SIF image file does not exist ({image_file}), but build recipe file "
                    f"exist ({recipe_file}). It is assumed that this MLCube is distributed as a singularity image, and "
                    "I need this image to identify its hash, but `force` parameter is set to false. Configure this "
                    "MLCube or set this parameter to true (e.g., rerun inspect command with `--force` CLi switch)."
                )
            logger.debug(
                "SingularityRun.inspect build recipe file exists (%s), SIF image file does not exist (%s), and `force` "
                "parameter is set to true - will build SIF image and will use it to compute hash.",
                recipe_file.as_posix(),
                image_file.as_posix(),
            )
            self.configure()
        else:
            logger.debug(
                "SingularityRun.inspect: build file (%s) is specified, build recipe exists (%s), SIF image exists (%s) "
                "- will use it to compute hash.",
                s_cfg.build_file,
                recipe_file.as_posix(),
                image_file.as_posix(),
            )
        return {"hash": _local_file_sha256sum(image_file)}

import logging
import typing as t
from enum import Enum
from pathlib import Path

import semver

from mlcube.errors import ExecutionError
from mlcube.shell import Shell
from mlcube.system_settings import SystemSettings

__all__ = ["Runtime", "Version", "Client"]

logger = logging.getLogger(__name__)


class Runtime(Enum):
    """Container runtime"""

    UNKNOWN = 0
    APPTAINER = 1
    SINGULARITY = 2


class Version:
    def __init__(self, runtime: Runtime, version: semver.VersionInfo) -> None:
        self.runtime = runtime
        self.version = version

    def __str__(self) -> str:
        return f"Version(runtime={self.runtime.name}, version={self.version})"


class Client:
    """Singularity container platform client.

    Args:
        singularity: A shell command to run singularity. When it's string, it needs to be constructed so that splitting
        using space character resulted in correct sequence of commands and arguments.
    """

    @classmethod
    def from_env(cls) -> "Client":
        # Check if system settings file contains information about singularity.
        executables = ["singularity", "sudo singularity", "apptainer", "sudo apptainer"]

        system_settings = SystemSettings()
        if "singularity" in system_settings.platforms:
            executables = [
                system_settings.platforms["singularity"]["singularity"]
            ] + executables
            logger.info(
                "Client.from_env found singularity platform config in MLCube system settings file "
                "(file=%s, platform=%s). Will try it first for detecting singularity CLI client.",
                system_settings.path.as_posix(),
                system_settings.platforms["singularity"],
            )
        logger.debug(
            "Client.from_env will try candidate executables in the following order "
            "(first available will be selected): %s",
            executables,
        )

        for executable in executables:
            try:
                client = Client(executable)
                logger.info(
                    "Client.from_env found singularity (exec=%s, version=%s)",
                    client.singularity,
                    client.version,
                )
                return client
            except ExecutionError:
                logger.warning(
                    "Client.from_env failed to run singularity as: %s", executable
                )
                continue

        raise ExecutionError(
            f"Failed to identify proper singularity client. I tried the following: {executables}."
        )

    def supports_fakeroot(self) -> bool:
        singularity_35 = (
            self.version.runtime == Runtime.SINGULARITY
            and self.version >= semver.VersionInfo(major=3, minor=5)
        )
        apptainer = self.version.runtime == Runtime.APPTAINER
        return singularity_35 or apptainer

    def __init__(self, singularity: t.Union[str, t.List]) -> None:
        if isinstance(singularity, str):
            singularity = singularity.split(" ")
        self.singularity: t.List[str] = [c.strip() for c in singularity if c.strip()]
        self.version: t.Optional[Version] = None
        self.init()
        logger.debug(
            "Client.__init__ executable=%s, version=%s", self.singularity, self.version
        )

    def init(self, force: bool = False) -> None:
        if force:
            self.version = None
        if self.version is None:
            version_cmd = self.singularity + ["--version"]
            exit_code, version_string = Shell.run_and_capture_output(version_cmd)
            if exit_code != 0:
                raise ExecutionError(
                    f"Singularity client failed to initialize. The following command ({version_cmd}) returned non-zero"
                    f"exit code ({exit_code}). MLCube cannot run singularity images unless this check passes.",
                    function=f"{self.__class__}.init",
                    args={
                        "force": force,
                        "singularity": self.singularity,
                        "version_cmd": version_cmd,
                    },
                )

            if version_string.startswith("singularity version "):
                runtime, version_string = (
                    Runtime.SINGULARITY,
                    version_string[20:].strip(),
                )
            elif version_string.startswith("apptainer version "):
                runtime, version_string = Runtime.APPTAINER, version_string[18:].strip()
            elif "/" in version_string:  # Handle old stuff like "x.y.z-pull/123-0a5d"
                runtime, version_string = Runtime.SINGULARITY, version_string.replace(
                    "/", "+", 1
                )
            else:
                logger.warning(
                    "Client.init unrecognized container runtime (version_string: %s)",
                    version_string,
                )
                runtime = Runtime.UNKNOWN
            self.version = Version(runtime, semver.VersionInfo.parse(version_string))
            logger.debug("Client.init version=%s", self.version)

    def build(
        self,
        build_dir: str,
        recipe: str,
        image_dir: str,
        image_name: str,
        build_args: str,
    ) -> None:
        # Get full path to a singularity image. By design, we compute it relative to {mlcube.root}/workspace.
        image_file = Path(image_dir, image_name)
        if image_file.exists():
            logger.info(
                "Client.build won't build SIF image (file exists: %s).",
                image_file,
            )
            return

        # Make sure a directory to store image exists. If paths are like "/opt/...", the call may fail.
        image_file.parent.mkdir(parents=True, exist_ok=True)

        build_dir = Path(
            build_dir
        )  # Let's assume that build context is the root MLCube directory
        if recipe.startswith("docker://") or recipe.startswith("docker-archive:"):
            # https://sylabs.io/guides/3.0/user-guide/build_a_container.html
            # URI beginning with docker:// to build from Docker Hub
            logger.info(
                "Client.build will build SIF image from docker image (image=%s).",
                recipe,
            )
        else:
            # This must be a recipe file. Make sure it exists.
            if not Path(build_dir, recipe).exists():
                raise IOError(
                    f"SIF recipe file does not exist (path={build_dir}, file={recipe})"
                )
            logger.info(
                "Client.build will build SIF image from recipe file (path=%s, file=%s).",
                build_dir,
                recipe,
            )
        try:
            Shell.run(
                ["cd", str(build_dir), ";"]
                + self.singularity
                + ["build", build_args, str(image_file), recipe]
            )
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Error occurred while building SIF image. See context for more details.",
                **err.context,
            )

    def run(
        self,
        run_args: str,
        volumes: str,
        image_file: str,
        args: t.List,
        entrypoint: t.Optional[str] = None,
    ) -> None:
        try:
            if entrypoint:
                Shell.run(
                    self.singularity
                    + [
                        "exec",
                        run_args,
                        volumes,
                        image_file,
                        entrypoint,
                        " ".join(args),
                    ]
                )
            else:
                Shell.run(
                    self.singularity
                    + ["run", run_args, volumes, image_file, " ".join(args)]
                )
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task. See context for more details.",
                **err.context,
            )

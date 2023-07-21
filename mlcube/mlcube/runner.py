"""This module provides the base class for all Python-based MLCube runners.

- `RunnerConfig`: Base class to manage runners' configurations.
- `Runner`: Base class for all Python-based reference MLCube runners.
"""
import logging
import typing as t

from omegaconf import DictConfig, OmegaConf

from mlcube.errors import ConfigurationError, MLCubeError

__all__ = ["RunnerConfig", "Runner"]


logger = logging.getLogger(__name__)


class RunnerConfig(object):
    """Base class to manage runners' default configurations."""

    DEFAULT = {}
    """Dictionary containing runner's default configuration parameters and their values."""

    @staticmethod
    def merge(mlcube: DictConfig) -> None:
        """Merge default MLCube runner configuration with user-provided configuration.

        Args:
            mlcube: The whole MLCube configuration.

        A default behavior would be to update the `runner` section (containing the default configuration) with runner
        specific section. The implementation for docker runner can look like this:

        ```python
        mlcube.runner = OmegaConf.merge(mlcube.runner, mlcube.get('docker', OmegaConf.create({})))
        ```

        Look at Singularity runner's implementation for more complex logic that might be required for some runners.
        """
        ...

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        """Validate if runner configuration is correct.

        Args:
            mlcube: The whole MLCube configuration. This method most likely needs to validate `mlcube.runner` section.

        If this validation passes, i.e., not exceptions are raised, it is assumed that corresponding MLCube runner can
        use this configuration to run this MLCube.
        """
        ...


RunnerConfigType = t.TypeVar("RunnerConfigType", bound="RunnerConfig")


class Runner(object):
    """Base MLCube runner."""

    CONFIG: RunnerConfigType = RunnerConfig

    def __init__(
        self, mlcube: t.Union[DictConfig, t.Dict], task: t.Optional[str]
    ) -> None:
        """Initialize the base runner.

        Args:
            mlcube: MLCube configuration.
            task: Task name to run.
        """
        if isinstance(mlcube, dict):
            mlcube: DictConfig = OmegaConf.create(mlcube)
        if not isinstance(mlcube, DictConfig):
            raise ConfigurationError(
                f"Invalid mlcube type ('{type(DictConfig)}'). Expecting 'DictConfig'."
            )

        self.mlcube = mlcube
        self.task = task

        logger.debug(
            "%s.__init__ configuration: %s",
            self.__class__.__name__,
            str(self.mlcube.runner),
        )

    def configure(self) -> None:
        """Configure this MLCube."""
        ...

    def run(self) -> None:
        """Run one MLCube task."""
        ...

    def inspect(self, force: bool = False) -> t.Dict:
        """Return low-level information about MLCube objects.

        Args:
            force: If true, and MLCube does not exist (e.g., has not been pulled or built yet), then pull/build it.
        """
        raise MLCubeError(
            f"The `inspect` command has not been implemented yet (runner={self.mlcube['runner']['runner']}, "
            f"cls={self.__class__.__name__})."
        )

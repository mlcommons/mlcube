import logging
import typing as t
from mlcube.errors import ConfigurationError
from omegaconf import (OmegaConf, DictConfig)


__all__ = ['RunnerConfig', 'Runner']


logger = logging.getLogger(__name__)


class RunnerConfig(object):

    DEFAULT = {}

    @staticmethod
    def merge(mlcube: DictConfig) -> None:
        ...

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        ...


RunnerConfigType = t.TypeVar('RunnerConfigType', bound='RunnerConfig')


class Runner(object):
    """ Base MLCube runner """

    CONFIG: RunnerConfigType = RunnerConfig

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Optional[t.Text]) -> None:
        """Base runner.
        Args:
            mlcube: MLCube configuration.
            task: Task name to run.
        """
        if isinstance(mlcube, dict):
            mlcube: DictConfig = OmegaConf.create(mlcube)
        if not isinstance(mlcube, DictConfig):
            raise ConfigurationError(f"Invalid mlcube type ('{type(DictConfig)}'). Expecting 'DictConfig'.")

        self.mlcube = mlcube
        self.task = task

        logger.debug("%s configuration: %s", self.__class__.__name__, str(self.mlcube.runner))

    def configure(self) -> None:
        ...

    def run(self) -> None:
        ...

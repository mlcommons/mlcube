import logging
import typing as t
from mlcube.errors import ConfigurationError
from omegaconf import (OmegaConf, DictConfig)


__all__ = ['BaseConfig', 'BaseRunner']


logger = logging.getLogger(__name__)


class BaseConfig(object):
    @staticmethod
    def merge_configs(default_config: DictConfig, actual_config: DictConfig) -> DictConfig:
        # Apply actual mlcube on top of default mlcube. Actual mlcube may be the result of merging
        # MLCube configuration and system settings.
        config = OmegaConf.merge(default_config, actual_config)
        # Make sure that all key/value pairs from default mlcube present in actual configuration. This may be the case
        for key, value in default_config.items():
            if config.get(key, None) is None:
                config[key] = default_config[key]
        #
        return config

    @staticmethod
    def dict_to_cli(args: t.Union[t.Dict, DictConfig], sep: t.Text = '=',
                    parent_arg: t.Optional[t.Text] = None) -> t.Text:
        """ Convert dict to CLI arguments.
        Args:
            args (typing.Dict): Dictionary with parameters.
            sep (str): Key-value separator. For build args and environment variables it's '=', for mount points -  ':'.
            parent_arg (str): If not None, a parent parameter name for each arg in args, e.g. --build-arg
        """
        if parent_arg is not None:
            cli_args = ' '.join(f'{parent_arg} {k}{sep}{v}' for k, v in args.items())
        else:
            cli_args = ' '.join(f'{k}{sep}{v}' for k, v in args.items())
        return cli_args


class BaseRunner(object):
    """ Base runner """

    CONFIG = None

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        """Base runner.
        Args:
            mlcube: MLCube configuration.
            task: Task name to run.
        """
        if isinstance(mlcube, dict):
            mlcube: DictConfig = OmegaConf.create(mlcube)
        if not isinstance(mlcube, DictConfig):
            raise ConfigurationError(f"Invalid mlcube type ('{type(DictConfig)}'). Expecting 'DictConfig'.")

        self.mlcube = self.CONFIG.validate(mlcube)
        self.task = task

        logger.debug("%s configuration: %s", self.__class__.__name__, str(self.mlcube.runner))

    def configure(self) -> None:
        ...

    def run(self) -> None:
        ...

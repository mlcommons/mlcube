import typing as t
from mlcube.errors import ConfigurationError
from omegaconf import (OmegaConf, DictConfig)


__all__ = ['BaseConfig', 'BaseRunner']


class BaseConfig(object):
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

    @staticmethod
    def assert_keys_not_none(name: t.Text, config: DictConfig, keys: t.Union[t.Text, t.List[t.Text]]) -> None:
        if not isinstance(config, (DictConfig, dict)):
            raise ConnectionError(f"The type({name}) is {type(name)}. Dictionary is expected.")
        if isinstance(keys, str):
            keys = [keys]
        missing_keys: t.List[t.Text] = [key for key in keys if config.get(key, None) is None]
        if len(missing_keys) > 0:
            raise ConfigurationError(f"Missing mandatory parameters in '{name}': {str(missing_keys)}")


class BaseRunner(object):
    """ Base runner """

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text, config_cls) -> None:
        """Base runner.
        Args:
            mlcube: MLCube configuration.
            task: Task name to run.
            config_cls: Configuration class.
        """
        if isinstance(mlcube, dict):
            mlcube: DictConfig = OmegaConf.create(mlcube)
        if not isinstance(mlcube, DictConfig):
            raise ConfigurationError(f"Invalid mlcube type ('{type(DictConfig)}'). Expecting 'DictConfig'.")

        self.mlcube = mlcube
        self.mlcube[config_cls.CONFIG_SECTION] = config_cls.from_dict(
            self.mlcube.get(config_cls.CONFIG_SECTION, OmegaConf.create({}))
        )
        self.task = task

    def configure(self) -> None:
        ...

    def run(self) -> None:
        ...

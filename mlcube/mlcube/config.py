import os
import logging
import typing as t
from omegaconf import (OmegaConf, DictConfig)


logger = logging.getLogger(__name__)


class IOType(object):
    INPUT = 'input'
    OUTPUT = 'output'

    @staticmethod
    def is_valid(io: t.Text) -> bool:
        return io in (IOType.INPUT, IOType.OUTPUT)


class ParameterType(object):
    FILE = 'file'
    DIRECTORY = 'directory'
    UNKNOWN = 'unknown'

    @staticmethod
    def is_valid(io: t.Text) -> bool:
        return io in (ParameterType.FILE, ParameterType.DIRECTORY, ParameterType.UNKNOWN)


class MLCubeConfig(object):

    @staticmethod
    def ensure_values_exist(config: DictConfig, keys: t.Union[t.Text, t.List], constructor: t.Callable) -> t.List:
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if config.get(key, None) is None:
                config[key] = constructor()
        return [config[key] for key in keys]

    @staticmethod
    def get_uri(value: t.Text) -> t.Text:
        if value.startswith('storage:'):
            raise ValueError(f"Storage schema is not yet supported")
        return os.path.abspath(os.path.expanduser(value))

    @staticmethod
    def create_runtime_config(root: t.Text, workspace: t.Optional[t.Text] = None) -> DictConfig:
        """ Return base configuration for all MLCubes.
        Args:
            root: Path to MLCube root directory.
            workspace: Workspace path to use in this MLCube run.
        Returns:
            Base configuration.
        """
        runtime_config = OmegaConf.create({
            # This configuration contains single entry - `runtime`. It is assumed that users do not use `runtime` key.
            'runtime': {
                # MLCube root folder
                'root': root,
                # Path to a default workspace which is located inside MLCube root directory. We need this to copy
                # configuration files to user-provided workspaces.
                'default_workspace': '${runtime.root}/workspace',
                # Default workspace path
                'workspace': '${runtime.root}/workspace' if workspace is None else MLCubeConfig.get_uri(workspace),
                # Default path to a global (user) config.
                'global_config': {
                    'uri': '${oc.env:MLCUBE_GLOBAL_CONFIG, ${oc.env:HOME}/.mlcube.yaml}',
                    'ignore': False
                }
            }
        })
        return runtime_config

    @staticmethod
    def create_mlcube_config(mlcube_config_file: t.Text, mlcube_cli_args: DictConfig, task_cli_args: t.Dict,
                             platform: t.Optional[t.Text], workspace: t.Optional[t.Text] = None,
                             resolve: bool = True) -> DictConfig:
        """ Create MLCube config merging different configs - base, global, local and cli.
        Args:
            mlcube_config_file: Path to mlcube.yaml file.
            mlcube_cli_args: MLCube config from command line.
            task_cli_args: Task parameters from command line.
            platform: Runner name.
            workspace: Workspace path to use in this MLCube run.
            resolve: If true, compute all values (some of them may reference other parameters or environmental
                variables).
        """
        logger.debug("mlcube_config_file = %s", mlcube_config_file)
        logger.debug("mlcube_cli_args = %s", mlcube_cli_args)
        logger.debug("task_cli_args = %s", task_cli_args)
        logger.debug("platform = %s", platform)
        logger.debug("workspace = %s", workspace)
        # TODO: sergey - it's not really clear now why I use list here.
        platforms = [platform] if platform else []
        # Merge default runtime config, local mlcube config and mlcube config from CLI.
        mlcube_config = OmegaConf.merge(
            MLCubeConfig.create_runtime_config(os.path.dirname(mlcube_config_file), workspace),
            OmegaConf.load(mlcube_config_file),
            mlcube_cli_args
        )
        # If available, load global MLCube config. We really need only the right platform section from global config.
        if not mlcube_config.runtime.global_config.ignore:
            uri = mlcube_config.runtime.global_config.uri
            try:
                global_config = OmegaConf.load(uri)
                if len(platforms) != 0:
                    global_config = OmegaConf.create({
                        platform: global_config.get(platform, {}) for platform in platforms
                    })
                mlcube_config = OmegaConf.merge(global_config, mlcube_config)
            except (IsADirectoryError, FileNotFoundError):
                logger.warning("Global configuration (%s) not loaded.", uri)

        for task_name in mlcube_config.tasks.keys():
            [task] = MLCubeConfig.ensure_values_exist(mlcube_config.tasks, task_name, dict)
            [parameters] = MLCubeConfig.ensure_values_exist(task, 'parameters', dict)
            [inputs, outputs] = MLCubeConfig.ensure_values_exist(parameters, ['inputs', 'outputs'], dict)

            MLCubeConfig.check_parameters(inputs, IOType.INPUT, task_cli_args)
            MLCubeConfig.check_parameters(outputs, IOType.OUTPUT, task_cli_args)

        if resolve:
            OmegaConf.resolve(mlcube_config)
        return mlcube_config

    @staticmethod
    def check_parameters(parameters: DictConfig, io: t.Text, task_cli_args: t.Dict) -> None:
        """ Check that task parameters are defined according to MLCube schema.
        Args:
            parameters: Task parameters (`inputs` or `outputs`).
            io: `input` or `output`.
            task_cli_args: Task parameters from command line.
        This function does not set `type` of parameters (if not present) in all cases.
        """
        for name in parameters.keys():
            # The `_param_name` is anyway there, so check it's not None.
            [param_def] = MLCubeConfig.ensure_values_exist(parameters, name, dict)
            # Deal with the case when value is a string (default value).
            if isinstance(param_def, str):
                parameters[name] = {'default': param_def}
                param_def = parameters[name]
            # If `default` key is not present, use parameter name as value.
            _ = MLCubeConfig.ensure_values_exist(param_def, 'default', lambda: name)
            # One challenge is how to identify type (file, directory) of input/output parameters if users have
            # not provided these types. The below is a kind of rule-based system that tries to infer types.

            # Make sure every parameter definition contains 'type' field. Also, if it's unknown, we can assume it's a
            # directory if a value ends with forward/backward slash.
            _ = MLCubeConfig.ensure_values_exist(param_def, 'type', lambda: ParameterType.UNKNOWN)
            if param_def.type == ParameterType.UNKNOWN and param_def.default.endswith(os.sep):
                param_def.type = ParameterType.DIRECTORY
            # See if there is value on a command line
            param_def.default = task_cli_args.get(name, param_def.default)
            # Check again parameter type. Users in certain number of cases will not be providing final slash on a
            # command line for directories, so we tried to infer types above using default values. Just in case, see
            # if we can do the same with user-provided values.
            if param_def.type == ParameterType.UNKNOWN and param_def.default.endswith(os.sep):
                param_def.type = ParameterType.DIRECTORY

            # TODO: For some input parameters, that generally speaking must exist, we can figure out types later,
            #       when we actually use them (in one of the runners). One problem is when inputs are optional. In this
            #       case, we need to know their type in advance.

            # It probably does not make too much sense to see, let's say, if an input parameter exists and set its
            # type at this moment, because MLCube can run on remote hosts.

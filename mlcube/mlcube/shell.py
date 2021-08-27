import os
import logging
import typing as t
from omegaconf import DictConfig
from mlcube.errors import ConfigurationError
from mlcube.config import (ParameterType, IOType)


__all__ = ['Shell']

logger = logging.getLogger(__name__)


class Shell(object):
    """ Helper functions to run commands. """

    @staticmethod
    def run(*cmd, die_on_error: bool = True) -> int:
        """Execute shell command.
        Args:
            cmd: Command to execute, e.g. Shell.run('ls', -lh'). This method will just join using whitespaces.
            die_on_error: If true and shell returns non-zero exit status, raise RuntimeError.
        Returns:
            Exit code.
        """
        cmd: t.Text = ' '.join(cmd)
        return_code: int = os.system(cmd)
        if return_code != 0 and die_on_error:
            logger.error("Command = '%s', return_code = %d, die_on_error = %r", cmd, return_code, die_on_error)
            raise RuntimeError("Command failed: {}".format(cmd))
        logger.info("Command = '%s', return_code = %d, die_on_error = %r", cmd, return_code, die_on_error)
        return return_code

    @staticmethod
    def docker_image_exists(docker: t.Optional[t.Text], image: t.Text) -> bool:
        """Check if docker image exists.
        Args:
            docker: Docker executable (docker/sudo docker/podman/nvidia-docker/...).
            image: Name of a docker image.
        Returns:
            True if image exists, else false.
        """
        docker = docker or 'docker'
        return Shell.run(f'{docker} inspect --type=image {image} > /dev/null 2>&1', die_on_error=False) == 0

    @staticmethod
    def ssh(connection_str: t.Text, command: t.Optional[t.Text]) -> None:
        if command:
            Shell.run('ssh', '-o', 'StrictHostKeyChecking=no', connection_str, f"'{command}'")

    @staticmethod
    def rsync_dirs(source: t.Text, dest: t.Text) -> None:
        Shell.run('rsync', '-e', "'ssh'", f"'{source}'", f"'{dest}'")

    @staticmethod
    def generate_mounts_and_args(mlcube: DictConfig, task: t.Text) -> t.Tuple[t.Dict, t.List]:
        """ Generate mount points and arguments for the give task.
        Return:
            A tuple containing two elements:
                -  A mapping from host path to path inside container.
                -  A list of task arguments.
        """
        # First task argument is always the task name.
        mounts, args = {}, [task]

        def _generate(_params: DictConfig, _io: t.Text) -> None:
            """ _params here is a dictionary containing input or output parameters.
            It maps parameter name to DictConfig(type, default)
            """
            if not IOType.is_valid(_io):
                raise ConfigurationError(f"Invalid IO = {_io}")
            for _param_name, _param_def in _params.items():
                if not ParameterType.is_valid(_param_def.type):
                    raise ConfigurationError(f"Invalid task: task={task}, param={_param_name}, "
                                             f"type={_param_def.type}. Type is invalid.")
                _host_path = os.path.join(mlcube.runtime.workspace, _param_def.default)

                if _param_def.type == ParameterType.UNKNOWN:
                    if _io == IOType.OUTPUT:
                        raise ConfigurationError(f"Invalid task: task={task}, param={_param_name}, "
                                                 f"type={_param_def.type}. Type is unknown.")
                    else:
                        if os.path.isdir(_host_path):
                            _param_def.type = ParameterType.DIRECTORY
                        elif os.path.isfile(_host_path):
                            _param_def.type = ParameterType.FILE
                        else:
                            raise ConfigurationError(f"Invalid task: task={task}, param={_param_name}, "
                                                     f"type={_param_def.type}. Type is unknown and unable to identify "
                                                     f"it ({_host_path}).")

                if _param_def.type == ParameterType.DIRECTORY:
                    os.makedirs(_host_path, exist_ok=True)
                    mounts[_host_path] = mounts.get(
                        _host_path,
                        '/mlcube_io{}/{}'.format(len(mounts), os.path.basename(_host_path))
                    )
                    args.append('--{}={}'.format(_param_name, mounts[_host_path]))
                elif _param_def.type == ParameterType.FILE:
                    _host_path, _file_name = os.path.split(_host_path)
                    os.makedirs(_host_path, exist_ok=True)
                    mounts[_host_path] = mounts.get(
                        _host_path,
                        '/mlcube_io{}/{}'.format(len(mounts), _host_path)
                    )
                    args.append('--{}={}'.format(_param_name, mounts[_host_path] + '/' + _file_name))

        params = mlcube.tasks[task].parameters
        _generate(params.inputs, IOType.INPUT)
        _generate(params.outputs, IOType.OUTPUT)

        return mounts, args

    @staticmethod
    def to_cli_args(args: t.Mapping[t.Text, t.Any], sep: t.Text = '=', parent_arg: t.Optional[t.Text] = None) -> t.Text:
        """ Convert dict to CLI arguments.
        Args:
            args: Dictionary with parameters.
            sep: Key-value separator. For build args and environment variables it's '=', for mount points it is ':'.
            parent_arg: If not None, a parent parameter name for each arg in args, e.g. --build-arg
        """
        parent_arg = '' if not parent_arg else parent_arg + ' '
        return ' '.join(f'{parent_arg}{k}{sep}{v}' for k, v in args.items())

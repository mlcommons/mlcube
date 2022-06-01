import os
import copy
import shutil
import logging
import sys
import typing as t
from pathlib import Path
from distutils import dir_util
from omegaconf import DictConfig
from mlcube.errors import (ConfigurationError, ExecutionError)
from mlcube.config import (ParameterType, IOType)


__all__ = ['Shell']

logger = logging.getLogger(__name__)


class Shell(object):
    """ Helper functions to run commands. """
    @staticmethod
    def parse_exec_status(status: int) -> t.Tuple[int, str]:
        """ Parse execution status returned by `os.system` call.
        Args:
            status: return code.
        Returns:
            Tuple containing exit code and exit status.

        https://github.com/mlperf/training_results_v0.5/blob/7238ee7edc18f64f0869923a04de2a92418c6c28/v0.5.0/nvidia/
        submission/code/translation/pytorch/cutlass/tools/external/googletest/googletest/test/gtest_test_utils.py#L185
        """
        if os.name == 'nt':
            exit_code, exit_status = (status, 'exited')
        else:
            if os.WIFEXITED(status):
                exit_code, exit_status = (os.WEXITSTATUS(status), 'exited')
            elif os.WIFSTOPPED(status):
                exit_code, exit_status = (-os.WSTOPSIG(status), 'stopped')
            elif os.WIFSIGNALED(status):
                exit_code, exit_status = (-os.WTERMSIG(status), 'signalled')
            else:
                exit_code, exit_status = (status, 'na')
        return exit_code, exit_status

    @staticmethod
    def run(cmd: t.Union[str, t.List], on_error: str = 'raise') -> int:
        """Execute shell command.
        Args:
            cmd: Command to execute, e.g. Shell.run(['ls', -lh']). If type is iterable, this method will join into
                one string using whitespace as a separator.
            on_error: Action to perform if `os.system` returns a non-zero status. Options - ignore (do nothing, return
                exit code), 'raise' (raise a RuntimeError exception), 'die' (exit the process).
        Returns:
            Exit status. On Windows, the exit status is the output of `os.system`. On Linux, the output is either
                process exit status if that processes exited, or -1 in other cases (e.g., process was killed).
        """
        if isinstance(cmd, t.List):
            cmd = ' '.join(cmd)

        if on_error not in ('raise', 'die', 'ignore'):
            raise ValueError(
                f"Unrecognized 'on_error' action ({on_error}). Valid options are ('raise', 'die', 'ignore')."
            )

        status: int = os.system(cmd)
        exit_code, exit_status = Shell.parse_exec_status(status)
        if exit_status == 'na':
            logger.warning("Command (cmd=%s) did not exit properly (status=%d).", cmd, status)

        msg = f"Command='{cmd}' status={status} exit_status={exit_status} exit_code={exit_code} on_error={on_error}"
        if exit_code != 0:
            logger.error(msg)
            if on_error == 'die':
                sys.exit(exit_code)
            if on_error == 'raise':
                raise ExecutionError(
                    'Failed to execute shell command.', status=exit_status, code=exit_code, cmd=cmd
                )
        else:
            logger.info(msg)
        return exit_code

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
        return Shell.run(f'{docker} inspect --type=image {image} > /dev/null 2>&1', on_error='ignore') == 0

    @staticmethod
    def ssh(connection_str: str, command: t.Optional[str], on_error: str = 'raise') -> int:
        if not command:
            return 0
        return Shell.run(f"ssh -o StrictHostKeyChecking=no {connection_str} '{command}'", on_error=on_error)

    @staticmethod
    def rsync_dirs(source: str, dest: str, on_error: str = 'raise') -> int:
        return Shell.run(f"rsync -e 'ssh' '{source}' '{dest}'", on_error=on_error)

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
                _host_path = Path(mlcube.runtime.workspace) / _param_def.default

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
                    new_mount = mounts.get(
                        _host_path,
                        '/mlcube_io{}/{}'.format(len(mounts), _host_path)
                    )
                    windows_match = ':\\'
                    if windows_match in new_mount:
                        index = new_mount.index(windows_match)
                        substring = new_mount[index-1:index+2]
                        new_mount = new_mount.replace(substring, '').replace('\\', '/')
                    mounts[_host_path] = new_mount
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

    @staticmethod
    def sync_workspace(target_mlcube: DictConfig, task: t.Text) -> None:
        """
        Args:
            target_mlcube: MLCube configuration. Its name (target_) means that this configuration defines actual
                configuration where MLCube is supposed to be executed. If workspaces are different, source_mlcube will
                refer to the MLCube configuration with default (internal) workspace.
            task: Task name to be executed.
        """
        def _storage_not_supported(_uri: t.Text) -> t.Text:
            """ Helper function to guard against unsupported storage. """
            _uri = _uri.strip()
            if _uri.startswith('storage:'):
                raise NotImplementedError(f"Storage protocol (uri={_uri}) is not supported yet.")
            return _uri

        def _is_inside_workspace(_workspace: t.Text, _artifact: t.Text) -> bool:
            """ Check if artifact is inside this workspace. Workspace directory and artifact must exist. """
            return os.path.commonpath([_workspace]) == os.path.commonpath([_workspace, _artifact])

        def _is_ok(_parameter: t.Text, _kind: t.Text, _workspace: t.Text, _artifact: t.Text, _must_exist: bool) -> bool:
            """ Return true if this artifact needs to be synced. """
            if not _is_inside_workspace(_workspace, _artifact):
                logger.debug("[sync_workspace] task = %s, parameter = %s, artifact is not inside %s workspace "
                             "(workspace = %s, uri = %s)", task, _parameter, _kind, _workspace, _artifact)
                return False
            if _must_exist and not os.path.exists(_artifact):
                logger.debug("[sync_workspace] task = %s, parameter = %s, artifact does not exist in %s workspace "
                             "(workspace = %s, uri = %s)", task, _parameter, _kind, _workspace, _artifact)
                return False
            if not _must_exist and os.path.exists(_artifact):
                logger.debug("[sync_workspace] task = %s, parameter = %s, artifact exists in %s workspace "
                             "(workspace = %s, uri = %s)", task, _parameter, _kind, _workspace, _artifact)
                return False
            return True

        def _is_task_output(_target_artifact: t.Text, _input_parameter: t.Text) -> bool:
            """ Check of this artifact is an output of some task. """
            for _task_name, _task_def in target_mlcube.tasks.items():
                for _output_param_name, _output_param_def in _task_def.parameters.outputs.items():
                    _target_output_artifact: t.Text = Path(target_workspace) / _storage_not_supported(_output_param_def.default)

                    # Can't really use `os.path.samefile` here since files may not exist.
                    # if os.path.samefile(_target_artifact, _target_output_artifact):
                    if _target_artifact == _target_output_artifact:
                        logger.debug("[sync_workspace] task = %s, parameter = %s is an output of task = %s, "
                                     "parameter = %s", task, _input_parameter, _task_name, _output_param_name)
                        return True
            return False

        # Check if actual workspace is not internal one (which is default workspace).
        target_workspace = os.path.abspath(_storage_not_supported(target_mlcube.runtime.workspace))
        os.makedirs(target_workspace, exist_ok=True)

        source_workspace = os.path.abspath(Path(target_mlcube.runtime.root) / 'workspace')
        if not os.path.exists(source_workspace):
            logger.debug("[sync_workspace] source workspace (%s) does not exist, nothing to sync.", source_workspace)
            return
        if os.path.samefile(target_workspace, source_workspace):
            logger.debug("[sync_workspace] target workspace (%s) is the same as source workspace (%s).",
                         target_workspace, source_workspace)
            return

        if task not in target_mlcube.tasks:
            raise ValueError(f"Task does not exist: {task}")

        # Deep copy of the MLCube config with workspace set to internal workspace (we need this to resolve artifact
        # paths).
        source_mlcube: DictConfig = copy.deepcopy(target_mlcube)
        source_mlcube.runtime.workspace = source_workspace
        source_mlcube.workspace = source_workspace

        inputs: t.Mapping[t.Text, DictConfig] = target_mlcube.tasks[task].parameters.inputs
        for input_name, input_def in inputs.items():
            # TODO: add support for storage protocol. Idea is to be able to retrieve actual storage specs from
            #       system settings file. It should be possible to also specify paths within that storage (see
            #       https://en.wikipedia.org/wiki/Uniform_Resource_Identifier). For instance, the `storage:home/${name}`
            #       means that the `storage` section defines some storage labelled as `home`, and MLCube needs to use
            #       ${name} path within that storage.

            source_uri: t.Text = Path(source_workspace) / _storage_not_supported(input_def.default)

            if not _is_ok(input_name, 'source', source_workspace, source_uri, _must_exist=True):
                continue

            target_uri: t.Text = Path(target_workspace) / _storage_not_supported(input_def.default)
            if not _is_ok(input_name, 'target', target_workspace, target_uri, _must_exist=False):
                continue

            if _is_task_output(target_uri, input_name):
                continue

            if os.path.isfile(source_uri):
                os.makedirs(os.path.dirname(target_uri), exist_ok=True)
                shutil.copy(source_uri, target_uri)
            elif os.path.isdir(source_uri):
                dir_util.copy_tree(source_uri, target_uri)
            else:
                raise RuntimeError(f"Unknown artifact type (%s)", source_uri)
            logger.debug("[sync_workspace] task = %s, parameter = %s, source (%s) copied to target (%s).",
                         task, input_name, source_uri, target_uri)

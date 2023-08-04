"""Various utils to work with shell (mostly - running external processes).

- `Shell`: This class provides a collection of methods to work with shell to run external processes.
"""
import copy
import logging
import os
import shutil
import subprocess
import sys
import typing as t
from distutils import dir_util
from pathlib import Path

from mlcube.config import (IOType, ParameterType, MountType)
from mlcube.errors import (ConfigurationError, ExecutionError)

from omegaconf import DictConfig


__all__ = ['Shell']

logger = logging.getLogger(__name__)


class Shell(object):
    """Helper functions to run commands."""

    @staticmethod
    def null() -> str:
        """Return /dev/null for Linux/Windows.

        TODO: In powershell, $null works. Is below the correct implementation?
        """
        if os.name == 'nt':
            return 'NUL'
        return '/dev/null'

    @staticmethod
    def parse_exec_status(status: int) -> t.Tuple[int, str]:
        """Parse execution status returned by `os.system` call.

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
        """Run the `cmd` command in an external process.

        Args:
            cmd: Command to execute, e.g. Shell.run(['ls', -lh']). If type is iterable, this method will join into
                one string using whitespace as a separator.
            on_error: Action to perform if `os.system` returns a non-zero status. Options - ignore (do nothing, return
                exit code), 'raise' (raise a RuntimeError exception), 'die' (exit the process).
        Returns:
            Exit status. On Windows, the exit status is the output of `os.system`. On Linux, the output is either
                process exit status if that processes exited, or -1 in other cases (e.g., process was killed).
        """
        logger.debug("Shell.run input_arg: cmd=%s, on_error=%s)", cmd, on_error)
        if isinstance(cmd, t.List):
            cmd = ' '.join(c for c in (c.strip() for c in cmd) if c)
            logger.debug("Shell.run list->str: cmd=\"%s\")", cmd)

        if on_error not in ('raise', 'die', 'ignore'):
            raise ValueError(
                f"Unrecognized 'on_error' action ({on_error}). Valid options are ('raise', 'die', 'ignore')."
            )

        status: int = os.system(cmd)
        exit_code, exit_status = Shell.parse_exec_status(status)
        if exit_status == 'na':
            logger.warning("Shell.run command (cmd=%s) did not exit properly (status=%d).", cmd, status)

        msg = f"Shell.run command='{cmd}' status={status} exit_status={exit_status} exit_code={exit_code} "\
              f"on_error={on_error}"
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
    def run_and_capture_output(cmd: t.List[str]) -> t.Tuple[int, str]:
        """Run command and return the exit code and command output.

        Args:
            cmd: Command to execute, will be passed to `subprocess.check_output` as is.

        Returns:
             A tuple containing exit code (either 0 or `subprocess.CalledProcessError.returncode`) and command output
             which is either output of `subprocess.check_output` or `subprocess.CalledProcessError.output.decode()`.
        """
        try:
            exit_code = 0
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        except FileNotFoundError as err:
            exit_code, output = 1, str(err)
        except subprocess.CalledProcessError as err:
            exit_code, output = err.returncode, err.output.decode()

        logger.debug(
            "Shell.run_and_capture_output cmd=%s, exit_code=%d, output=\"%s\"",
            cmd, exit_code, output.replace("\n", " ")
        )
        return exit_code, output.strip()

    @staticmethod
    def docker_image_exists(docker: t.Optional[str], image: str) -> bool:
        """Check if docker image exists.

        Args:
            docker: Docker executable (docker/sudo docker/podman/nvidia-docker/...).
            image: Name of a docker image.
        Returns:
            True if image exists, else false.
        """
        docker = docker or 'docker'
        cmd = f'{docker} inspect --type=image {image} > {Shell.null()}'
        return Shell.run(cmd, on_error='ignore') == 0

    @staticmethod
    def ssh(connection_str: str, command: t.Optional[str], on_error: str = 'raise') -> int:
        """Execute a command on a remote host via SSH.

        Args:
            connection_str: SSH connection string.
            command: Command to execute.
            on_error: Action to perform if an error occurs.
        """
        if not command:
            return 0
        return Shell.run(f"ssh -o StrictHostKeyChecking=no {connection_str} '{command}'", on_error=on_error)

    @staticmethod
    def rsync_dirs(source: str, dest: str, on_error: str = 'raise') -> int:
        """Synchronize directories.

        Args:
            source: Source directory.
            dest: Destination directory.
            on_error: Action to perform if an error occurs.
        """
        return Shell.run(f"rsync -e 'ssh' '{source}' '{dest}'", on_error=on_error)

    @staticmethod
    def get_host_path(workspace_path: str, path_from_config: str) -> str:
        """Return host path for a task parameter.

        Args:
            workspace_path: Workspace directory path for this MLCube.
            path_from_config: Parameter path as specified by a user in an MLCube configuration file (e.g., mlcube.yaml).

        Returns:
            Absolute host path.
        """
        # Omega conf will resolve any variables defined in MLCube configuration file. We need to take care about `~`
        # (user home directory) and environment variables.
        host_path = Path(
            os.path.expandvars(os.path.expanduser(path_from_config))
        )
        # According to MLCube contract, relative paths are relative to MLCube workspace directory.
        if not host_path.is_absolute():
            host_path = Path(workspace_path) / host_path
        return host_path.as_posix()

    @staticmethod
    def generate_mounts_and_args(mlcube: DictConfig, task: str,
                                 make_dirs: bool = True) -> t.Tuple[t.Dict, t.List, t.Dict]:
        """Generate mount points, task arguments and mount options for the given task.

        Args:
            mlcube: MLCube configuration (e.g., coming from `mlcube.yaml` file).
            task: Task name for which mount points need to be generated.
            make_dirs: If true, make host directories recursively if they do not exist. We need this to actually make
                unit tests work (that set this value to false).
        Return:
            A tuple containing three elements:
                - A mapping from host path to path inside container.
                - A list of task arguments.
                - A mapping from host paths to mount options (optional).
        """
        # First task argument is always the task name.
        mounts: t.Dict[str, str] = {}         # Mapping from host paths to container paths.
        args: t.List[str] = [task]            # List of arguments for the given task.
        mounts_opts: t.Dict[str, str] = {}    # Mapping from host paths to mount options (rw/ro).

        def _generate(_params: DictConfig, _io: str) -> None:
            """Process parameters (could be inputs or outputs).

            This function updates `mounts`, `args` and `mounts_opts`.

            Args:
                _params: Dictionary of input or output parameters.
                _io: Specifies if these parameters are input our output parameters.
            """
            if not IOType.is_valid(_io):
                raise ConfigurationError(f"Invalid IO = {_io}")
            for _param_name, _param_def in _params.items():
                assert isinstance(_param_def, DictConfig), f"Unexpected parameter definition: {_param_def}."
                if not ParameterType.is_valid(_param_def.type):
                    raise ConfigurationError(
                        f"Invalid task: task={task}, param={_param_name}, type={_param_def.type}. Type is invalid."
                    )

                # MLCube contract says relative paths in MLCube configuration files are relative with respect to MLCube
                # workspace directory. In certain cases it makes sense to use absolute paths too. This maybe the case
                # when we want to reuse host cache directories that many machine learning frameworks use to cache models
                # and datasets. We also need to be able to resolve `~` (user home directory), as well as environment
                # variables (BTW, this is probably needs some discussion at some point in time). This environment
                # variable could be, for instance, `${HOME}`.
                _host_path: str = Shell.get_host_path(mlcube.runtime.workspace, _param_def.default)

                if _param_def.type == ParameterType.UNKNOWN:
                    if _io == IOType.OUTPUT:
                        raise ConfigurationError(
                            f"Invalid task: task={task}, param={_param_name}, type={_param_def.type}. "
                            "Type cannot be unknown for output parameters."
                        )
                    else:
                        if os.path.isdir(_host_path):
                            _param_def.type = ParameterType.DIRECTORY
                        elif os.path.isfile(_host_path):
                            _param_def.type = ParameterType.FILE
                        else:
                            raise ConfigurationError(
                                f"Invalid task: task={task}, param={_param_name}, type={_param_def.type}. "
                                f"Type is unknown and unable to identify it ({_host_path})."
                            )

                if _param_def.type == ParameterType.DIRECTORY:
                    if make_dirs:
                        os.makedirs(_host_path, exist_ok=True)
                    mounts[_host_path] = mounts.get(_host_path, f"/mlcube_io{len(mounts)}")
                    args.append('--{}={}'.format(_param_name, mounts[_host_path]))
                elif _param_def.type == ParameterType.FILE:
                    _host_path, _file_name = os.path.split(_host_path)
                    if make_dirs:
                        os.makedirs(_host_path, exist_ok=True)
                    mounts[_host_path] = mounts.get(_host_path, f"/mlcube_io{len(mounts)}")
                    args.append('--{}={}'.format(_param_name, mounts[_host_path] + '/' + _file_name))

                mount_type: t.Optional[str] = _param_def.get('opts', None)
                if mount_type:
                    if not MountType.is_valid(_param_def.opts):
                        raise ConfigurationError(
                            f"Invalid mount options: mount={task}, param={_param_name}, opts={_param_def.opts}."
                        )
                    if mount_type == MountType.RO and _io == IOType.OUTPUT:
                        logger.warning(
                            "Task's (%s) parameter (%s) is OUTPUT and requested to mount as RO.", task, _param_name
                        )
                    if _host_path in mounts_opts and mounts_opts[_host_path] != mount_type:
                        logger.warning(
                            "Conflicting mount options found. Host path (%s) has already been requested to mount as "
                            "'%s', but new parameter (%s) requests to mount as '%s'.",
                            _host_path, mounts_opts[_host_path], _param_name, mount_type
                        )
                        # Since we can only have `ro`/`rw`, we'll set the mount option to `rw`.
                        mount_type = MountType.RW

                    mounts_opts[_host_path] = mount_type
                    logger.info(
                        "Host path (%s) for parameter '%s' will be mounted with '%s' option.",
                        _host_path, _param_name, mount_type
                    )

        params = mlcube.tasks[task].parameters     # Dictionary of input and output parameters for the task.
        _generate(params.inputs, IOType.INPUT)     # Process input parameters.
        _generate(params.outputs, IOType.OUTPUT)   # Process output parameters.

        return mounts, args, mounts_opts

    @staticmethod
    def to_cli_args(args: t.Mapping[str, t.Any], sep: str = '=', parent_arg: t.Optional[str] = None) -> str:
        """Convert dict to CLI arguments.

        Args:
            args: Dictionary with parameters.
            sep: Key-value separator. For build args and environment variables it's '=', for mount points it is ':'.
            parent_arg: If not None, a parent parameter name for each arg in args, e.g. --build-arg
        """
        parent_arg = '' if not parent_arg else parent_arg + ' '
        return ' '.join(f'{parent_arg}{k}{sep}{v}' for k, v in args.items())

    @staticmethod
    def sync_workspace(target_mlcube: DictConfig, task: str) -> None:
        """Synchronize MLCube workspaces.

        Args:
            target_mlcube: MLCube configuration. Its name (target_) means that this configuration defines actual
                configuration where MLCube is supposed to be executed. If workspaces are different, source_mlcube will
                refer to the MLCube configuration with default (internal) workspace.
            task: Task name to be executed.
        """
        def _storage_not_supported(_uri: str) -> str:
            """Raise an exception if the given URI is not supported.

            Args:
                _uri: URI to check. If it starts with `storage:` (yet unsupported schema), raise an exception.
            """
            _uri = _uri.strip()
            if _uri.startswith('storage:'):
                raise NotImplementedError(f"Storage protocol (uri={_uri}) is not supported yet.")
            return _uri

        def _is_inside_workspace(_workspace: str, _artifact: str) -> bool:
            """Check if artifact is inside this workspace. Workspace directory and artifact must exist."""
            return os.path.commonpath([_workspace]) == os.path.commonpath([_workspace, _artifact])

        def _is_ok(_parameter: str, _kind: str, _workspace: str, _artifact: str, _must_exist: bool) -> bool:
            """Return true if this artifact needs to be synced."""
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

        def _is_task_output(_target_artifact: str, _input_parameter: str) -> bool:
            """Check of this artifact is an output of some task."""
            for _task_name, _task_def in target_mlcube.tasks.items():
                for _output_param_name, _output_param_def in _task_def.parameters.outputs.items():
                    _target_output_artifact: str = \
                        Path(target_workspace) / _storage_not_supported(_output_param_def.default)

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

        inputs: t.Mapping[str, DictConfig] = target_mlcube.tasks[task].parameters.inputs
        for input_name, input_def in inputs.items():
            # TODO: add support for storage protocol. Idea is to be able to retrieve actual storage specs from
            #       system settings file. It should be possible to also specify paths within that storage (see
            #       https://en.wikipedia.org/wiki/Uniform_Resource_Identifier). For instance, the `storage:home/${name}`
            #       means that the `storage` section defines some storage labelled as `home`, and MLCube needs to use
            #       ${name} path within that storage.

            source_uri: str = Path(source_workspace) / _storage_not_supported(input_def.default)

            if not _is_ok(input_name, 'source', source_workspace, source_uri, _must_exist=True):
                continue

            target_uri: str = Path(target_workspace) / _storage_not_supported(input_def.default)
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
                raise RuntimeError(f"Unknown artifact type ({source_uri}).")
            logger.debug("[sync_workspace] task = %s, parameter = %s, source (%s) copied to target (%s).",
                         task, input_name, source_uri, target_uri)

import os
import logging
import typing as t
from omegaconf import (OmegaConf, DictConfig)


__all__ = ['ConfigurationError', 'IllegalParameterError', 'DockerRun']


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """ Base class for all configuration errors. """
    pass


class IllegalParameterError(ConfigurationError):
    """ Exception to be raised when a configuration parameter is missing or has illegal value. """
    def __init__(self, name: t.Text, value: t.Any) -> None:
        """
        Args:
            name: Parameter name, possibly, qualified (e.g. `container.image`).
            value: Current parameter value.
        """
        super().__init__(f"{name} = {value}")


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
        print(cmd)
        return_code: int = os.system(cmd)
        if return_code != 0 and die_on_error:
            raise RuntimeError("Command failed: {}".format(cmd))
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


class Config(object):
    """ Helper class to manage `container` environment configuration."""

    CONFIG_SECTION = 'docker'         # Section name in MLCube configuration file.

    DEFAULT_CONFIG = {
        'image': '???',               # Image name.
        'docker': 'docker',           # Executable (docker, podman, sudo docker ...).

        'env_args': {},               # Environmental variables for build and run actions.

        'gpu_args': '',               # Docker run arguments when accelerator_count > 0.
        'cpu_args': '',               # Docker run arguments when accelerator_count == 0.

        'build_args': {},             # Docker build arguments
        'build_context': '.',         # Docker build context relative to $MLCUBE_ROOT. Default is $MLCUBE_ROOT.
        'build_file': 'Dockerfile',   # Docker file relative to $MLCUBE_ROOT, default is:
                                      # `$MLCUBE_ROOT/Dockerfile`.
        'build_always': True,         # Try to build the docker image every time a task is executed.
    }

    @staticmethod
    def from_dict(docker_env: DictConfig) -> DictConfig:
        """ Initialize configuration from user config
        Args:
            docker_env: MLCube `container` configuration, possible merged with user local configuration.
        Return:
            Initialized configuration.
        """
        # Make sure all parameters present with their default values.
        for name, value in Config.DEFAULT_CONFIG.items():
            docker_env[name] = docker_env.get(name, None) or value

        if not docker_env.image:
            raise IllegalParameterError(f'{Config.CONFIG_SECTION}.image', docker_env.image)

        if isinstance(docker_env.build_args, DictConfig):
            docker_env.build_args = Config.dict_to_cli(docker_env.build_args, parent_arg='--build-arg')
        if isinstance(docker_env.env_args, DictConfig):
            docker_env.env_args = Config.dict_to_cli(docker_env.env_args, parent_arg='-e')

        logger.info(f"DockerRun configuration: {str(docker_env)}")
        return docker_env

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


class DockerRun(object):
    """ Docker runner. """

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        """Docker Runner.
        Args:
            mlcube: MLCube configuration.
            task: Task name to run.
        """
        if isinstance(mlcube, dict):
            mlcube: DictConfig = OmegaConf.create(mlcube)
        if not isinstance(mlcube, DictConfig):
            raise ConfigurationError(f"Invalid mlcube type ('{type(DictConfig)}'). Expecting 'DictConfig'.")

        self.mlcube = mlcube
        self.mlcube.docker = Config.from_dict(self.mlcube.get(Config.CONFIG_SECTION, OmegaConf.create({})))
        self.task = task

    def configure(self):
        """Build Docker image on a current host."""
        image: t.Text = self.mlcube.docker.image
        context: t.Text = os.path.join(self.mlcube.runtime.root, self.mlcube.docker.build_context)
        recipe: t.Text = os.path.join(context, self.mlcube.docker.build_file)
        docker: t.Text = self.mlcube.docker.docker

        if not os.path.exists(recipe):
            Shell.run(docker, 'pull', image)
        else:
            build_args: t.Text = self.mlcube.docker.build_args
            Shell.run(docker, 'build', build_args, '-t', image, '-f', recipe, context)

    def run(self):
        """ Run a cube. """
        docker: t.Text = self.mlcube.docker.docker
        image: t.Text = self.mlcube.docker.image
        if self.mlcube.docker.build_always or not Shell.docker_image_exists(docker, image):
            logger.warning("Docker image (%s) does not exist or build always is on. Running 'configure' phase.", image)
            self.configure()

        # The 'mounts' dictionary maps host paths to container paths
        mounts, task_args = self._generate_mounts_and_args()
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Config.dict_to_cli(mounts, sep=':', parent_arg='--volume')
        env_args = self.mlcube.docker.env_args
        num_gpus: int = self.mlcube.platform.get('accelerator_count', None) or 0
        run_args: t.Text = self.mlcube.docker.cpu_args if num_gpus == 0 else self.mlcube.docker.gpu_args

        Shell.run(docker, 'run', run_args, env_args, volumes, image, ' '.join(task_args))

    def _generate_mounts_and_args(self) -> t.Tuple[t.Dict, t.List]:
        """ Generate mount points and arguments for the give task.
        Return:
            A tuple containing two elements:
                -  A mapping from host path to path inside container.
                -  A list of task arguments.
        """
        # First task argument is always the task name.
        mounts, args = {}, [self.task]

        def _generate(_params: DictConfig) -> None:
            """ _params here is a dictionary containing input or output parameters.
            It maps parameter name to DictConfig(type, default)
            """
            for _param_name, _param_def in _params.items():
                if _param_def.type not in ('file', 'directory'):
                    raise ConfigurationError(f"Invalid task: task={self.task}, param={_param_name}, "
                                             f"type={_param_def.type}")
                _host_path = os.path.join(self.mlcube.runtime.workspace, _param_def.get('default', _param_name))
                if _param_def.type == 'directory':
                    os.makedirs(_host_path, exist_ok=True)
                    mounts[_host_path] = mounts.get(
                        _host_path,
                        '/mlcube_io{}/{}'.format(len(mounts), os.path.basename(_host_path))
                    )
                    args.append('--{}={}'.format(_param_name, mounts[_host_path]))
                elif _param_def.type == 'file':
                    _host_path, _file_name = os.path.split(_host_path)
                    os.makedirs(_host_path, exist_ok=True)
                    mounts[_host_path] = mounts.get(
                        _host_path,
                        '/mlcube_io{}/{}'.format(len(mounts), _host_path)
                    )
                    args.append('--{}={}'.format(_param_name, mounts[_host_path] + '/' + _file_name))

        params = self.mlcube.tasks[self.task].parameters
        _generate(params.get('inputs', OmegaConf.create({})))
        _generate(params.get('outputs', OmegaConf.create({})))

        return mounts, args

import os
import typing
import logging
from omegaconf import (OmegaConf, DictConfig)


__all__ = ['ConfigurationError', 'IllegalParameterError', 'DockerRun']


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """ Base class for all configuration errors. """
    pass


class IllegalParameterError(ConfigurationError):
    """ Exception to be raised when a configuration parameter is missing or has illegal value. """
    def __init__(self, name: str, value: typing.Any) -> None:
        """
        Args:
            name (str): Parameter name, possibly, qualified (e.g. `container.image`).
            value (str): Current parameter value.
        """
        super().__init__(f"{name} = {value}")


class Shell(object):
    """ Helper functions to run commands. """

    @staticmethod
    def run(*cmd, die_on_error: bool = True) -> int:
        """Execute shell command.
        Args:
            cmd: Command to execute, e.g. Shell.run('ls', -lh'). This method will just join using whitespaces.
            die_on_error (bool): If true and shell returns non-zero exit status, raise RuntimeError.
        Returns:
            Exit code.
        """
        cmd: str = ' '.join(cmd)
        print(cmd)
        return_code: int = os.system(cmd)
        if return_code != 0 and die_on_error:
            raise RuntimeError("Command failed: {}".format(cmd))
        return return_code

    @staticmethod
    def docker_image_exists(docker: typing.Optional[str], image: str) -> bool:
        """Check if docker image exists.
        Args:
            docker (str): Docker executable (docker/sudo docker/podman/nvidia-docker/...).
            image (str): Name of a docker image.
        Returns:
            True if image exists, else false.
        """
        docker = docker or 'docker'
        return Shell.run(f'{docker} inspect --type=image {image} > /dev/null 2>&1', die_on_error=False) == 0


class Config(object):
    """ Helper class to manage `container` environment configuration."""

    CONFIG_SECTION = 'container'         # Section name in MLCube configuration file.

    DEFAULTS = {
        'image': '',                     # Image name.
        'docker': 'docker',              # Executable (docker, podman, sudo docker ...).
        'gpu_args': '',                  # Docker run arguments when accelerator_count > 0.
        'cpu_args': '',                  # Docker run arguments when accelerator_count == 0.

        'build_args': {},                # Docker build arguments
        'build_context': 'build',        # Docker build context relative to $MLCUBE_ROOT. Default is `build`.
        'build_file': 'Dockerfile',      # Docker file name within docker build context, default is `Dockerfile`.
        'build_always': True,            # Try to build the docker image every time a task is executed.

        'env_args': {},                  # Environmental variables for build and run actions.
    }

    @staticmethod
    def from_dict(container_env: DictConfig) -> DictConfig:
        """ Initialize configuration from user config
        Args:
            container_env (DictConfig): MLCube `container` configuration, possible merged with user local configuration.
        Return:
            Initialized configuration.
        """
        # Make sure all parameters present with their default values.
        for name, value in Config.DEFAULTS.items():
            container_env[name] = container_env.get(name, None) or value

        if not container_env.image:
            raise IllegalParameterError(f'{Config.CONFIG_SECTION}.image', container_env.image)

        if isinstance(container_env.build_args, DictConfig):
            container_env.build_args = Config.dict_to_cli(container_env.build_args, parent_arg='--build-arg')
        if isinstance(container_env.env_args, DictConfig):
            container_env.env_args = Config.dict_to_cli(container_env.env_args, parent_arg='-e')

        logger.info(f"DockerRun configuration: {str(container_env)}")
        return container_env

    @staticmethod
    def dict_to_cli(args: typing.Union[typing.Dict, DictConfig], sep: str = '=',
                    parent_arg: typing.Optional[str] = None) -> str:
        """ Convert dict to CLI arguments.
        Args:
            args (typing.Dict): Dictionary with parameters.
            parent_arg (str): If not None, a parent parameter name for each arg in args, e.g. --build-arg
        """
        if parent_arg is not None:
            cli_args = ' '.join(f'{parent_arg} {k}{sep}{v}' for k, v in args.items())
        else:
            cli_args = ' '.join(f'{k}{sep}{v}' for k, v in args.items())
        return cli_args


class DockerRun(object):
    """ Docker runner. """

    def __init__(self, mlcube: typing.Dict, **kwargs) -> None:
        """Docker Runner.
        Args:
            mlcube (typing.Dict): MLCube configuration.
            kwargs: Additional parameters (root, workspace, task).
        """
        if not isinstance(mlcube, dict):
            raise ConfigurationError(f"Invalid mlcube type ('{type(mlcube)}'). Expecting 'dict'.")

        self.mlcube = OmegaConf.create(mlcube)
        self.mlcube.container = Config.from_dict(self.mlcube.get(Config.CONFIG_SECTION, OmegaConf.create({})))

        self.root = kwargs.get('root', None)
        if not self.root:
            raise IllegalParameterError('root', self.root)
        self.task = kwargs.get('task', None)
        if not self.task:
            raise IllegalParameterError('task', self.task)
        self.workspace = kwargs.get('workspace', os.path.join(self.root, 'workspace'))

    def configure(self):
        """Build Docker image on a current host."""
        image: str = self.mlcube.container.image
        context: str = os.path.join(self.root, self.mlcube.container.build_context)
        recipe: str = os.path.join(context, self.mlcube.container.build_file)
        docker: str = self.mlcube.container.docker

        if not os.path.exists(recipe):
            Shell.run(docker, 'pull', image)
        else:
            build_args: str = self.mlcube.container.build_args
            Shell.run(docker, 'build', build_args, '-t', image, '-f', recipe, context)

    def run(self):
        """ Run a cube. """
        docker: str = self.mlcube.container.docker
        image: str = self.mlcube.container.image
        if self.mlcube.container.build_always or not Shell.docker_image_exists(docker, image):
            logger.warning("Docker image (%s) does not exist or build always is on. Running 'configure' phase.", image)
            self.configure()

        # The 'mounts' dictionary maps host paths to container paths
        mounts, task_args = self._generate_mounts_and_args()
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Config.dict_to_cli(mounts, sep=':', parent_arg='--volume')
        env_args = self.mlcube.container.env_args
        num_gpus: int = self.mlcube.platform.get('accelerator_count', None) or 0
        run_args: str = self.mlcube.container.cpu_args if num_gpus == 0 else self.mlcube.container.gpu_args

        Shell.run(docker, 'run', run_args, env_args, volumes, image, ' '.join(task_args))

    def _generate_mounts_and_args(self) -> typing.Tuple[typing.Dict, typing.List]:
        """ Generate mount points and arguments for the give task.
        Return:
            A tuple containing two elements:
                -  A mapping from host path to path inside container.
                -  A list of task arguments.
        """
        # First task argument is always the task name.
        mounts, args = {}, [self.task]

        params = self.mlcube.tasks[self.task].io
        for param in params:
            # Fields in param: name (raw_data), type (directory), io (output), default ($WORKSPACE/raw_data)
            host_path = param.get(
                'default',
                f'$WORKSPACE/{param.name}'
            ).replace('$WORKSPACE', self.workspace)
            if param.type == 'directory':
                os.makedirs(host_path, exist_ok=True)
                mounts[host_path] = mounts.get(
                    host_path,
                    '/mlcube_io{}/{}'.format(len(mounts), os.path.basename(host_path))
                )
                args.append('--{}={}'.format(param.name, mounts[host_path]))
            elif param.type == 'file':
                host_path, file_name = os.path.split(host_path)
                os.makedirs(host_path, exist_ok=True)
                mounts[host_path] = mounts.get(
                    host_path,
                    '/mlcube_io{}/{}'.format(len(mounts), host_path)
                )
                args.append('--{}={}'.format(param.name, mounts[host_path] + '/' + file_name))
            else:
                raise ConfigurationError(f"Invalid task: task={self.task}, param={param.name}, type={param.type}")

        return mounts, args

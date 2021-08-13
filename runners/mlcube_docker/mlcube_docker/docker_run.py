import os
import logging
import typing as t
from omegaconf import DictConfig
from mlcube.shell import Shell
from mlcube.errors import IllegalParameterError
from mlcube.runner import (BaseRunner, BaseConfig)


__all__ = ['Config', 'DockerRun']


logger = logging.getLogger(__name__)


class Config(BaseConfig):
    """ Helper class to manage `docker` environment configuration."""

    CONFIG_SECTION = 'docker'         # Section name in MLCube configuration file.

    class BuildStrategy(object):
        PULL = 'pull'
        AUTO = 'auto'
        ALWAYS = 'always'

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
        'build_strategy': 'pull',     # How to configure MLCube:
                                      #   'pull': never try to build, always pull
                                      #   'auto': build if image not found and dockerfile found
                                      #   'always': build even if image found
        # TODO: The above variable may be confusing. Is `configure_strategy` better? Docker uses `--pull`
        #       switch as build arg to force pulling the base image.
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

        logger.debug(f"DockerRun configuration: {str(docker_env)}")
        return docker_env


class DockerRun(BaseRunner):
    """ Docker runner. """

    PLATFORM_NAME = 'docker'

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task, Config)

    def configure(self) -> None:
        """Build Docker image on a current host."""
        image: t.Text = self.mlcube.docker.image
        context: t.Text = os.path.join(self.mlcube.runtime.root, self.mlcube.docker.build_context)
        recipe: t.Text = os.path.join(context, self.mlcube.docker.build_file)
        docker: t.Text = self.mlcube.docker.docker

        # Build strategies: `pull`, `auto` and `always`.
        build_strategy: t.Text = self.mlcube.docker.build_strategy
        build_recipe_exists: bool = os.path.exists(recipe)
        if build_strategy == Config.BuildStrategy.PULL or not build_recipe_exists:
            logger.info("Will pull image (%s) because (build_strategy=%s, build_recipe_exists=%r)",
                        image, build_strategy, build_recipe_exists)
            Shell.run(docker, 'pull', image)
            if build_recipe_exists:
                logger.warning("Docker recipe exists (%s), but your build strategy is '%s', and so the image has been "
                               "pulled, not built. Make sure your image is up-to-data with your source code.",
                               recipe, build_strategy)
        else:
            logger.info("Will build image (%s) because (build_strategy=%s, build_recipe_exists=%r)",
                        image, build_strategy, build_recipe_exists)
            build_args: t.Text = self.mlcube.docker.build_args
            Shell.run(docker, 'build', build_args, '-t', image, '-f', recipe, context)

    def run(self) -> None:
        """ Run a cube. """
        docker: t.Text = self.mlcube.docker.docker
        image: t.Text = self.mlcube.docker.image

        build_strategy: t.Text = self.mlcube.docker.build_strategy
        if build_strategy == Config.BuildStrategy.ALWAYS or not Shell.docker_image_exists(docker, image):
            logger.warning("Docker image (%s) does not exist or build strategy is 'always'. "
                           "Will run 'configure' phase.", image)
            try:
                self.configure()
            except RuntimeError:
                context: t.Text = os.path.join(self.mlcube.runtime.root, self.mlcube.docker.build_context)
                recipe: t.Text = os.path.join(context, self.mlcube.docker.build_file)
                if build_strategy == Config.BuildStrategy.PULL and os.path.exists(recipe):
                    logger.warning("MLCube configuration failed. Docker recipe (%s) exists, but your build strategy is "
                                   "set to pull. Rerun with: -Pdocker.build_strategy=auto to build image locally.",
                                   recipe)
                raise

        # The 'mounts' dictionary maps host paths to container paths
        mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Config.dict_to_cli(mounts, sep=':', parent_arg='--volume')
        env_args = self.mlcube.docker.env_args
        num_gpus: int = self.mlcube.platform.get('accelerator_count', None) or 0
        run_args: t.Text = self.mlcube.docker.cpu_args if num_gpus == 0 else self.mlcube.docker.gpu_args

        Shell.run(docker, 'run', run_args, env_args, volumes, image, ' '.join(task_args))

import os
import logging
import typing as t
from omegaconf import (DictConfig, OmegaConf)
from mlcube.shell import Shell
from mlcube.runner import (Runner, RunnerConfig)
from mlcube.errors import IllegalParameterValueError


__all__ = ['Config', 'DockerRun']

from mlcube.validate import Validate

logger = logging.getLogger(__name__)


class Config(RunnerConfig):
    """ Helper class to manage `docker` environment configuration."""

    class BuildStrategy(object):
        PULL = 'pull'
        AUTO = 'auto'
        ALWAYS = 'always'

        @staticmethod
        def validate(build_strategy: t.Text) -> None:
            if build_strategy not in ('pull', 'auto', 'always'):
                raise IllegalParameterValueError('build_strategy', build_strategy, "['pull', 'auto', 'always']")

    DEFAULT = OmegaConf.create({
        'runner': 'docker',

        'image': '${docker.image}',   # Image name.
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
    })

    @staticmethod
    def merge(mlcube: DictConfig) -> None:
        mlcube.runner = OmegaConf.merge(mlcube.runner, mlcube.get('docker', OmegaConf.create({})))

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        """ Initialize configuration from user config
        Args:
            mlcube: MLCube `container` configuration, possible merged with user local configuration.
        Return:
            Initialized configuration.
        """
        # Make sure all parameters present with their default values.
        validator = Validate(mlcube.runner, 'runner')
        _ = validator.check_unknown_keys(Config.DEFAULT.keys())\
                     .check_values(['image', 'docker', 'build_strategy'], str, blanks=False)
        Config.BuildStrategy.validate(mlcube.runner.build_strategy)

        if isinstance(mlcube.runner.build_args, DictConfig):
            mlcube.runner.build_args = Shell.to_cli_args(mlcube.runner.build_args, parent_arg='--build-arg')
        if isinstance(mlcube.runner.env_args, DictConfig):
            mlcube.runner.env_args = Shell.to_cli_args(mlcube.runner.env_args, parent_arg='-e')


class DockerRun(Runner):
    """ Docker runner. """

    CONFIG = Config

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task)

    def configure(self) -> None:
        """Build Docker image on a current host."""
        image: t.Text = self.mlcube.runner.image
        context: t.Text = os.path.join(self.mlcube.runtime.root, self.mlcube.runner.build_context)
        recipe: t.Text = os.path.join(context, self.mlcube.runner.build_file)
        docker: t.Text = self.mlcube.runner.docker

        # Build strategies: `pull`, `auto` and `always`.
        build_strategy: t.Text = self.mlcube.runner.build_strategy
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
            build_args: t.Text = self.mlcube.runner.build_args
            Shell.run(docker, 'build', build_args, '-t', image, '-f', recipe, context)

    def run(self) -> None:
        """ Run a cube. """
        docker: t.Text = self.mlcube.runner.docker
        image: t.Text = self.mlcube.runner.image

        build_strategy: t.Text = self.mlcube.runner.build_strategy
        if build_strategy == Config.BuildStrategy.ALWAYS or not Shell.docker_image_exists(docker, image):
            logger.warning("Docker image (%s) does not exist or build strategy is 'always'. "
                           "Will run 'configure' phase.", image)
            try:
                self.configure()
            except RuntimeError:
                context: t.Text = os.path.join(self.mlcube.runtime.root, self.mlcube.runner.build_context)
                recipe: t.Text = os.path.join(context, self.mlcube.runner.build_file)
                if build_strategy == Config.BuildStrategy.PULL and os.path.exists(recipe):
                    logger.warning("MLCube configuration failed. Docker recipe (%s) exists, but your build strategy is "
                                   "set to pull. Rerun with: -Prunner.build_strategy=auto to build image locally.",
                                   recipe)
                raise
        # Deal with user-provided workspace
        Shell.sync_workspace(self.mlcube, self.task)

        # The 'mounts' dictionary maps host paths to container paths
        mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Shell.to_cli_args(mounts, sep=':', parent_arg='--volume')
        env_args = self.mlcube.runner.env_args
        num_gpus: int = self.mlcube.platform.get('accelerator_count', None) or 0
        run_args: t.Text = self.mlcube.runner.cpu_args if num_gpus == 0 else self.mlcube.runner.gpu_args

        Shell.run(docker, 'run', run_args, env_args, volumes, image, ' '.join(task_args))

import os
import shlex
import logging
import typing as t
from pathlib import Path
from omegaconf import (DictConfig, OmegaConf)
from mlcube.shell import Shell
from mlcube.runner import (Runner, RunnerConfig)
from mlcube.errors import (IllegalParameterValueError, ExecutionError, ConfigurationError)


__all__ = ['Config', 'DockerRun']

from mlcube.validate import Validate

logger = logging.getLogger(__name__)


class Config(RunnerConfig):
    """ Helper class to manage `docker` environment configuration."""

    class BuildStrategy(object):
        """MLCube docker runner configuration strategy.

        The build strategy describes process of build/pulling docker images for MLCubes:
            - `run`: Call 'configure' when build strategy is `always`, or docker image does not exist.
            - `configure`: Pull image if build strategy is pull or docker recipe (Dockerfile) exists. Else, build image.
        """

        PULL = 'pull'
        """Pull images from remote docker hubs.
        
        Docker images are never built locally even if Dockerfiles exist (MLCube runner will log the warning message
        when this case is detected). This is the default value for the build strategy. This results in some 
        consequences: when users clone an MLCube source from GitHub, mlcube will pull the image defined in mlcube.yaml,
        and will not build it locally from sources. This is OK as long as source files have not changed since the docker
        image has been built for this MLCube and pushed to docker hub. If files have changed, and version of the docker 
        image in mlcube.yaml has not been updated, and this image exists on docker hub, the MLCube implementation that
        MLCube will run will not be consistent with source files.
        """

        AUTO = 'auto'
        """Automatically identify if docker images can be built locally, if not, pull them from docker hub."""

        ALWAYS = 'always'
        """Build docker images before execution of each task.
        
        Technically this means call `configure` command each time a task is executed. Currently, MLCube docker runner 
        just runs the `docker build ...` command without instructing docker to rebuild the whole image. This means that 
        docker may decided that it does not need to rebuild the respective image. This behavior can be overridden by 
        providing custom build_args flags (`build_args: "--no-cache"` or `build_args: "--no-cache --pull"` to force 
        re-download the base image layers. 
        ).
        """

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
        if 'runner' not in mlcube:
            mlcube['runner'] = {}
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

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Optional[t.Text]) -> None:
        super().__init__(mlcube, task)

    def configure(self) -> None:
        """Build Docker image on a current host."""
        image: t.Text = self.mlcube.runner.image
        context: t.Text = os.path.abspath(os.path.join(self.mlcube.runtime.root, self.mlcube.runner.build_context))
        recipe: t.Text = os.path.abspath(os.path.join(context, self.mlcube.runner.build_file))
        docker: t.Text = self.mlcube.runner.docker

        # Build strategies: `pull`, `auto` and `always`.
        build_strategy: t.Text = self.mlcube.runner.build_strategy
        build_recipe_exists: bool = os.path.exists(recipe)
        if build_strategy == Config.BuildStrategy.PULL or not build_recipe_exists:
            logger.info("Will pull image (%s) because (build_strategy=%s, build_recipe_exists=%r)",
                        image, build_strategy, build_recipe_exists)
            if build_recipe_exists:
                logger.warning(
                    "Docker recipe exists (%s), but your build strategy is `%s`, and so the image will be pulled, not "
                    "built. Make sure your image is up-to-date with your source code. If you want to rebuilt MLCube "
                    "docker image locally, rerun with `-Prunner.build_strategy=always`.",
                    recipe, build_strategy
                )
            try:
                Shell.run([docker, 'pull', image])
            except ExecutionError as err:
                description = f"Error occurred while pulling docker image (docker={docker}, image={image})."
                if build_recipe_exists:
                    description += \
                        f" By the way, docker recipe ({recipe}) exists, but your build strategy is set to "\
                        "pull. Consider rerunning with: `-Prunner.build_strategy=auto` to build image locally."
                raise ExecutionError.mlcube_configure_error(self.__class__.__name__, description, **err.context)

        else:
            logger.info("Will build image (%s) because (build_strategy=%s, build_recipe_exists=%r)",
                        image, build_strategy, build_recipe_exists)
            build_args: t.Text = self.mlcube.runner.build_args
            try:
                Shell.run([docker, 'build', build_args, '-t', image, '-f', recipe, context])
            except ExecutionError as err:
                raise ExecutionError.mlcube_configure_error(
                    self.__class__.__name__,
                    f"Error occurred while building docker image (docker={docker}, build_args={build_args}, "
                    f"image={image}, recipe={recipe}, context={context}).",
                    **err.context
                )

    def run(self) -> None:
        """ Run a cube. """
        docker: t.Text = self.mlcube.runner.docker
        image: t.Text = self.mlcube.runner.image

        build_strategy: t.Text = self.mlcube.runner.build_strategy
        if build_strategy == Config.BuildStrategy.ALWAYS or not Shell.docker_image_exists(docker, image):
            logger.warning("Docker image (%s) does not exist or build strategy is 'always'. "
                           "Will run 'configure' phase.", image)
            self.configure()
        # Deal with user-provided workspace
        try:
            Shell.sync_workspace(self.mlcube, self.task)
        except Exception as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while syncing MLCube workspace (task={self.task}). Actual error is {type(err)} - see "
                "context for details.",
                error=str(err),
                worspace=self.mlcube.runtime.workspace,
                mlcube=OmegaConf.to_container(self.mlcube),
                task=self.task
            )

        # The 'mounts' dictionary maps host paths to container paths
        try:
            # The `task_args` list will always contain task name as its first element.
            mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
        except ConfigurationError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while generating mount points for docker run command (task={self.task}). See context "
                "for details and check your MLCube configuration file.",
                error=str(err)
            )
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Shell.to_cli_args(mounts, sep=':', parent_arg='--volume')
        env_args = self.mlcube.runner.env_args
        num_gpus: int = self.mlcube.get('platform', {}).get('accelerator_count', None) or 0

        run_args: t.Text = self.mlcube.runner.cpu_args if num_gpus == 0 else self.mlcube.runner.gpu_args
        if 'entrypoint' in self.mlcube.tasks[self.task] and (not self.mlcube.tasks[self.task].entrypoint.isspace()):
            logger.info(
                "Using custom task entrypoint: task=%s, entrypoint='%s'",
                self.task, self.mlcube.tasks[self.task].entrypoint
            )
            # TODO: What if entrypoints contain whitespaces?
            if " " in  self.mlcube.tasks[self.task].entrypoint:
               # use first item in entry point list as the executable to specify in docker run --entrypoint
               run_args += f" --entrypoint={shlex.split(self.mlcube.tasks[self.task].entrypoint)[0]}" 
               
            else:
               run_args += f" --entrypoint={self.mlcube.tasks[self.task].entrypoint}"
            # Remove task name. According to MLCube rules, custom entry points do not require task name as their
            # first positional arguments.
            # Check whether the mlcube --task matches the stem of the .py or .sh file specified in --entrypoint
            if task_args[0] == Path(shlex.split(self.mlcube.tasks[self.task].entrypoint)[1]).stem : 
              _ = task_args.pop(0)
            else:
                # the mlcube --task does not match the stem of the .py or .sh file specified in --entrypoint 
                logger.info("the mlcube --task does not match the stem of the entry point %s specified in mlcube.yaml",
                             Path(shlex.split(self.mlcube.tasks[self.task].entrypoint)[1]).stem)
            
        try:
            if 'entrypoint' in self.mlcube.tasks[self.task] and (not self.mlcube.tasks[self.task].entrypoint.isspace()): 
              Shell.run([docker, 'run', run_args, env_args, volumes, image, shlex.split(self.mlcube.tasks[self.task].entrypoint)[1],' '.join(task_args)])
            else:
              Shell.run([docker, 'run', run_args, env_args, volumes, image, ' '.join(task_args)])

        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task (docker={docker}, run_args={run_args}, env_args={env_args}, "
                f"volumes={volumes}, image={image}, task_args={task_args}).",
                **err.context
            )

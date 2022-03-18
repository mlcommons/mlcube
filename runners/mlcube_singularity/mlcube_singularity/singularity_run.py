import os
import logging
import typing as t
from omegaconf import DictConfig, OmegaConf
from mlcube.shell import Shell
from mlcube.runner import (Runner, RunnerConfig)


__all__ = ['Config', 'SingularityRun']

from mlcube.validate import Validate

logger = logging.getLogger(__name__)


class Config(RunnerConfig):
    """ Helper class to manage `singularity` environment configuration."""

    DEFAULT = OmegaConf.create({
        'runner': 'singularity',                           # Name of this runner.

        'image': '${singularity.image}',                   # Path to Singularity image, relative to ${image_dir}.
        'image_dir': '${runtime.workspace}/.image',        # Root image directory for the image.

        'singularity': 'singularity',                      # Executable file for singularity runtime.

        'build_args': '--fakeroot',                        # Image build arguments.
        # Sergey: there seems to be a better name for this parameter. Originally, the only source was a singularity
        # recipe (build file). Later, MLCube started to support other sources, such as docker images.
        'build_file': 'Singularity.recipe'                 # Source for the image build process.
    })

    @staticmethod
    def merge(mlcube: DictConfig) -> None:
        """Merge current (mostly default) configuration with configuration from MLCube yaml file.
        Args:
            mlcube: Current MLCube configuration. Contains all fields from MLCube configuration file (YAML) including
                platform-specific configuration sections (docker/singularity). In addition, this dictionary contains
                'runtime' configuration (`root` and `workspace`), and `runner` configuration that contains default
                runner configuration (Singularity in this case) from system settings file (it is exact or modified
                version of `Config.DEFAULT` dictionary to account for user local environment).
        Idea is that if mlcube contains `singularity` section, then it means that we use it as is. Else, we can try
        to run this MLCube using information from `docker` section if it exists.
        """
        s_cfg: t.Optional[DictConfig] = mlcube.get('singularity', None)
        if not s_cfg:
            # Singularity runner will try to use docker section. At this point, it will work as long as we assume we
            # pull docker images from a docker hub.
            logger.warning("Singularity configuration not found in MLCube file (singularity=%s).", str(s_cfg))

            d_cfg = mlcube.get('docker', None)
            if not d_cfg:
                logger.warning("Docker configuration not found too. Singularity runner will likely fail to run.")
                return

            # The idea is that we can use the remote docker image as a source for the build process, automatically
            # generating an image name in a local environment. Key here is that the source has a scheme - `docker://`
            s_cfg = OmegaConf.create(dict(
                image=''.join(c for c in d_cfg['image'] if c.isalnum()) + '.sif',
                build_file='docker://' + d_cfg['image']
            ))
            logger.info(f"Singularity runner has converted docker configuration into singularity (%s).",
                        str(OmegaConf.to_container(s_cfg)))

        mlcube.runner = OmegaConf.merge(mlcube.runner, s_cfg)

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        validator = Validate(mlcube.runner, 'runner')
        validator.check_unknown_keys(Config.DEFAULT.keys())\
                 .check_values(['image', 'image_dir', 'singularity'], str, blanks=False)


class SingularityRun(Runner):

    CONFIG = Config

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task)

    def configure(self) -> None:
        """Build Singularity Image on a current host."""
        s_cfg: DictConfig = self.mlcube.runner

        # Get full path to a singularity image. By design, we compute it relative to {mlcube.root}/workspace.
        image_uri: t.Text = os.path.join(s_cfg.image_dir, s_cfg.image)
        if os.path.exists(image_uri):
            logger.info("Image found (%s).", image_uri)
            return
        # Make sure a directory to store image exists. If paths are like "/opt/...", the call may fail.
        os.makedirs(os.path.dirname(image_uri), exist_ok=True)

        # Let's assume that build context is the root MLCube directory
        recipe_path: t.Text = self.mlcube.runtime.root
        if s_cfg.build_file.startswith('docker://'):
            # https://sylabs.io/guides/3.0/user-guide/build_a_container.html
            # URI beginning with docker:// to build from Docker Hub
            ...
        else:
            recipe_file: t.Text = os.path.join(recipe_path, s_cfg.build_file)
            if not os.path.exists(recipe_file):
                raise IOError(f"Singularity recipe not found: {recipe_file}")
        Shell.run(
            'cd', recipe_path, ';',
            s_cfg.singularity, 'build', s_cfg.build_args, image_uri, s_cfg.build_file
        )

    def run(self) -> None:
        """  """
        image_uri: t.Text = os.path.join(self.mlcube.runner.image_dir, self.mlcube.runner.image)
        if not os.path.exists(image_uri):
            self.configure()

        # Deal with user-provided workspace
        Shell.sync_workspace(self.mlcube, self.task)

        mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Shell.to_cli_args(mounts, sep=':', parent_arg='--bind')

        Shell.run(self.mlcube.runner.singularity, 'run', volumes, image_uri, ' '.join(task_args))

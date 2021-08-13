import os
import logging
import typing as t
from omegaconf import DictConfig, OmegaConf
from mlcube.errors import IllegalParameterError
from mlcube.shell import Shell
from mlcube.runner import (BaseRunner, BaseConfig)


__all__ = ['Config', 'SingularityRun']


logger = logging.getLogger(__name__)


class Config(BaseConfig):
    """ Helper class to manage `singularity` environment configuration."""

    CONFIG_SECTION = 'singularity'

    DEFAULT_CONFIG = {
        'image': '???',
        'image_dir': '${runtime.workspace}/.image',

        'singularity': 'singularity',

        'build_args': '--fakeroot',
        'build_file': 'Singularity.recipe'
    }

    @staticmethod
    def from_dict(singularity_env: DictConfig) -> DictConfig:
        """ Initialize singularity configuration from user config
        Args:
            singularity_env: MLCube `singularity` configuration, possible merged with user local configuration.
        Return:
            Initialized configuration.
        """
        # Make sure all parameters present with their default values.
        for name, value in Config.DEFAULT_CONFIG.items():
            singularity_env[name] = singularity_env.get(name, None) or value

        if not singularity_env.image:
            raise IllegalParameterError(f'{Config.CONFIG_SECTION}.image', singularity_env.image)

        logger.info(f"SingularityRun configuration: {str(singularity_env)}")
        return singularity_env


class SingularityRun(BaseRunner):

    PLATFORM_NAME = 'singularity'

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task, Config)

    def configure(self) -> None:
        """Build Singularity Image on a current host."""
        s_cfg: DictConfig = self.mlcube.singularity

        # Get full path to a singularity image. By design, we compute it relative to {mlcube.root}/workspace.
        image_uri: t.Text = os.path.join(s_cfg.image_dir, s_cfg.image)
        if os.path.exists(image_uri):
            logger.info("Image found (%s).", image_uri)
            return
        # Make sure a directory to store image exists. If paths are like "/opt/...", the call may fail.
        os.makedirs(os.path.dirname(image_uri), exist_ok=True)

        # Let's assume build context is the root MLCube directory
        recipe_path: t.Text = self.mlcube.runtime.root
        recipe_file: t.Text = os.path.join(recipe_path, s_cfg.build_file)
        if not os.path.exists(recipe_file):
            raise IOError(f"Singularity recipe not found: {recipe_file}")
        Shell.run(
            'cd', recipe_path, ';',
            s_cfg.singularity, 'build', s_cfg.build_args, image_uri, s_cfg.build_file
        )

    def run(self) -> None:
        """  """
        s_cfg: DictConfig = self.mlcube.singularity
        image_uri: t.Text = os.path.join(s_cfg.image_dir, s_cfg.image)
        if not os.path.exists(image_uri):
            self.configure()

        mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Config.dict_to_cli(mounts, sep=':', parent_arg='--bind')

        Shell.run(s_cfg.singularity, 'run', volumes, image_uri, ' '.join(task_args))

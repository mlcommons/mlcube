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
        'runner': 'singularity',

        'image': '${singularity.image}',
        'image_dir': '${runtime.workspace}/.image',

        'singularity': 'singularity',

        'build_args': '--fakeroot',
        'build_file': 'Singularity.recipe'
    })

    @staticmethod
    def merge(mlcube: DictConfig) -> None:
        mlcube.runner = OmegaConf.merge(mlcube.runner, mlcube.get('singularity', OmegaConf.create({})))

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
        image_uri: t.Text = os.path.join(self.mlcube.runner.image_dir, self.mlcube.runner.image)
        if not os.path.exists(image_uri):
            self.configure()

        # Deal with user-provided workspace
        Shell.sync_workspace(self.mlcube, self.task)

        mounts, task_args = Shell.generate_mounts_and_args(self.mlcube, self.task)
        logger.info(f"mounts={mounts}, task_args={task_args}")

        volumes = Shell.to_cli_args(mounts, sep=':', parent_arg='--bind')

        Shell.run(self.mlcube.runner.singularity, 'run', volumes, image_uri, ' '.join(task_args))

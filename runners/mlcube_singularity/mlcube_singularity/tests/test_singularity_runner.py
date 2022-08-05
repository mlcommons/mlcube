from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import TestCase
from unittest.mock import patch, mock_open

from mlcube.config import MLCubeConfig
from mlcube.shell import Shell
from mlcube_singularity.singularity_run import Config, SingularityRun

from omegaconf import DictConfig, OmegaConf

from spython.utils.terminal import (
    check_install as check_singularity_installed,
)

_HAVE_SINGULARITY: bool = check_singularity_installed(software='singularity')

_IMAGE_DIRECTORY: Path = Path(tempfile.mkdtemp())

_MLCUBE_DEFAULT_ENTRY_POINT = """
singularity:
  image: ubuntu-18.04.sif
  image_dir: {IMAGE_DIRECTORY}
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  pwd: {parameters: {inputs: {}, outputs: {}}}
""".replace('{IMAGE_DIRECTORY}', _IMAGE_DIRECTORY.as_posix())


class TestSingularityRunner(TestCase):
    """Test singularity runner.

    Run these tests with `pytest -s` to see the output of task executions to confirm they work.
    """

    @staticmethod
    def noop(*args, **kwargs) -> None:
        ...

    def setUp(self) -> None:
        self.sync_workspace = Shell.sync_workspace
        Shell.sync_workspace = TestSingularityRunner.noop

        if _HAVE_SINGULARITY:
            if not _IMAGE_DIRECTORY.exists():
                _IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
            Shell.run(
                ['singularity', 'build', (_IMAGE_DIRECTORY / 'ubuntu-18.04.sif').as_posix(), 'docker://ubuntu:18.04'],
                on_error='raise'
            )

    def tearDown(self) -> None:
        Shell.sync_workspace = self.sync_workspace
        if _IMAGE_DIRECTORY.exists():
            shutil.rmtree(_IMAGE_DIRECTORY.as_posix())

    @unittest.skipUnless(_HAVE_SINGULARITY, reason="No singularity available.")
    def test_mlcube_default_entrypoints(self):
        with patch("io.open", mock_open(read_data=_MLCUBE_DEFAULT_ENTRY_POINT)):
            mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
                "/some/path/to/mlcube.yaml", runner_config=Config.DEFAULT, runner_cls=SingularityRun
            )
        self.assertEqual(mlcube.runner.image, 'ubuntu-18.04.sif')
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                'ls': {'parameters': {'inputs': {}, 'outputs': {}}},
                'pwd': {'parameters': {'inputs': {}, 'outputs': {}}}
            }
        )
        SingularityRun(mlcube, task=None).configure()
        SingularityRun(mlcube, task='ls').run()
        SingularityRun(mlcube, task='pwd').run()

"""Unit tests for singularity runner.

There's no automatic validation of test outputs now. Run tests with `pytest -s --log-cli-level=10` command to see
all MLCube logs. In particular, for TestSingularityRunner::test_mlcube_custom_entrypoints tests one should see that
indeed custom entry points are used. The log will contain the following lines:
```shell
mlcube_singularity.singularity_run:singularity_run.py:229 Using custom task entrypoint:
    task=free, entrypoint='/usr/bin/free'
mlcube.shell:shell.py:99 Command='singularity exec   /tmp/tmpljhf3drp/ubuntu-18.04.sif /usr/bin/free ' ...
```
When custom entrypoints are not used, singularity uses `run` command instead of `exec`.
"""
import shutil
import tempfile
import typing as t
import unittest
from pathlib import Path
from unittest import TestCase
from unittest.mock import (mock_open, patch)

from mlcube.config import MLCubeConfig
from mlcube.shell import Shell

from mlcube_singularity.singularity_run import (Config, SingularityRun)

from omegaconf import DictConfig, OmegaConf

from spython.utils.terminal import check_install as check_singularity_installed


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


_MLCUBE_CUSTOM_ENTRY_POINTS = """
singularity:
  image: ubuntu-18.04.sif
  image_dir: {IMAGE_DIRECTORY}
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  free: {entrypoint: '/usr/bin/free', parameters: {inputs: {}, outputs: {}}}
""".replace('{IMAGE_DIRECTORY}', _IMAGE_DIRECTORY.as_posix())

_sync_workspace_fn: t.Optional[t.Callable] = None


class TestSingularityRunner(TestCase):
    """Test singularity runner.

    Run these tests with `pytest -s` to see the output of task executions to confirm they work.
    """

    @staticmethod
    def noop(*args, **kwargs) -> None:
        ...

    @classmethod
    def setUpClass(cls) -> None:
        global _sync_workspace_fn
        _sync_workspace_fn = Shell.sync_workspace
        Shell.sync_workspace = TestSingularityRunner.noop

        if _HAVE_SINGULARITY:
            if not _IMAGE_DIRECTORY.exists():
                _IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
            Shell.run(
                ['singularity', 'build', (_IMAGE_DIRECTORY / 'ubuntu-18.04.sif').as_posix(), 'docker://ubuntu:18.04'],
                on_error='raise'
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if _sync_workspace_fn is not None:
            Shell.sync_workspace = _sync_workspace_fn
        if _IMAGE_DIRECTORY.exists():
            shutil.rmtree(_IMAGE_DIRECTORY.as_posix())

    @unittest.skipUnless(_HAVE_SINGULARITY, reason="No singularity available.")
    @patch("io.open", mock_open(read_data=_MLCUBE_DEFAULT_ENTRY_POINT))
    def test_mlcube_default_entrypoints(self):
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

    @unittest.skipUnless(_HAVE_SINGULARITY, reason="No singularity available.")
    @patch("io.open", mock_open(read_data=_MLCUBE_CUSTOM_ENTRY_POINTS))
    def test_mlcube_custom_entrypoints(self):
        mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
            "/some/path/to/mlcube.yaml", runner_config=Config.DEFAULT, runner_cls=SingularityRun
        )
        self.assertEqual(mlcube.runner.image, 'ubuntu-18.04.sif')
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                'ls': {'parameters': {'inputs': {}, 'outputs': {}}},
                'free': {'entrypoint': '/usr/bin/free', 'parameters': {'inputs': {}, 'outputs': {}}}
            }
        )
        SingularityRun(mlcube, task=None).configure()
        SingularityRun(mlcube, task='ls').run()
        SingularityRun(mlcube, task='free').run()

import unittest
from unittest import TestCase
from unittest.mock import (mock_open, patch)

from omegaconf import DictConfig, OmegaConf

from mlcube.config import MLCubeConfig
from mlcube.shell import Shell

from mlcube_docker.docker_run import (Config, DockerRun)

_HAVE_DOCKER: bool = Shell.run(['docker', '--version'], on_error='ignore') == 0

_MLCUBE_DEFAULT_ENTRY_POINT = """
docker:
  image: ubuntu:18.04
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  pwd: {parameters: {inputs: {}, outputs: {}}}
"""


class TestDockerRunner(TestCase):

    @staticmethod
    def noop(*args, **kwargs) -> None:
        ...

    def setUp(self) -> None:
        self.sync_workspace = Shell.sync_workspace
        Shell.sync_workspace = TestDockerRunner.noop

    def tearDown(self) -> None:
        Shell.sync_workspace = self.sync_workspace

    @unittest.skipUnless(_HAVE_DOCKER, reason="No docker available.")
    @patch("io.open", mock_open(read_data=_MLCUBE_DEFAULT_ENTRY_POINT))
    def test_mlcube_default_entrypoints(self):
        mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
            "/some/path/to/mlcube.yaml", runner_config=Config.DEFAULT, runner_cls=DockerRun
        )
        self.assertEqual(mlcube.runner.image, 'ubuntu:18.04')
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                'ls': {'parameters': {'inputs': {}, 'outputs': {}}},
                'pwd': {'parameters': {'inputs': {}, 'outputs': {}}}
            }
        )

        DockerRun(mlcube, task=None).configure()
        DockerRun(mlcube, task='ls').run()
        DockerRun(mlcube, task='pwd').run()

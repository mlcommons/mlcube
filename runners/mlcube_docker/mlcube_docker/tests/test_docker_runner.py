import typing as t
import unittest
from unittest import TestCase
from unittest.mock import mock_open, patch

from mlcube_docker.docker_run import Config, DockerRun
from omegaconf import DictConfig, OmegaConf

from mlcube.config import MLCubeConfig
from mlcube.shell import Shell

_HAVE_DOCKER: bool = Shell.run(["docker", "--version"], on_error="ignore") == 0

_MLCUBE_DEFAULT_ENTRY_POINT = """
docker:
  image: ubuntu:18.04
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  pwd: {parameters: {inputs: {}, outputs: {}}}
"""

_MLCUBE_CUSTOM_ENTRY_POINTS = """
docker:
  image: ubuntu:18.04
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  free: {entrypoint: '/usr/bin/free', parameters: {inputs: {}, outputs: {}}}
"""


class TestDockerRunner(TestCase):
    def _check_inspect_output(self, info: t.Dict) -> None:
        self.assertIsInstance(info, dict)
        self.assertIn("hash", info)
        self.assertFalse(info["hash"].startswith("sha256:"))

    @staticmethod
    def noop(*args, **kwargs) -> None:
        ...

    def setUp(self) -> None:
        """Configure testing environment.

        Some unit tests patch the `io.open` function to bypass file-reading routine and use MLCube configuration
        instead, which is stored in memory (e.g. _MLCUBE_DEFAULT_ENTRY_POINT). In this case I provide a fake path
        (/some/path/to/mlcube.yaml) for the `MLCubeConfig.create_mlcube_config` method. Later, when this test runs
        MLCubes, workspace is synced what results in an error (PermissionDenied). And we do not want to sync workspaces
        anyway. So, here I manually patch the `Shell.sync_workspace` method making it a no-operations (noop) method
        (could not figure out how to do it with @patch decorator).
        """
        self.sync_workspace = Shell.sync_workspace
        Shell.sync_workspace = TestDockerRunner.noop

    def tearDown(self) -> None:
        Shell.sync_workspace = self.sync_workspace

    @unittest.skipUnless(_HAVE_DOCKER, reason="No docker available.")
    def test_mlcube_default_entrypoints(self):
        with patch("io.open", mock_open(read_data=_MLCUBE_DEFAULT_ENTRY_POINT)):
            mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
                "/some/path/to/mlcube.yaml",
                runner_config=Config.DEFAULT,
                runner_cls=DockerRun,
            )
        self.assertEqual(mlcube.runner.image, "ubuntu:18.04")
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                "ls": {"parameters": {"inputs": {}, "outputs": {}}},
                "pwd": {"parameters": {"inputs": {}, "outputs": {}}},
            },
        )

        DockerRun(mlcube, task=None).configure()
        self._check_inspect_output(DockerRun(mlcube, task=None).inspect())
        DockerRun(mlcube, task="ls").run()
        DockerRun(mlcube, task="pwd").run()

    @unittest.skipUnless(_HAVE_DOCKER, reason="No docker available.")
    def test_mlcube_custom_entrypoints(self):
        with patch("io.open", mock_open(read_data=_MLCUBE_CUSTOM_ENTRY_POINTS)):
            mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
                "/some/path/to/mlcube.yaml",
                runner_config=Config.DEFAULT,
                runner_cls=DockerRun,
            )
        self.assertEqual(mlcube.runner.image, "ubuntu:18.04")
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                "ls": {"parameters": {"inputs": {}, "outputs": {}}},
                "free": {
                    "entrypoint": "/usr/bin/free",
                    "parameters": {"inputs": {}, "outputs": {}},
                },
            },
        )

        DockerRun(mlcube, task=None).configure()
        self._check_inspect_output(DockerRun(mlcube, task=None).inspect())
        DockerRun(mlcube, task="ls").run()
        DockerRun(mlcube, task="free").run()

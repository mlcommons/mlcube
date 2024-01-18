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
from io import open
from pathlib import Path
from unittest import TestCase
from unittest.mock import mock_open, patch

from mlcube_singularity.singularity_client import Client
from mlcube_singularity.singularity_run import Config, SingularityRun
from omegaconf import DictConfig, OmegaConf

from mlcube.config import MLCubeConfig
from mlcube.errors import ExecutionError
from mlcube.shell import Shell


try:
    client = Client.from_env()
    client.init()
except ExecutionError:
    client = None

_IMAGE_DIRECTORY: Path = Path(tempfile.mkdtemp())


_MLCUBE_DEFAULT_ENTRY_POINT = """
singularity:
  image: ubuntu-18.04.sif
  image_dir: {IMAGE_DIRECTORY}
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  pwd: {parameters: {inputs: {}, outputs: {}}}
""".replace(
    "{IMAGE_DIRECTORY}", _IMAGE_DIRECTORY.as_posix()
)


_MLCUBE_CUSTOM_ENTRY_POINTS = """
singularity:
  image: ubuntu-18.04.sif
  image_dir: {IMAGE_DIRECTORY}
tasks:
  ls: {parameters: {inputs: {}, outputs: {}}}
  free: {entrypoint: '/usr/bin/free', parameters: {inputs: {}, outputs: {}}}
""".replace(
    "{IMAGE_DIRECTORY}", _IMAGE_DIRECTORY.as_posix()
)


_MLCUBE_CONFIG_FILE = "/some/path/to/mlcube.yaml"
"""We will be mocking io.open call only for this file path."""

_io_open = open
"""Original function we will be mocking in these unit tests."""


def get_custom_mock_open(file_path_to_mock: str, read_data: str) -> t.Callable:
    """Function to help mock `io.open` only for this specific file path.

    Original implementation:
    https://stackoverflow.com/questions/67234524/python-unittest-mock-open-specific-paths-dont-mock-others

    Args:
        file_path_to_mock: Only mock the `io.open` call for this path. For others, call original `io.open`.
        read_data: Content for the `file_path_to_mock` file.

    """
    def mocked_open() -> t.Callable:
        def conditional_open_fn(path, *args, **kwargs):
            if path == file_path_to_mock:
                return mock_open(read_data=read_data)()
            return _io_open(path, *args, **kwargs)
        return conditional_open_fn
    return mocked_open


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

        if client:
            if not _IMAGE_DIRECTORY.exists():
                _IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
            client.build(
                Path.cwd().as_posix(),
                "docker://ubuntu:18.04",
                _IMAGE_DIRECTORY.as_posix(),
                "ubuntu-18.04.sif",
                build_args="",
            )
            # Shell.run(
            #     ['singularity', 'build', (_IMAGE_DIRECTORY / 'ubuntu-18.04.sif').as_posix(), 'docker://ubuntu:18.04'],
            #     on_error='raise'
            # )

    @classmethod
    def tearDownClass(cls) -> None:
        if _sync_workspace_fn is not None:
            Shell.sync_workspace = _sync_workspace_fn
        if _IMAGE_DIRECTORY.exists():
            shutil.rmtree(_IMAGE_DIRECTORY.as_posix())

    @unittest.skipUnless(client is not None, reason="No singularity available.")
    def test_mlcube_default_entrypoints(self):
        with patch("io.open", new_callable=get_custom_mock_open(_MLCUBE_CONFIG_FILE, _MLCUBE_DEFAULT_ENTRY_POINT)):
            mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
                _MLCUBE_CONFIG_FILE,
                runner_config=Config.DEFAULT,
                runner_cls=SingularityRun,
            )
        self.assertEqual(mlcube.runner.image, "ubuntu-18.04.sif")
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                "ls": {"parameters": {"inputs": {}, "outputs": {}}},
                "pwd": {"parameters": {"inputs": {}, "outputs": {}}},
            },
        )
        SingularityRun(mlcube, task=None).configure()
        SingularityRun(mlcube, task="ls").run()
        SingularityRun(mlcube, task="pwd").run()

    @unittest.skipUnless(client is not None, reason="No singularity available.")
    def test_mlcube_custom_entrypoints(self):
        with patch("io.open", new_callable=get_custom_mock_open(_MLCUBE_CONFIG_FILE, _MLCUBE_CUSTOM_ENTRY_POINTS)):
            mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
                _MLCUBE_CONFIG_FILE,
                runner_config=Config.DEFAULT,
                runner_cls=SingularityRun,
            )
        self.assertEqual(mlcube.runner.image, "ubuntu-18.04.sif")
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
        SingularityRun(mlcube, task=None).configure()
        SingularityRun(mlcube, task="ls").run()
        SingularityRun(mlcube, task="free").run()

    @unittest.skipUnless(client is not None, reason="No singularity available.")
    def test_mlcube_no_singularity_section_config(self):
        mlcube: t.Union[DictConfig, t.Dict] = MLCubeConfig.create_mlcube_config(
            (Path(__file__).parent / "resources" / "docker_mlcube.yaml").as_posix(),
            runner_config=Config.DEFAULT,
            runner_cls=SingularityRun,
        )
        self.assertIsInstance(mlcube, DictConfig)

        mlcube = OmegaConf.to_container(mlcube, resolve=True)
        self.assertIsInstance(mlcube, dict)

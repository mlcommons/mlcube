from click.testing import CliRunner
from mlcube_docker.__main__ import cli


runner = CliRunner()


def test_mlcube_docker():
    from mlcube.tests.test_mlcommons_mlcube_cli import test_mlcube
    test_mlcube()

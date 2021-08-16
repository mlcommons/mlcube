from click.testing import CliRunner


runner = CliRunner()


def test_mlcube_docker():
    from mlcube.tests.test_mlcommons_mlcube_cli import test_mlcube
    test_mlcube()

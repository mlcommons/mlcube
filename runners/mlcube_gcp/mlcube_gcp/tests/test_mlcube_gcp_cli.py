from click.testing import CliRunner
from mlcube_gcp.__main__ import cli

runner = CliRunner()


def test_mlcube_gcp():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube_gcp [OPTIONS] COMMAND [ARGS]...' in response.output
    assert "Run MLCube ML workload in the remote environment." in response.output

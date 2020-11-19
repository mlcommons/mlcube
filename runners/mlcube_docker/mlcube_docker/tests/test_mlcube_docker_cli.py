from click.testing import CliRunner
from mlcube_docker.__main__ import cli


runner = CliRunner()


def test_mlcube_docker():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube_docker [OPTIONS] COMMAND [ARGS]...' in response.output
    assert '  configure  Configure docker environment for MLCube ML workload.' in response.output
    assert '  run        Run MLCube ML workload in the docker environment.' in response.output

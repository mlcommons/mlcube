from click.testing import CliRunner
from mlcube_ssh.__main__ import cli


runner = CliRunner()


def test_mlcube_ssh():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube_ssh [OPTIONS] COMMAND [ARGS]...' in response.output
    assert '  configure  Configure remote environment for MLCube ML workload.' in response.output
    assert '  run        Run MLCube ML workload in the remote environment.' in response.output

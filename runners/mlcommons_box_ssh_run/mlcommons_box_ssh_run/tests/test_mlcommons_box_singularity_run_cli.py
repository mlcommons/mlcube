from click.testing import CliRunner
from mlcommons_box_ssh_run.__main__ import cli


runner = CliRunner()


def test_mlcommons_box_ssh_run():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcommons_box_ssh_run [OPTIONS] COMMAND [ARGS]...' in response.output
    assert '  configure  Configure remote environment for MLCommons-Box ML workload.' in response.output
    assert '  run        Run MLCommons-Box ML workload in the remote environment.' in response.output

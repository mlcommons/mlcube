from click.testing import CliRunner
from mlcube_singularity.__main__ import cli


runner = CliRunner()


def test_mlcube_singularity():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube_singularity [OPTIONS] COMMAND [ARGS]...' in response.output
    assert '  configure  Configure singularity environment for MLCommons-Box ML workload.' in response.output
    assert '  run        Run MLCommons-Box ML workload in the singularity environment.' in response.output

from click.testing import CliRunner

from mlcube.__main__ import cli

runner = CliRunner()


def test_mlcube():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube [OPTIONS] COMMAND [ARGS]...' in response.output
    assert '--log-level, --log_level [critical|error|warning|info|debug]' in response.output
    assert '--help                      Show help message and exit.' in response.output
    assert 'run          Run MLCube task(s).' in response.output
    assert 'show_config  Show effective MLCube configuration.' in response.output
    print("All assertions passed")

from click.testing import CliRunner
from mlcube.main import cli

runner = CliRunner()


def test_mlcube():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube [OPTIONS] COMMAND [ARGS]...' in response.output
    assert '--help  Show this message and exit.' in response.output
    assert 'run          Run MLCube ML task.' in response.output
    assert 'show_config  Show MLCube configuration.' in response.output
    print("All assertions passed")

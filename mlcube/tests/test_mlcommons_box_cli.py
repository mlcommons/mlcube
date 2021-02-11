from click.testing import CliRunner
from mlcube.main import cli

runner = CliRunner()

def test_mlcube():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    print(response.output)
    assert 'Usage: mlcube [OPTIONS] COMMAND [ARGS]...' in response.output
    assert 'MLCube 📦 is a packaging tool for ML models' in response.output
    assert 'verify  Verify MLCube metadata' in response.output

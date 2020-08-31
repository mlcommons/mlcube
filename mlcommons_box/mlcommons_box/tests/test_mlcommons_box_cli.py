from click.testing import CliRunner
from mlcommons_box.main import cli

runner = CliRunner()

def test_mlcommons_box():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcommons_box [OPTIONS] COMMAND [ARGS]...' in response.output
    assert 'Box 📦 is a packaging tool for ML models' in response.output
    assert '  verify  Verify Box metadata' in response.output

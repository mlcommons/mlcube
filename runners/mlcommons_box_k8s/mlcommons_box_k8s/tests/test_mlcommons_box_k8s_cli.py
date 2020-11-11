from click.testing import CliRunner
from mlcommons_box_k8s.main import cli

runner = CliRunner()


def test_mlcommons_box_k8s():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcommons_box_k8s [OPTIONS] COMMAND [ARGS]...' in response.output
    assert "  run  Runs a MLBox in a Kubernetes cluster." in response.output

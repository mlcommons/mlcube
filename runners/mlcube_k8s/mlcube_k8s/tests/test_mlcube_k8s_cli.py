from click.testing import CliRunner
from mlcube_k8s.main import cli

runner = CliRunner()


def test_mlcube_k8s():
    response = runner.invoke(cli)
    assert response.exit_code == 0
    assert 'Usage: mlcube_k8s [OPTIONS] COMMAND [ARGS]...' in response.output
    assert "  run  Runs a MLCube in a Kubernetes cluster." in response.output

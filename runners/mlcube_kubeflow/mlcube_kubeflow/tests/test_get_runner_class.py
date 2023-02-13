from unittest import TestCase
from mlcube_kubeflow import get_runner_class
from mlcube_kubeflow.kubeflow_run import KubeflowRun


class TestGetRunnerClass(TestCase):
    """This is a placeholder test to pass CI workflows."""

    def test_get_runner_class(self) -> None:
        self.assertIs(get_runner_class(), KubeflowRun)

from unittest import TestCase
from mlcube_k8s import get_runner_class
from mlcube_k8s.k8s_run import KubernetesRun


class TestGetRunnerClass(TestCase):
    """This is a placeholder test to pass CI workflows."""

    def test_get_runner_class(self) -> None:
        self.assertIs(get_runner_class(), KubernetesRun)

from unittest import TestCase
from mlcube_gcp import get_runner_class
from mlcube_gcp.gcp_run import GCPRun


class TestGetRunnerClass(TestCase):
    """This is a placeholder test to pass CI workflows."""

    def test_get_runner_class(self) -> None:
        self.assertIs(get_runner_class(), GCPRun)

import typing as t
import unittest
from unittest import TestCase

try:
    # SPython does not work in Windows OS
    import mlcube_singularity
    from mlcube_singularity.singularity_run import SingularityRun
except ImportError:
    mlcube_singularity = None
    SingularityRun = None


class TestFactoryFunction(TestCase):

    @unittest.skipUnless(SingularityRun is not None, reason="SPython is not available.")
    def test_factory_fn(self) -> None:
        self.assertTrue(hasattr(mlcube_singularity, 'get_runner_class'))
        self.assertTrue(callable(mlcube_singularity.get_runner_class))

        runner_cls: t.Type[SingularityRun] = mlcube_singularity.get_runner_class()
        self.assertIs(runner_cls, SingularityRun)

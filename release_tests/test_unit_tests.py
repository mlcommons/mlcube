import unittest
from pathlib import Path
from release_tests import (ReleaseTest, SysPath)


class UnitTestsTest(ReleaseTest):
    """  """

    @staticmethod
    def run_unit_tests(proj_dir: Path, proj_name: str) -> unittest.TestResult:
        return unittest.TextTestRunner().run(
            unittest.defaultTestLoader.discover(
                start_dir=str(proj_dir.joinpath(proj_name).resolve()),
                top_level_dir=str(proj_dir.resolve()),
                pattern='test_*.py'
            )
        )

    def test_mlcommons_box(self):
        with SysPath(self.mlcommons_box_dir):
            results: unittest.TestResult = UnitTestsTest.run_unit_tests(
                self.mlcommons_box_dir,
                'mlcommons_box'
            )
        if not results.wasSuccessful():
            print(results.errors, results.failures)
        self.assertTrue(results.wasSuccessful())

    def test_runners(self):
        failed_tests = []
        with SysPath(self.mlcommons_box_dir):
            for runner_dir in self.runner_dirs:
                with SysPath(runner_dir):
                    test_result = UnitTestsTest.run_unit_tests(runner_dir, str(runner_dir.name))
                    if not test_result.wasSuccessful():
                        failed_tests.append(test_result)

        if len(failed_tests) > 0:
            for failed_test in failed_tests:
                print(failed_test.errors, failed_test.failures)
        self.assertTrue(len(failed_tests) == 0)

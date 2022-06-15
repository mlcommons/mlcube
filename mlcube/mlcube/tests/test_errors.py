import typing as t
from unittest import TestCase
from mlcube.errors import ExecutionError


class TestErrors(TestCase):

    def check_execution_error_state(self, err: ExecutionError, message: str, description: str, context: t.Dict) -> None:
        self.assertEqual(err.message, message)
        self.assertEqual(err.description, description)
        self.assertDictEqual(err.context, context)

        self.assertEqual(
            err.describe(frmt='text'),
            f"ERROR:\n\tmessage: {message}\n\tdescription: {description}\n\tcontext: {context}"
        )

    def test_execution_error_init_method(self) -> None:
        self.check_execution_error_state(
            ExecutionError("Brief error description.", "Long error description.", param_a='value_a', param_b=1.2),
            "Brief error description.", "Long error description.", {'param_a': 'value_a', 'param_b': 1.2}
        )

    def test_execution_error_mlcube_configure_error_method(self) -> None:
        self.check_execution_error_state(
            ExecutionError.mlcube_configure_error(
                "MLCube Reference Runner", "Long error description.", param_a='value_a', param_b=1.2
            ),
            "MLCube Reference Runner runner failed to configure MLCube.", "Long error description.",
            {'param_a': 'value_a', 'param_b': 1.2}
        )

    def test_execution_error_mlcube_run_error_method(self) -> None:
        self.check_execution_error_state(
            ExecutionError.mlcube_run_error(
                "MLCube Reference Runner", "Long error description.", param_a='value_a', param_b=1.2
            ),
            "MLCube Reference Runner runner failed to run MLCube.", "Long error description.",
            {'param_a': 'value_a', 'param_b': 1.2}
        )

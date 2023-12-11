import typing as t
from unittest import TestCase

from click import BaseCommand, Option
from click.testing import CliRunner, Result

from mlcube.__main__ import cli, config, configure, create, describe, run, show_config
from mlcube.cli import Options, markdown2text


class TestCli(TestCase):
    def test_options(self) -> None:
        class Obj:
            ...

        decorators: t.List[str] = []
        for name in (v for v, m in vars(Options).items() if not v.startswith(("_", "__")) and callable(m)):
            decorator: t.Optional[t.Callable] = getattr(Options, name, None)
            self.assertIsNotNone(decorator, f"MLCube BUG: option decorator must not be None (name = {name}).")
            obj = decorator(Obj())
            params: t.List = getattr(obj, "__click_params__", None)
            self.assertIsInstance(params, list, f"Click library changed its implementation? Type={type(params)}.")
            self.assertEqual(1, len(params), f"Click library changed its implementation? Size={len(params)}.")
            cmd: Option = params[0]
            self.assertTrue(isinstance(cmd.help, str) and len(cmd.help) > 0, f"Invalid option help ({cmd.help})")
            plain_text = markdown2text(cmd.help)
            self.assertTrue(
                isinstance(plain_text, str) and len(plain_text) > 0,
                f"Invalid markdown2text conversion from markdown ('{cmd.help}') to plain text ('{plain_text}').",
            )
            decorators.append(name)

        expected_options_count: int = 14
        self.assertEqual(
            expected_options_count,
            len(decorators),
            f"Expected number of option decorators is {expected_options_count}. "
            f"Actual tested decorators: {decorators}.",
        )

    def test_help(self) -> None:
        """python -m unittest  mlcube.tests.test_cli"""
        cli_funcs = [cli, show_config, configure, run, describe, config, create]
        for cli_func in cli_funcs:
            self.assertIsInstance(cli_func, BaseCommand)
            result: Result = CliRunner().invoke(cli_func, [f"--help"])
            self.assertEqual(result.exit_code, 0, f"Error while running `{cli_func.name}`. Output: {result.output}")

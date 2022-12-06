import typing as t
from unittest import TestCase

from click import Option

from mlcube.cli import (markdown2text, Options)


class TestCli(TestCase):
    def test_options(self) -> None:
        class Obj:
            ...

        decorators: t.List[str] = []
        for name in (v for v, m in vars(Options).items() if not v.startswith(('_', '__')) and callable(m)):
            decorator: t.Optional[t.Callable] = getattr(Options, name, None)
            self.assertIsNotNone(decorator, f"MLCube BUG: option decorator must not be None (name = {name}).")
            obj = decorator(Obj())
            params: t.List = getattr(obj, '__click_params__', None)
            self.assertIsInstance(params, list, f"Click library changed its implementation? Type={type(params)}.")
            self.assertEqual(1, len(params), f"Click library changed its implementation? Size={len(params)}.")
            cmd: Option = params[0]
            self.assertTrue(
                isinstance(cmd.help, str) and len(cmd.help) > 0,
                f"Invalid option help ({cmd.help})"
            )
            plain_text = markdown2text(cmd.help)
            self.assertTrue(
                isinstance(plain_text, str) and len(plain_text) > 0,
                f"Invalid markdown2text conversion from markdown ('{cmd.help}') to plain text ('{plain_text}')."
            )
            decorators.append(name)

        self.assertEqual(
            8, len(decorators), f"Expected number of option decorators is 8. Actual tested decorators: {decorators}."
        )

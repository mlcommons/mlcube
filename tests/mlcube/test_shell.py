from unittest import TestCase

from mlcube.errors import ExecutionError
from mlcube.shell import Shell


class TestShell(TestCase):
    def test_run_01(self) -> None:
        for cmd in ('python --version', ['python', '--version']):
            for die_on_error in (True, False):
                exit_code = Shell.run(cmd, on_error='die')
                self.assertEqual(exit_code, 0, f"cmd = {cmd}, die_on_error = {die_on_error}")

    def test_run_02(self) -> None:
        cmds = [
            'python -c "print(message)"',
            'python -c "import os, signal; os.kill(os.getpid(), signal.SIGUSR1);"',
            '8389dfb48c6f4a1aaa16bdda76c1fb11'
        ]
        for cmd in cmds:
            exit_code = Shell.run(cmd, on_error='ignore')
            self.assertGreater(exit_code, 0, f"cmd = {cmd}")

    def test_run_03(self) -> None:
        with self.assertRaises(ExecutionError):
            _ = Shell.run('python -c "print(message)"', on_error='raise')

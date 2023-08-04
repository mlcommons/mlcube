import typing as t
from unittest import TestCase

from mlcube.errors import ExecutionError
from mlcube.shell import Shell

from omegaconf import DictConfig


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

    def test_run_and_capture_output(self) -> None:
        exit_code, version_str = Shell.run_and_capture_output(["python", "--version"])
        self.assertEqual(exit_code, 0, "Expecting exit code to be zero for `python --version`")
        self.assertTrue(version_str.startswith("Python"), "Expecting version string to start with `Python`.")

        exit_code, version_str = Shell.run_and_capture_output(["python", "-c" "print(message)"])
        self.assertNotEqual(exit_code, 0, "Expecting exit code to be non zero for `python -c 'print(message)'.`")
        self.assertIn("NameError: name 'message' is not defined", version_str, "No expected error.")

    def test_generate_mount_points(self) -> None:
        def _call_with_type_check(_task: str) -> t.Tuple[t.Dict, t.List, t.Dict]:
            _mounts, _args, _mounts_opts = Shell.generate_mounts_and_args(_mlcube_config, _task, make_dirs=False)

            self.assertIsInstance(_mounts, dict, "Invalid mounts dictionary")
            self.assertIsInstance(_args, list, "Invalid args list")
            self.assertIsInstance(_mounts_opts, dict, "Invalid mounts opts dictionary")

            return _mounts, _args, _mounts_opts

        # Test Case 1
        mounts, args, mounts_opts = _call_with_type_check('process')
        self.assertDictEqual(
            mounts,
            {
                '/mlcube/workspace/input': '/mlcube_io0',
                '/mlcube/workspace/output': '/mlcube_io1'
            }
        )
        self.assertListEqual(args, ['process', '--input_dir=/mlcube_io0', '--output_dir=/mlcube_io1'])
        self.assertDictEqual(
            mounts_opts,
            {'/mlcube/workspace/output': 'rw'}
        )

        # Test Case 2
        mounts, args, mounts_opts = _call_with_type_check('split')
        self.assertDictEqual(
            mounts,
            {
                '/mlcube/workspace/input': '/mlcube_io0',
                '/mlcube/workspace': '/mlcube_io1',
                '/datasets/my_split': '/mlcube_io2'
            }
        )
        self.assertListEqual(
            args,
            ['split', '--input_dir=/mlcube_io0', '--config=/mlcube_io1/config.yaml', '--output_dir=/mlcube_io2']
        )
        self.assertDictEqual(
            mounts_opts,
            {'/mlcube/workspace': 'ro', '/datasets/my_split': 'rw'}
        )


_mlcube_config = DictConfig({
    'runtime': {'workspace': '/mlcube/workspace'},
    'tasks': {
        'process': {
            'parameters': {
                'inputs': {'input_dir': {'type': 'directory', 'default': 'input'}},
                'outputs': {'output_dir': {'type': 'directory', 'default': 'output', 'opts': 'rw'}}
            }
        },
        'split': {
            'parameters': {
                'inputs': {
                    'input_dir': {'type': 'directory', 'default': 'input'},
                    'config': {'type': 'file', 'default': 'config.yaml', 'opts': 'ro'}
                },
                'outputs': {
                    'output_dir': {'type': 'directory', 'default': '/datasets/my_split', 'opts': 'rw'}
                }
            }
        }
    }
})

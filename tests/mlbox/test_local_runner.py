from unittest import TestCase
from mlbox.runners.local import LocalRunner


class TestLocalRunner(TestCase):

  def run_bare_metal(self):
    """ Test a bare metal script. """
    runner = LocalRunner(platform_config={})
    ret_code = runner.execute(['df', '-h'])
    self.assertEqual(0, ret_code)

  def test_run_in_container(self):
    """ Test a script inside a container. """
    runner = LocalRunner(platform_config={})
    ret_code = runner.execute([
      'nvidia-docker', 'run', '--rm', '-i', 'nvcr.io/nvidia/tensorflow:18.07-py3', '/bin/bash', '-c',
      'cd /workspace/nvidia-examples/cnn && mpiexec --allow-run-as-root --bind-to socket -np 1 ' +
      'python resnet.py --precision=fp32 --log_dir=/tmp/nvtfcnn ' +
      '--batch_size=2 --num_iter=10 --iter_unit=batch --layers=50'
    ])
    self.assertEqual(0, ret_code)

from unittest import TestCase
from typing import List
from mlbox.runners.local import LocalRunner


class TestLocalRunner(TestCase):

  def run_tests(self, test_case: [List[str], str]):
    runner = LocalRunner(platform_config={})
    ret_code = runner.execute(test_case)
    self.assertEqual(0, ret_code)

  def test_bare_metal(self):
    """ Test a bare metal script. """
    test_case = ['df', '-h']
    self.run_tests(test_case)
    self.run_tests(' '.join(test_case))

  def test_docker(self):
    """ Test a script inside a container.
    Pre-requisites: nvidia-docker, 'nvcr.io/nvidia/tensorflow:18.07-py3' NGC container, not too old GPU.
    This unit tests a ResNet50 for couple iterations using a synthetic data.
    """
    test_case = [
      'nvidia-docker', 'run', '--rm', '-i', 'nvcr.io/nvidia/tensorflow:18.07-py3', '/bin/bash', '-c',
      'cd /workspace/nvidia-examples/cnn && mpiexec --allow-run-as-root --bind-to socket -np 1 ' +
      'python resnet.py --precision=fp32 --log_dir=/tmp/nvtfcnn ' +
      '--batch_size=2 --num_iter=10 --iter_unit=batch --layers=50'
    ]
    self.run_tests(test_case)
    # TODO: This is not going to work, the command to be executed in a docker container, must be represented as string.
    # self.run_tests(' '.join(test_case))

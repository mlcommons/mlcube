from unittest import TestCase
from mlbox.runners.local import LocalRunner


class TestLocalRunner(TestCase):

  def test_run_bare_metal(self):
    runner = LocalRunner(platform_config={})
    ret_code = runner.execute(['df', '-h'])
    self.assertEqual(0, ret_code)

  def test_run_in_container_v01(self):
    """
    nvidia-docker run --rm -ti nvcr.io/nvidia/tensorflow:18.07-py3
    cd /workspace/nvidia-examples/cnn
    mpiexec --allow-run-as-root --bind-to socket -np 1 python resnet.py --precision=fp32 --log_dir=/tmp/nvtfcnn --batch_size=2 --num_iter=10 --iter_unit=batch --model=resnet50 --layers=50
    """
    # '/bin/bash -c \"cd /workspace/nvidia-examples/cnn && mpiexec --allow-run-as-root --bind-to socket -np 1 python resnet.py --precision=fp32 --log_dir=/tmp/nvtfcnn --batch_size=2 --num_iter=10 --iter_unit=batch --layers=50\"'
    # 'mpiexec --allow-run-as-root --bind-to socket -np 1 python /workspace/nvidia-examples/cnn/resnet.py --precision=fp32 --log_dir=/tmp/nvtfcnn --batch_size=2 --num_iter=10 --iter_unit=batch --layers=50'
    # '/bin/bash -c "echo Host name inside container $(hostname)"'
    runner = LocalRunner(platform_config={})
    runner.execute([
      'nvidia-docker', 'run', '--rm', '-i', 'nvcr.io/nvidia/tensorflow:18.07-py3', 'hostname'
    ])
    # self.assertEqual(0, ret_code)

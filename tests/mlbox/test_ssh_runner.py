import os
from unittest import TestCase
from mlbox.runners.ssh import SSHRunner


class TestSSHRunner(TestCase):
  """
  Run me like this:
    ```bash
    # Go to MLBOX root directory
    cd mlbox

    # export variables for this test
    export MLBOX_SHH_RUNNER_HOST=...
    export MLBOX_SSH_RUNNER_SHH_ARG=-o,StrictHostKeyChecking=no

    # Set python path
    export PYTHONROOT=$(pwd):${PYTHONROOT}

    # Run this test case
    python -m unittest mlbox.tests.TestSSHRunner.test_remote_host_name
    ```
  """

  def test_remote_host_name(self):
    """ Test a bare metal script. """
    ssh_runner = SSHRunner(platform_config={
      "ssh_args": os.environ.get('MLBOX_SSH_RUNNER_SHH_ARG', '').split(','),
      "host": os.environ.get('MLBOX_SHH_RUNNER_HOST', None)
    })
    ssh_runner.execute(["hostname"])

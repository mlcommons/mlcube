import os
from unittest import TestCase
from mlbox.runners.ssh import SSHRunner


class TestSSHRunner(TestCase):
  """
  Run me like this:
    ```bash
    # Setup passwordless login
    ...

    # Go to MLBOX root directory.
    cd mlbox

    # Export variables for this test.
    export MLBOX_SHH_RUNNER_HOST=...
    export MLBOX_SSH_RUNNER_SHH_ARG=-o,StrictHostKeyChecking=no

    # Set python path
    export PYTHONPATH=$(pwd):${PYTHONPATH}

    # Run this test case
    python -m unittest tests.mlbox.test_ssh_runner.TestSSHRunner.test_remote_host_name
    ```
  """

  def test_remote_host_name(self):
    """ Test a bare metal script on a remote machine. """
    ssh_runner = SSHRunner(platform_config={
      "ssh_args": os.environ.get('MLBOX_SSH_RUNNER_SHH_ARG', '').split(','),
      "host": os.environ.get('MLBOX_SHH_RUNNER_HOST', None)
    })
    ssh_runner.execute(["hostname"])

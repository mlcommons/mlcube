from unittest import TestCase
from mlbox.runners.local import LocalRunner


class TestLocalRunner(TestCase):
  def test_run_local_cmd(self):
    runner = LocalRunner(platform_config={})
    ret_code = runner.execute(['df', '-h'])
    self.assertEqual(0, ret_code)

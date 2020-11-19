import os
from unittest import TestCase
from mlcube_ssh.ssh_metadata import (Platform, SystemInterpreter, VirtualEnvInterpreter)


class TestPlatformMetadata(TestCase):
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'test_data', 'platforms')

    def test_platform_01(self):
        platform: Platform = Platform(os.path.join(TestPlatformMetadata.CONFIG_PATH, 'platform_01.yaml'))

        self.assertEqual('gcp-f1-micro', platform.host)
        self.assertDictEqual({}, platform.authentication)
        self.assertEqual('docker.yaml', platform.platform)

        interpreter = platform.interpreter
        self.assertIsInstance(interpreter, SystemInterpreter)
        self.assertEqual('system', interpreter.type)
        self.assertEqual('python3.6', interpreter.python)
        self.assertEqual('mlcube-docker==0.2.2', interpreter.requirements)

        self.assertEqual('gcp-f1-micro', platform.get_connection_string())

    def test_platform_02(self):
        platform: Platform = Platform(os.path.join(TestPlatformMetadata.CONFIG_PATH, 'platform_02.yaml'))

        self.assertEqual('gcp-f1-micro', platform.host)
        self.assertDictEqual(
            {'user': 'gcp_user', 'identify_file': '/opt/mlcube/ssh/gcp_identity'},
            platform.authentication
        )
        self.assertEqual('singularity.yaml', platform.platform)

        interpreter = platform.interpreter
        self.assertIsInstance(interpreter, VirtualEnvInterpreter)
        self.assertEqual('virtualenv', interpreter.type)
        self.assertEqual('python3.6', interpreter.python)
        self.assertEqual('mlcube-docker==0.2.1', interpreter.requirements)
        self.assertEqual('${HOME}/mlcube/environments', interpreter.location)
        self.assertEqual('mlcube-docker-0.2.1', interpreter.name)

        self.assertEqual('-i /opt/mlcube/ssh/gcp_identity gcp_user@gcp-f1-micro', platform.get_connection_string())

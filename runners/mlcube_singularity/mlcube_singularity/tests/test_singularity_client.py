from unittest import TestCase

import semver
from mlcube_singularity.singularity_client import Client, Runtime, Version


class TestSingularityRunner(TestCase):
    def test___init__(self) -> None:
        client = Client(
            "sudo singularity", Version(Runtime.APPTAINER, semver.VersionInfo(3, 7, 5))
        )
        self.assertListEqual(["sudo", "singularity"], client.singularity)
        self.assertEqual(Runtime.APPTAINER, client.version.runtime)
        self.assertEqual(3, client.version.version.major)
        self.assertEqual(7, client.version.version.minor)
        self.assertEqual(5, client.version.version.patch)

    def test_supports_fakeroot(self) -> None:
        client = Client(
            "sudo singularity", Version(Runtime.APPTAINER, semver.VersionInfo(3, 7, 5))
        )
        self.assertTrue(client.supports_fakeroot())

        client = Client(
            "sudo singularity",
            Version(Runtime.SINGULARITY, semver.VersionInfo(3, 7, 5)),
        )
        self.assertTrue(client.supports_fakeroot())

        client = Client(
            "sudo singularity",
            Version(Runtime.SINGULARITY, semver.VersionInfo(3, 5, 0)),
        )
        self.assertTrue(client.supports_fakeroot())

        client = Client(
            "sudo singularity",
            Version(Runtime.SINGULARITY, semver.VersionInfo(3, 4, 9)),
        )
        self.assertFalse(client.supports_fakeroot())

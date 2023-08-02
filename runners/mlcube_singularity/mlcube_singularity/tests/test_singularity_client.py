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

    def inspect_version(self, version: Version, expected: Version) -> None:
        self.assertIsInstance(version, Version)

        self.assertIsInstance(version.runtime, Runtime)
        self.assertEqual(version.runtime, expected.runtime)

        self.assertIsInstance(version.version, semver.VersionInfo)
        self.assertEqual(version.version, expected.version)

    def test_version__init__(self) -> None:
        version = Version(Runtime.APPTAINER, semver.VersionInfo(3, 7, 5))

        self.assertIsInstance(version.runtime, Runtime)
        self.assertEqual(version.runtime, Runtime.APPTAINER)

        self.assertIsInstance(version.version, semver.VersionInfo)
        self.assertEqual(version.version, semver.VersionInfo(3, 7, 5))

    def test_version_from_version_string(self) -> None:
        self.inspect_version(
            Version.from_version_string("singularity version 3.7.4"),
            Version(Runtime.SINGULARITY, semver.VersionInfo(3, 7, 4)),
        )
        self.inspect_version(
            Version.from_version_string("singularity-ce version 3.5.4"),
            Version(Runtime.SINGULARITY, semver.VersionInfo(3, 5, 4)),
        )
        self.inspect_version(
            Version.from_version_string("singularity-ce version 3.11.0-rc.2"),
            Version(
                Runtime.SINGULARITY,
                semver.VersionInfo(3, 11, 0, prerelease="rc.2", build=None),
            ),
        )
        self.inspect_version(
            Version.from_version_string("apptainer version 1.1.9-1.el9"),
            Version(
                Runtime.APPTAINER,
                semver.VersionInfo(1, 1, 9, prerelease="1.el9", build=None),
            ),
        )
        self.inspect_version(
            Version.from_version_string("0.1.3-pull/123-0a5d"),
            Version(
                Runtime.SINGULARITY,
                semver.VersionInfo(0, 1, 3, prerelease="pull", build="123-0a5d"),
            ),
        )
        self.inspect_version(
            Version.from_version_string("1.0.32"),
            Version(
                Runtime.UNKNOWN,
                semver.VersionInfo(1, 0, 32),
            ),
        )

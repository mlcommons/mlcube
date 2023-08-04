import typing as t
from unittest import TestCase

import semver
from mlcube_singularity.singularity_client import Client, DockerImage, Runtime, Version


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

    def check_docker_image(self, image: DockerImage, expected: DockerImage) -> None:
        self.assertIsInstance(image, DockerImage)

        def _check_nullable_value(_actual: t.Optional, _expected: t.Optional) -> None:
            if expected is None:
                self.assertIsNone(_actual)
            else:
                self.assertIsInstance(_actual, type(_expected))
                self.assertEqual(_actual, _expected)

        _check_nullable_value(image.host, expected.host)
        _check_nullable_value(image.port, expected.port)

        self.assertIsInstance(image.path, list)
        self.assertTrue(len(image.path) > 0)
        self.assertListEqual(image.path, expected.path)

        _check_nullable_value(image.tag, expected.tag)
        _check_nullable_value(image.digest, expected.digest)

    def test_docker_image_from_string(self) -> None:
        self.check_docker_image(
            DockerImage.from_string(
                "LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE"
            ),
            DockerImage(
                host="LOCATION-docker.pkg.dev",
                path=["PROJECT-ID", "REPOSITORY", "IMAGE"],
            ),
        )
        self.check_docker_image(
            DockerImage.from_string(
                "LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE:TAG"
            ),
            DockerImage(
                host="LOCATION-docker.pkg.dev",
                path=["PROJECT-ID", "REPOSITORY", "IMAGE"],
                tag="TAG",
            ),
        )
        self.check_docker_image(
            DockerImage.from_string(
                "LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE@IMG-DIGEST"
            ),
            DockerImage(
                host="LOCATION-docker.pkg.dev",
                path=["PROJECT-ID", "REPOSITORY", "IMAGE"],
                digest="IMG-DIGEST",
            ),
        )
        self.check_docker_image(
            DockerImage.from_string("USERNAME/REPOSITORY:TAG"),
            DockerImage(path=["USERNAME", "REPOSITORY"], tag="TAG"),
        )
        self.check_docker_image(
            DockerImage.from_string("mlcommons/hello_world:0.0.1"),
            DockerImage(path=["mlcommons", "hello_world"], tag="0.0.1"),
        )
        self.check_docker_image(
            DockerImage.from_string(
                "mlcommons/hello_world@sha256:9b77d4cb97f8dcf14ac137bf65185fc8980578"
            ),
            DockerImage(
                path=["mlcommons", "hello_world"],
                digest="sha256:9b77d4cb97f8dcf14ac137bf65185fc8980578",
            ),
        )

    def test_docker_image_to_string(self) -> None:
        names = [
            "LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE",
            "LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE:TAG",
            "LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE@IMG-DIGEST",
            "USERNAME/REPOSITORY:TAG",
            "mlcommons/hello_world:0.0.1",
            "mlcommons/hello_world@sha256:9b77d4cb97f8dcf14ac137bf65185fc8980578",
        ]
        for name in names:
            self.assertEqual(str(DockerImage.from_string(name)), name)

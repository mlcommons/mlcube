import subprocess
import typing as t
from pathlib import Path
from release_tests import (ReleaseTest, CurrentDir)


class VersionsTest(ReleaseTest):
    """ Test all projects use the same release version. """

    def get_version(self, directory: Path) -> t.Optional[t.Text]:
        """ Return project version specified in setup.py file. """
        self.assertTrue(
            directory.joinpath('setup.py').exists(),
            f"The 'setup.py' file does not exist in {directory}"
        )
        with CurrentDir(directory.resolve()):
            result = subprocess.run(['python', 'setup.py', '--version'], stdout=subprocess.PIPE)
        version = result.stdout.decode("utf-8").strip()
        self.assertTrue(
            version is not None and version != '',
            f"Invalid version in setup.py (directory={directory}, version={version})."
        )
        return version

    def test_package_versions(self) -> None:
        """ Test that all package versions are the same. """
        mlcube_ver = self.get_version(self.mlcube_dir)
        for runner_dir in self.runner_dirs:
            runner_ver = self.get_version(runner_dir)
            self.assertEqual(
                mlcube_ver,
                runner_ver,
                f"Runner's version ({runner_dir.name}) {runner_ver} != {mlcube_ver} (MLCube version)"
            )
        print(f"Release version: {mlcube_ver}")

    def test_dependency_versions(self) -> None:
        """ Test that all runners required current MLCube version. """
        expected_ver = self.get_version(self.mlcube_dir)
        for path in self.runner_dirs:
            with open(path.joinpath('requirements.txt'), 'r') as requirements:
                packages = [line.strip() for line in requirements]
            for package in packages:
                if not package.startswith('mlcube'):
                    continue
                parts = package.split('==')
                self.assertEqual(2, len(parts), f"Invalid dependency '{package}'. Missing version?")
                self.assertEqual(expected_ver, parts[1], f"Dependency version ({package}) does not match current "
                                                         f"version {expected_ver}.")
                break

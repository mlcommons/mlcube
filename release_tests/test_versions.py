import subprocess
from pathlib import Path
from typing import Optional
from release_tests import (ReleaseTest, CurrentDir)


class VersionsTest(ReleaseTest):
    @staticmethod
    def get_version(directory: Path) -> Optional[str]:
        if not directory.joinpath('setup.py').exists():
            return None
        with CurrentDir(directory.resolve()):
            result = subprocess.run(['python', 'setup.py', '--version'], stdout=subprocess.PIPE)
        return result.stdout.decode("utf-8").strip()

    def test_package_versions(self) -> None:
        #
        mlcommons_box_ver = VersionsTest.get_version(self.mlcommons_box_dir)
        for runner_dir in self.runner_dirs:
            runner_ver = VersionsTest.get_version(runner_dir)
            self.assertEqual(
                mlcommons_box_ver,
                runner_ver,
                f"Runner's version ({runner_dir.name}) {runner_ver} != {mlcommons_box_ver} (MLCommons-Box version)"
            )
        print(f"Release version: {mlcommons_box_ver}")

    def test_dependency_versions(self) -> None:
        expected_ver = VersionsTest.get_version(self.mlcommons_box_dir)
        for path in self.runner_dirs:
            with open(path.joinpath('requirements.txt'), 'r') as requirements:
                packages = [line.strip() for line in requirements]
            for package in packages:
                if not package.startswith('mlcommons-box'):
                    continue
                parts = package.split('==')
                self.assertEqual(2, len(parts), f"Invalid dependency '{package}'. Missing version?")
                self.assertEqual(expected_ver, parts[1], f"Dependency version ({package}) does not match current "
                                                         f"version {expected_ver}.")
                break

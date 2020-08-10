"""This file sets up the mlperf module."""

import os
import sys
from setuptools import setup, find_packages, Command
from pathlib import Path

def install_requires():
    with open("requirements.txt", "r") as requirements_file:
        return [req for req in requirements_file.readlines() if req]

class clean(Command):
    """Custom clean command."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -vrf ./build ./dist ./*.egg-info')

def schemas():
    paths = []
    for (path, _, filenames) in os.walk("mlbox/schemas"):
        for filename in filenames:
            paths.append(os.path.join("..", path, filename))
    return paths

extra_files = schemas()

setup(
    name="mlbox",
    # entry_points={"console_scripts": ["mlbox = mlbox.mlbox:main"]},
    version="0.0.1",
    description="MLBox manager",
    long_description=Path("README.md").read_text(),
    license="Apache 2.0",
    packages=["mlbox"],
    long_description_content_type="text/x-rst",
    install_requires=install_requires(),
    python_requires='>=3.6',
    include_package_data=True,
    package_data={"": extra_files},
    cmdclass={
        'clean': clean,
    }
)

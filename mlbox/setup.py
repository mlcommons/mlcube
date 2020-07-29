from setuptools import setup

setup(
  name = "MLBox",
  version = "0.0.1",
  description = "MLBox manager",
  author = "MLCommons",
  packages = ["mlbox"],
  entry_points = {
    "console_scripts": ["mlbox = mlbox.mlbox:main"]
  },
  install_requires = [
    "docker",
    "pyyaml"
  ]
)

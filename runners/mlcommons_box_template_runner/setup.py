from setuptools import setup, find_packages

setup(
    name = "mlcommons-box-template-runner",
    version = "0.1.0",
    description = "MLCommons Box Template Runner",
    packages = find_packages(include="mlcommons_box_template_runner"),
    package_data = {"mlcommons_box_template_runner":["mlcommons_box_runner.yaml"]},
    include_package_data = True,
    entry_points = {
        "console_scripts": ["mlcbr-template = mlcommons_box_template_runner.main:main"]
    }
)

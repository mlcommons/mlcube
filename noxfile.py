import os
import shutil
import typing as t
from pathlib import Path

import nox

"""
## Introduction
Run various MLCube and MLCube runner tests. Some tests run for multiple python versions, others just for one. Some do
not take too much time (e.g., unit test), others require some time (e.g., MLCube examples or minified benchmarks). This 
is based on `nox` (https://nox.thea.codes/). 

## Prerequisites
No need to use MLCube python environment - nox will be creating new environments for each test session installing all
required dependencies. Only nox package needs to be installed.
In addition, python versions specified in this file or on a command line needs to be discoverable by NOX. One option
is to ensure they are all in `PATH` environment variable. 

## Example NOX commands
```bash
nox --list             # List all available test sessions. 
nox -t unit            # Run all unit tests for all python versions.
nox -t unit -p 3.10    # Run all unit tests for python 3.10.
nox                    # Run all default test sessions (see below for more details).
``` 

## Default sessions
Only three test suits are executed by default - `mlcube_unit`, `runner_unit` and `test_versions`. All other test
sessions need to be explicitly specified on a command line.

## Environment variables
- `MLCUBE_PYTHON_VERSIONS`: Comma-separated list of python versions to run nox sessions with (e.g., "3.8,3.9,3.10"). 

## Details
- The script itself runs using whatever python was used to run it. It's the `session` variable that interacts with
  a correct session environment. 
- The `nox` cleans temporary directory of every session before running them. When running sessions involving docker 
  runner make sure to configure docker runner to use your user and group ID. To do so, update your `~/mlcube.yaml` using
  the following template (where USER_ID = `id -u` and GROUP_ID = `id -g`):
  ```
  ...
  platforms:
  ...
  docker:
    ...
    gpu_args: '-u USER_UD:GROUP_ID'
    cpu_args: '-u USER_UD:GROUP_ID'
    ...
  ...
  ```
"""

nox.options.sessions = ["mlcube_unit", "runner_unit", "test_versions"]
"""Default sessions to run."""

MLCUBE_PYTHON_VERSIONS = ["3.6", "3.7", "3.8", "3.9", "3.10", "3.11"]
"""The list of python versions to run nox sessions with. Can be overridden by setting the environment variable."""
if "MLCUBE_PYTHON_VERSIONS" in os.environ:
    MLCUBE_PYTHON_VERSIONS = os.environ["MLCUBE_PYTHON_VERSIONS"].split(",")


# Prevent Python from writing bytecode
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- Test Sessions ---------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

@nox.session(python=MLCUBE_PYTHON_VERSIONS, tags=("mlcube", "unit"))
def mlcube_unit(session: nox.Session) -> None:
    """Run MLCube core unit tests.

    Related nox commands:
        ```bash
        nox --list | grep mlcube_unit       # Show all sessions.
        nox -s mlcube_unit -p 3.6           # Run for one python version (same as `nox -t mlcube -p 3.6`).
        nox -s mlcube_unit                  # Run for all python versions (same as `nox -t mlcube`).
        ```
    """
    session.install(f"pytest")
    _install_mlcube(session, run_unit_test=True)


@nox.session(python=MLCUBE_PYTHON_VERSIONS, tags=("runner", "unit"))
@nox.parametrize("runner", ["docker", "gcp", "k8s", "kubeflow", "singularity", "ssh"])
def runner_unit(session: nox.Session, runner: str) -> None:
    """Run MLCube runner unit tests.

    Related nox commands:
        ```bash
        nox --list | grep runner_unit                # Show all sessions
        nox -s runner_unit                           # Run all runner_unit sessions (all pythons X all runners).
        nox -s "runner_unit-3.10(runner='docker')"   # Run one session for docker runner using python 3.10.
        ```
    """
    session.install(f"pytest")
    _install_mlcube(session)
    _install_runner(session, runner, run_unit_test=True)


@nox.session
def test_versions(session: nox.Session) -> None:
    """Check versions of all projects are the same and all runners depend on the latest MLCube.

    This test ensures that (1) all runner projects have the same version as MLCube version (projects' setup.py are
    examined for this), and (2) all runners depend on the same latest MLCube version (projects' requirements.txt files
    are examined for this).

    Related nox commands:
        ```bash
        nox --list | grep test_versions        # Show all sessions.
        nox -s test_versions                   # Run test_version sessions.
        ```
    """
    project_root_dir: Path = Path(__file__).parent
    mlcube_ver = _get_project_version(session, project_root_dir / "mlcube")

    runner_dirs = [d for d in (project_root_dir / "runners").iterdir() if d.is_dir()]
    for runner_dir in runner_dirs:
        # Check project version
        runner_ver = _get_project_version(session, runner_dir)
        if runner_ver != mlcube_ver:
            raise ValueError(f"Runner's version ({runner_dir.name}) {runner_ver} != {mlcube_ver} (MLCube version).")
        # Check dependency version
        mlcube_dep_ver = _get_mlcube_dep_version(runner_dir)
        if mlcube_dep_ver != mlcube_ver:
            raise ValueError(
                f"Dependency version {mlcube_dep_ver} does not match MLCube version {mlcube_ver} in {runner_dir}."
            )


@nox.session(tags=("mlcube-example", "mnist"))
@nox.parametrize("runner", ["docker", "singularity"])
def mlcube_example_mnist(session: nox.Session, runner: str) -> None:
    """ Run MNIST MLCube example.

    Sessions of this test cannot run in parallel (a prerequisite step - clone the `mlcube_examples` project).

    Detailed nox commands:
        ```bash
        nox --list | grep mlcube_example_mnist                  # Show all sessions.
        nox -s "mlcube_example_mnist(runner='docker')"          # Run test session with docker runner
        nox -s "mlcube_example_mnist(runner='singularity')"     # Run test session with singularity runner
        ```
    """
    # Copy MLCube and fail earlier to avoid wasting time installing python packages
    repository_dir: Path = _clone_mlcube_examples(session)
    mlcube_dir: Path = _copy_directory(session, repository_dir / "mnist")

    _install_mlcube(session)
    _install_runner(session, runner)

    try:
        config_args = "-Prunner.build_strategy=always" if runner == "docker" else ""
        with session.chdir(mlcube_dir):
            workspace_dir: Path = mlcube_dir / "workspace"
            _check_files_exist(workspace_dir, ["data.yaml", "train.yaml"])

            _run_mlcube(session, "describe")
            _run_mlcube(session, "configure", platform=runner, args=[config_args])
            #
            _run_mlcube(session, "run", platform=runner, task="download")
            _check_files_exist(workspace_dir, ["data/mnist.npz", "logs/mlcube_mnist_download.log"])
            #
            _run_mlcube(session, "run", platform=runner, task="train")
            _check_files_exist(
                workspace_dir / "model" / "mnist_model",
                ["saved_model.pb", "variables/variables.data-00000-of-00001", "variables/variables.index"]
            )
            _check_files_exist(workspace_dir / "logs", ["mlcube_mnist_train.log"])

    except Exception:
        raise
    finally:
        # Maybe do not do it and keep files for subsequent analysis? The nox will empty this anyway next time.
        # _rmtree_with_log(mlcube_dir)
        ...


@nox.session(tags=("mlcube-example", "matmul"))
def mlcube_example_matmul(session: nox.Session) -> None:
    """Test MatMul MLCube example.

    Detailed nox commands:
        ```bash
        nox --list | grep mlcube_example_matmul         # Show all sessions.
        nox -s mlcube_example_matmul                    # Run this test session
        ```
    """
    # Copy MLCube and fail earlier to avoid wasting time installing python packages
    repository_dir: Path = _clone_mlcube_examples(session)
    mlcube_dir: Path = _copy_directory(session, repository_dir / "matmul")

    _install_mlcube(session)
    _install_runner(session, "docker")

    try:
        with session.chdir(mlcube_dir):
            workspace_dir: Path = mlcube_dir / "workspace"
            _check_files_exist(workspace_dir, ["shapes.yaml"])

            _run_mlcube(session, "describe")
            _run_mlcube(session, "configure", platform="docker", args=["-Prunner.build_strategy=always"])
            #
            _run_mlcube(session, "run", platform="docker", task="matmul")
            _check_files_exist(workspace_dir, ["matmul.txt"])
    except Exception:
        raise
    finally:
        # Maybe do not do it and keep files for subsequent analysis? The nox will empty this anyway next time.
        # _rmtree_with_log(mlcube_dir)
        ...


@nox.session(tags=("mlcube-example", "hello-world"))
def mlcube_example_hello_world(session: nox.Session) -> None:
    """Test HelloWorld MLCube example.

    Detailed nox commands:
        ```bash
        nox --list | grep mlcube_example_hello_world         # Show all sessions.
        nox -s mlcube_example_hello_world                    # Run this test session
        ```
    """
    # Copy MLCube and fail earlier to avoid wasting time installing python packages
    repository_dir: Path = _clone_mlcube_examples(session)
    mlcube_dir: Path = _copy_directory(session, repository_dir / "hello_world")

    _install_mlcube(session)
    _install_runner(session, "docker")

    try:
        with session.chdir(mlcube_dir):
            workspace_dir: Path = mlcube_dir / "workspace"
            _check_files_exist(workspace_dir / "names", ["alice.txt"])

            _run_mlcube(session, "describe")
            _run_mlcube(session, "configure", platform="docker", args=["-Prunner.build_strategy=always"])
            #
            _run_mlcube(session, "run", platform="docker", task="hello")
            _check_files_exist(workspace_dir / "chats", ["chat_with_alice.txt"])
            #
            _run_mlcube(session, "run", platform="docker", task="bye")
            _check_files_exist(workspace_dir / "chats", ["chat_with_alice.txt"])
    except Exception:
        raise
    finally:
        # Maybe do not do it and keep files for subsequent analysis? The nox will empty this anyway next time.
        # _rmtree_with_log(mlcube_dir)
        ...

# ----------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------- Support Functions -------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


def _install_mlcube(session: nox.Session, run_unit_test: bool = False) -> None:
    """Install MLCube core library.

    Args:
        session: Current nox session.
        run_unit_test: If true, run unit tests after installation.
    """
    with session.chdir(Path(__file__).parent / "mlcube"):
        session.install(".")
        if run_unit_test:
            session.run("pytest", "-v")


def _install_runner(session: nox.Session, runner: str, run_unit_test: bool = False) -> None:
    """Install MLCube runner library.

    Args:
        session: Current nox session.
        runner: Runner name (docker, singularity, etc.)
        run_unit_test: If true, run unit tests after installation.
    """
    with session.chdir(Path(__file__).parent / "runners" / f"mlcube_{runner}"):
        session.install(".")
        if run_unit_test:
            session.run("pytest", "-v")


def _clone_mlcube_examples(session: nox.Session) -> Path:
    """Clone if not cloned previously the MLCube examples repository in the nox cache.

    Args:
        session: Current nox session.
    Returns:
        The path to the cloned repository (e.g., `./.nox/.cache/mlcube_examples/`)
    """
    cache_dir = session.cache_dir.resolve()
    mlcube_examples_dir = cache_dir / "mlcube_examples"

    if not mlcube_examples_dir.exists():
        with session.chdir(cache_dir):
            session.run("git", "clone", "https://github.com/mlcommons/mlcube_examples.git", external=True)

    return mlcube_examples_dir


def _run_mlcube(
        session: nox.Session, command: str, platform: t.Optional[str] = None, task: t.Optional[str] = None,
        args: t.Optional[t.List[str]] = None
) -> None:
    """Run MLCube command.

    Args:
        session: Current nox session.
        command: MLCube command (describe, configure, run).
        platform: Platform to run on (docker, singularity). Applies to configure and run commands.
        task: Task name to run. Applies to the task command.
        args: List of additional arguments to pass to the MLCube (for instance args=["-Prunner.build_strategy=always"]).
    """
    command_line: t.List[str] = ["mlcube", command]

    if platform:
        command_line.append(f"--platform={platform}")
    if task:
        command_line.append(f"--task={task}")
    if args:
        command_line.extend(args)

    session.run(*command_line)


def _copy_directory(session: nox.Session, source_dir: Path) -> Path:
    """Copy `source_dir` directory to session temporary directory.

    If target directory already exists, it will be removed first.

    Args:
        session: Current nox session.
        source_dir: Source directory to copy.
    Returns:
        Absolute path to a copied directory (that will always be in the session's tmp directory).
    """
    target_dir = Path(session.create_tmp()).resolve() / source_dir.name
    _rmtree_with_log(target_dir)
    shutil.copytree(source_dir, target_dir)
    return target_dir


def _rmtree_with_log(directory: Path) -> None:
    """Remove directory if exists, and print the directory path if there's an exception."""
    try:
        if directory.exists():
            shutil.rmtree(directory)
    except Exception:
        print("Can't remote directory tree:", directory.as_posix())
        raise


def _check_files_exist(*args) -> None:
    """Check all files exist and are not empty.

    Args:
        args: Must contain zero, one or two arguments.
                - Zero: do nothing.
                - One:  it's the list of files (t.List[t.Union[str, Path]]).
                - Two:  root directory (Path) and list of files (t.List[t.Union[str, Path]]).
            If root directory is none, files are considered as containing absolute paths. Else, all files in `files` are
            relative to this root directory.
    """
    if not args:
        return
    if len(args) == 1:
        root_directory, files = None, args[1]
    elif len(args) == 2:
        root_directory, files = args
        assert isinstance(root_directory, Path), f"Invalid root_directory type ({type(root_directory)})."
    else:
        assert False, f"Invalid number of arguments: ({len(args)})."

    missing_files: t.List[Path] = []
    zero_size_files: t.List[Path] = []

    for idx, file in enumerate(files):
        if isinstance(file, str):
            file = Path(file)
        assert isinstance(file, Path), f"Invalid file path type (pos=idx, type={type(file)})."

        file = (root_directory / file).resolve() if root_directory is not None else file.resolve()

        if not file.exists():
            missing_files.append(file)
        elif file.stat().st_size == 0:
            zero_size_files.append(file)

    if missing_files or zero_size_files:
        raise FileNotFoundError(f"Missing files ({missing_files}) or zero-size files ({zero_size_files}) found.")


def _get_project_version(session: nox.Session, project_dir: Path) -> str:
    """Return project version specified in setup.py file.

    Args:
        session: The current nox session.
        project_dir: Project root directory that must contain setup.py file.

    Returns:
         Project version specified in project's setup.py file.
    """
    if not (project_dir / "setup.py").is_file():
        raise FileNotFoundError(f"The setup.py file not found in {project_dir}.")

    with session.chdir(project_dir):
        version = session.run('python', 'setup.py', '--version', silent=True).strip()

    if not version:
        raise ValueError(f"Invalid version in setup.py (directory={project_dir}, version={version}).")

    return version


def _get_mlcube_dep_version(project_dir: Path) -> str:
    """Return MLCube library version the runner project depends on.

    Args:
        project_dir: Runner's project root directory that must contain `requirements.txt` file.

    Return:
        MLCube version from requirements.txt file.
    """
    if not (project_dir / "requirements.txt").is_file():
        raise FileNotFoundError(f"The requirements.txt file not found in {project_dir}.")

    with open(project_dir / 'requirements.txt', "rt") as requirements:
        for raw_req in (requirement.strip() for requirement in requirements):
            if not raw_req.startswith('mlcube'):
                continue
            parsed_req = raw_req.split('==')
            if len(parsed_req) != 2 or parsed_req[0] != "mlcube":
                raise ValueError(
                    f"Invalid MLCube requirement spec (raw_req={raw_req}, parsed_req={parsed_req}) in {project_dir}."
                )
            return parsed_req[1]

    raise ValueError(f"No MLCube requirement spec found in {project_dir}.")

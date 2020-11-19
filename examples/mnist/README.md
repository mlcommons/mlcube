# MNIST MLCube example
Directory structure:
```shell script
build/               # MLCube implementation. Contains source python code and Docker/Singularity recipes. 
platform/            # Platform definition files for the following runners:
   docker.yaml       #     Run MLCube locally using docker.
   singularity.yaml  #     Run MLCube locally using singularity.
   ssh.yaml          #     Run MLCube on a remote host using Docker or Singularity runtime.
run/                 # Task invocations specifications. Assigns values to task arguments.
tasks/               # Task definitions. For each task, a list of parameters and their types are listed.
workspace/           # Default place to store input/output artifacts.
mlcube.yaml           # Main MLCube definition file.
```

The `build` directory contains actual implementation of the MLCube workload. For instance, it can contain a python
project. The MNIST MLCube also stores Docker and Singularity recipes in this folder. MNIST cube supports both container
runtimes, and users can choose what they want to use. It can be runner-dependent, but reference Docker/Singularity 
runners assumes that `build` directory exists and contains either `Dockerfile` or `Singularity.recipe`. In both cases,
the `build` directory becomes a root content directory during the image build phase (configure phase in MLCube terms).

The `platform` directory is a new one. It contains platform files for supported runner. This makes it possible to run
MLCube using different platforms ("runtimes") such as Docker or Singularity. Platform files do not need to be stored
in this directory, and users can store them wherever they want. This is useful for runners that run MLCubes on remote
hosts (e.g., cloud or SSH runners). For instance, reference SSH runner can reuse platform configuration file for a
particular host across multiple MLCube implementations.

The `workspace` directory is default choice to store input/output artifacts such as datasets, models, log files etc.
One thing to keep in mind is, for instance, SSH runner syncs this directory between remote and local host. Artifacts
such as Singularity containers should not be stored here unless users want to sync them as well.

### End to end example using Singularity runner and GitHub source tree
- Setup and activate python virtual environment, install runner requirements
  ```shell script
  virtualenv -p python3.8 ./env
  source ./env/bin/activate
  pip install typer mlspeclib
  export PYTHONPATH=$(pwd)/mlcube:$(pwd)/runners/mlcube_singularity_run:$(pwd)/runners/mlcube_docker_run
  ```

- Specify path to the Singularity image. In MNIST MLCube (`platform/singularity.yaml`), the path is
  `/opt/singularity/mlperf_mlcube_mnist-0.01.simg`. Either change it, or make sure the `/opt/singularity` the directory
  exists and writable, or users have permission to create one.

- Setup environment. This is optional step. 
  ```shell script
  export https_proxy=${http_proxy}
  ```

- Configure MNIST MLCube.
  ```shell script
  python -m mlcube_singularity_run configure --mlcube=examples/mnist --platform=examples/mnist/platform/singularity.yaml
  ```

- Run two tasks - `download` (download data) and `train`
  ```shell script
  python -m mlcube_singularity_run run --mlcube=examples/mnist --platform=examples/mnist/platform/singularity.yaml --task=examples/mnist/run/download.yaml
  python -m mlcube_singularity_run run --mlcube=examples/mnist --platform=examples/mnist/platform/singularity.yaml --task=examples/mnist/run/train.yaml
  ```

### End to end example using Docker runner and GitHub source tree
- Setup and activate python virtual environment, install runner requirements
  ```shell script
  virtualenv -p python3.8 ./env
  source ./env/bin/activate
  pip install typer mlspeclib
  export PYTHONPATH=$(pwd)/mlcube:$(pwd)/runners/mlcube_singularity_run:$(pwd)/runners/mlcube_docker_run
  ```

- Setup environment. This step is optional. Docker runner uses `http_proxy` and `https_proxy` environmental variables
  (if set) and passes them to docker's build and run phases. 
  ```shell script
  export https_proxy=${http_proxy}
  ```

- Configure MNIST MLCube.
  ```shell script
  python -m mlcube_docker_run configure --mlcube=examples/mnist --platform=examples/mnist/platform/docker.yaml
  ```

- Run two tasks - `download` (download data) and `train`
  ```shell script
  python -m mlcube_docker_run run --mlcube=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/download.yaml
  python -m mlcube_docker_run run --mlcube=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/train.yaml
  ```
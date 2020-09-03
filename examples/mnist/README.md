# MNIST MLBox example
Directory structure:
```shell script
build/               # MLBox implementation. Contains source python code and Docker/Singularity recipes. 
platform/            # Platform definition files for the following runners:
   docker.yaml       #     Run MLBox locally using docker.
   singularity.yaml  #     Run MLBox locally using singularity.
   ssh.yaml          #     Run MLBox on a remote host using Docker or Singularity runtime.
run/                 # Task invocations specifications. Assigns values to task arguments.
tasks/               # Task definitions. For each task, a list of parameters and their types are listed.
workspace/           # Default place to store input/output artifacts.
mlbox.yaml           # Main MLBox definition file.
```

The `build` directory contains actual implementation of the MLBox workload. For instance, it can contain a python
project. The MNIST MLBox also stores Docker and Singularity recipes in this folder. MNIST box supports both container
runtimes, and users can choose what they want to use. It can be runner-dependent, but reference Docker/Singularity 
runners assumes that `build` directory exists and contains either `Dockerfile` or `Singularity.recipe`. In both cases,
the `build` directory becomes a root content directory during the image build phase (configure phase in MLBox terms).

The `platform` directory is a new one. It contains platform files for supported runner. This makes it possible to run
MLBox using different platforms ("runtimes") such as Docker or Singularity. Platform files do not need to be stored
in this directory, and users can store them wherever they want. This is useful for runners that run MLBoxes on remote
hosts (e.g., cloud or SSH runners). For instance, reference SSH runner can reuse platform configuration file for a
particular host across multiple MLBox implementations.

The `workspace` directory is default choice to store input/output artifacts such as datasets, models, log files etc.
One thing to keep in mind is, for instance, SSH runner syncs this directory between remote and local host. Artifacts
such as Singularity containers should not be stored here unless users want to sync them as well.

### End to end example using Singularity runner and GitHub source tree
- Setup and activate python virtual environment, install runner requirements
  ```shell script
  virtualenv -p python3.8 ./env
  source ./env/bin/activate
  pip install typer mlspeclib
  export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/mlbox_singularity_run:$(pwd)/runners/mlbox_docker_run
  ```

- Specify path to the Singularity image. In MNIST MLBox (`platform/singularity.yaml`), the path is
  `/opt/singularity/mlperf_mlbox_mnist-0.01.simg`. Either change it, or make sure the `/opt/singularity` the directory
  exists and writable, or users have permission to create one.

- Setup environment. This is optional step. 
  ```shell script
  export https_proxy=${http_proxy}
  ```

- Configure MNIST MLBox.
  ```shell script
  python -m mlbox_singularity_run configure --mlbox=examples/mnist --platform=examples/mnist/platform/singularity.yaml
  ```

- Run two tasks - `download` (download data) and `train`
  ```shell script
  python -m mlbox_singularity_run run --mlbox=examples/mnist --platform=examples/mnist/platform/singularity.yaml --task=examples/mnist/run/download.yaml
  python -m mlbox_singularity_run run --mlbox=examples/mnist --platform=examples/mnist/platform/singularity.yaml --task=examples/mnist/run/train.yaml
  ```

### End to end example using Docker runner and GitHub source tree
- Setup and activate python virtual environment, install runner requirements
  ```shell script
  virtualenv -p python3.8 ./env
  source ./env/bin/activate
  pip install typer mlspeclib
  export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/mlbox_singularity_run:$(pwd)/runners/mlbox_docker_run
  ```

- Setup environment. This step is optional. Docker runner uses `http_proxy` and `https_proxy` environmental variables
  (if set) and passes them to docker's build and run phases. 
  ```shell script
  export https_proxy=${http_proxy}
  ```

- Configure MNIST MLBox.
  ```shell script
  python -m mlbox_docker_run configure --mlbox=examples/mnist --platform=examples/mnist/platform/docker.yaml
  ```

- Run two tasks - `download` (download data) and `train`
  ```shell script
  python -m mlbox_docker_run run --mlbox=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/download.yaml
  python -m mlbox_docker_run run --mlbox=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/train.yaml
  ```
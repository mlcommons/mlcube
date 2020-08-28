# Singularity Runner
Singularity runner uses Singularity runtime for running MBoxes. It supports two commands - `configure` and `build`:
- `configure`: build Singularity container on a machine where it runs. 
- `run`: run MLBox in a Singularity container build at configure phase.

It follows the [MLBox Runners Specification v0.1](https://docs.google.com/document/d/1bL8bsAam71Ex8GI_6mQ59QlVf8RkVW-GvsbPweAd8C8)
to implement the command line interface:
```shell script
python -m mlbox_singularity_run configure --mlbox=MLBOX_PATH --platform=PLATFORM_FILE_PATH --task=TASK_FILE_PATH
```
where:
- `MLBOX_PATH` is the path to the MLBox root directory.
- `PLATFORM_FILE_PATH` is the path to the Singularity platform definition file. This file is usually located in the
  `platform` sub-directory of the MLBox.
- `TASK_FILE_PATH` is the path to the task run file. This file is usually located in the `run` sub-directory of the
  MLBox.

### Singularity Platform Definition File
The schema definition file is the part of the Singularity runner and is located in the source directory of the project:
[mlbox-singularity.yaml](mlbox_singularity_run/mlbox-singularity.yaml). Onle one parameter is defined in the schema - 
`image`. It is path to singularity image. It is relative to MLBOX_ROOT/workspace:
- By default, containers are stored in `$MLBOX_ROOT/workspace` if image is a file name.
- If it is a relative path, it is relative to `$MLBOX_ROOT/workspace`.
- Absolute paths (starting with `/`) are used as is.

One drawback of using workspace directory is that when using SSH runner, this directory is synchronized between remote
and local hosts what results in transferring the Singularity image back to user's local machine which may not be
desirable behavior. 

If path to image does not exist, singularity runner will attempt to create one. 

### Configure
Configure command line interface requires two mandatory arguments - `mlbox` and `platform`:
```shell script
python -m mlbox_singularity_run configure --mlbox=MLBOX_PATH --platform=PLATFORM_FILE_PATH
```

### End to end example using MNIST MLBOX and GitHub source tree
- Setup and activate python virtual environment, install runner requirements
  ```shell script
  virtualenv -p python3.8 ./env
  source ./env/bin/activate
  pip install typer mlspeclib
  export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/mlbox_singularity_run
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

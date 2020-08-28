# MLBox SSH runner

This is the port of the SHH runner from this [repository](https://github.com/sergey-serebryakov/mlbox/tree/feature/mlbox_runners_v2)

__Porting Status__  
- Support for new MLBox directory structure.
- Still runs only docker MLBoxes. Configure phase works, the run phase does not because of different directory tree.

## Pre-requisites
1. Remote server available via SSH/rsync.
2. Password-less login with public/private keys. If it's not the case, the ssh runner will be asking for a password 
   several times (quite annoying).
3. Remote server must provide python interpreter with ssh runner requirements (`mlspeclib`, `typer`). It can be either
   a system python or user python (virtualenv, conda etc.). Full path to the python executable must be known.
4. Python version should be at least 3.5 (or maybe 3.6 - type annotations are used).
 
## Current limitations (may not be the complete list)
1. Only docker-based MLBoxes are supported. So, remote host must provide docker/nvidia-docker.
2. Task files have the following path `run/{task_name}.yaml` (relative to MLBox root path).
3. MLBox contains the `build` directory with Dockerfile. Images are built, not pulled.
4. The whole `workspace` directory is synced with the local host after each task execution.
5. The SHH runner was tested with MNIST MLBox only.

> Pretty much all of these can easily be solved. In fact, the original repo do not have the first three limitations.

## How to use SSH runner using MNIST example MLBox
1. Copy the `ssh.yaml` platform file in the `platform` directory of a MLBox. 
   `platform.yaml`.
2. Edit `platform.yaml`. Change the following fields: 
   - `host`: IP address of the remote host
   - `user`: User name to use
   - `env->interpreter->python`: Python interpreter to use on a remote host to run SSH runner. If it's a custom
     installation, specify the absolute path.
   - `env->variables`: Dictionary of environmental variables to use. Will be used for docker build/run. In some cases,
     _http_proxy_ and _https_proxy_ variables need to be set.
3. Configure remote host (copy mlbox runners, mlbox, build docker image) - run in the mlbox root directory:
   ```shell script
   export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/mlbox_singularity_run:$(pwd)/runners/mlbox_ssh_run

   python -m mlbox_ssh_run configure --mlbox=examples/mnist --platform=examples/mnist/platform/ssh.yaml
   ```  
4. Run two tasks - download data and model training. After each task execution, local mlbox workspace directory
   will contain tasks' output artifacts (data sets, log files, models etc.):
   ```shell script
    python -m mlbox_ssh_run run --mlbox=examples/mnist --platform=examples/mnist/platform/ssh.yaml --task=examples/mnist/run/download.yaml

    python -m mlbox_ssh_run run --mlbox=examples/mnist --platform=examples/mnist/platform/ssh.yaml --task=examples/mnist/run/train.yaml
   ```









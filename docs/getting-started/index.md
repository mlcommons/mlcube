# Installation

Here is the step-by-step guide to install MLCube library and run simple MLCube cubes.

## Create a python environment
```
# Option 1: use python virtual environment `virtualenv`.
virtualenv -p python3.6 ./env_mlcube && source ./env_mlcube/bin/activate

# Option 2: use conda.
conda create -n mlcube python=3.6 && conda activate mlcube
```

## Install MLCube Runners
```
# Install MLCube Docker runner.
pip install mlcube-docker

# Optionally, install other runners.
# pip install mlcube-gcp
# pip install mlcube-k8s
# pip install mlcube-kubeflow
# pip install mlcube-singularity
# pip install mlcube-ssh

# Check that the docker runner has been installed.
mlcube config --get runners

# Show MLCube system settings.
mlcube config --list

# This system settings file (~/mlcube.yaml) configures local MLCube runners. Documentation
# for MLCube runners describes each of these parameters in details. A typical first step for
# enterprise environments that are usually behind a firewall is to configure proxy servers.
#  platforms:
#    docker:
#      env_args:
#        http_proxy: http://ADDRESS:PORT
#        https_proxy: https://ADDRESS:PORT
#      build_args:
#        http_proxy: http://ADDRESS:PORT
#        https_proxy: https://ADDRESS:PORT
```

## Explore with examples
A great way to learn about MLCube is try out the example MLCube cubes located [here](https://github.com/mlcommons/mlcube_examples).
```
git clone https://github.com/mlcommons/mlcube_examples.git && cd ./mlcube_examples
mlcube describe --mlcube ./mnist
```

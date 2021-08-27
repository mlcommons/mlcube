# Installation

Here is the step-by-step guide to run simple MLCube cubes.

## Create a python environment
```
# Create Python Virtual Environment
virtualenv -p python3 ./env && source ./env/bin/activate
```

## Install MLCube Runners
```
# Install MLCube Docker runner 
pip install mlcube-docker

# Optionally, setup host environment by providing the correct `http_proxy` and `https_proxy` environmental variables.
# export http_proxy=...
# export https_proxy=..

# Optionally, install other runners
# pip install mlcube-singularity
# pip install mlcube-ssh
# pip install mlcube-k8s
``` 

## Explore with examples
```
git clone https://github.com/mlcommons/mlcube_examples.git && cd ./mlcube_examples
```
A great way to learn about MLCube is try out the example MLCube cubes located [here](https://github.com/mlcommons/mlcube_examples).


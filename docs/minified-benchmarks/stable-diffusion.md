# Stable Diffusion

The benchmark reference for Stable Diffusion can be found in this [link](https://github.com/mlcommons/training/tree/master/stable_diffusion), and here is the PR for the minified benchmark implementation: [link](https://github.com/mlcommons/training/pull/696).

This video explains all the following steps:

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/Aa__68lX9Ks/0.jpg)](https://youtu.be/Aa__68lX9Ks)

## Project setup

An important requirement is that you must have Docker installed.

```bash
# Create Python environment and install MLCube Docker runner 
virtualenv -p python3 ./env && source ./env/bin/activate && pip install pip==24.0
pip install mlcube-docker
# Fetch the implementation from GitHub
git clone https://github.com/mlcommons/training && cd ./training
git fetch origin pull/696/head:feature/mlcube_sd && git checkout feature/mlcube_sd
cd ./stable_diffusion/mlcube
```

Inside the mlcube directory run the following command to check implemented tasks.

```shell
mlcube describe
```

### MLCube tasks

* Core tasks:

Download dataset.

```shell
mlcube run --task=download_data
```

Download models.

```shell
mlcube run --task=download_models
```

Train.

```shell
mlcube run --task=train
```

* Demo tasks:

Download demo dataset.

```shell
mlcube run --task=download_demo
```

Download models.

```shell
mlcube run --task=download_models
```

Train demo.

```shell
mlcube run --task=demo
```

### Execute the complete pipeline

You can execute the complete pipeline with one single command.

* Core pipeline:

```shell
mlcube run --task=download_data,download_models,train
```

* Demo pipeline:

Tested in an Nvidia A100 (40G)

```shell
mlcube run --task=download_demo,download_models,demo
```

**Note**: To rebuild the image use the flag: `-Pdocker.build_strategy=always` during the `mlcube run` command.

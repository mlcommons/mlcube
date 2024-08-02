# 3D Unet

The benchmark reference for 3D Unet can be found in this [link](https://github.com/mlcommons/training/tree/master/retired_benchmarks/unet3d/pytorch), and here is the PR for the minified benchmark implementation: [link](https://github.com/mlcommons/training/pull/695).

## Project setup

An important requirement is that you must have Docker installed.

```bash
# Create Python environment and install MLCube Docker runner 
virtualenv -p python3 ./env && source ./env/bin/activate && pip install pip==24.0 && pip install mlcube-docker
# Fetch the implementation from GitHub
git clone https://github.com/mlcommons/training && cd ./training
git fetch origin pull/695/head:feature/mlcube_3d_unet && git checkout feature/mlcube_3d_unet
cd ./image_segmentation/pytorch/mlcube
```

Inside the mlcube directory run the following command to check implemented tasks.

```shell
mlcube describe
```

### MLCube tasks

Download dataset.

```shell
mlcube run --task=download_data -Pdocker.build_strategy=always
```

Process dataset.

```shell
mlcube run --task=process_data -Pdocker.build_strategy=always
```

Train SSD.

```shell
mlcube run --task=train -Pdocker.build_strategy=always
```

### Execute the complete pipeline

You can execute the complete pipeline with one single command.

```shell
mlcube run --task=download_data,process_data,train -Pdocker.build_strategy=always
```

## Run a quick demo

You can run a quick demo that first downloads a tiny dataset and then executes a short training workload.

```shell
mlcube run --task=download_demo,demo -Pdocker.build_strategy=always
```

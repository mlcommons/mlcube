# ResNet

The benchmark reference for ResNet can be found in this [link](https://github.com/mlcommons/training/tree/master/retired_benchmarks/resnet-tf2), and here is the PR for the minified benchmark implementation: [link](https://github.com/mlcommons/training/pull/686).

## Project setup

```bash
# Create Python environment and install MLCube Docker runner 
virtualenv -p python3 ./env && source ./env/bin/activate && pip install pip==24.0 && pip install mlcube-docker

# Fetch the implementation from GitHub
git clone https://github.com/mlcommons/training && cd ./training/image_classification
git fetch origin pull/686/head:feature/resnet_mlcube && git checkout feature/resnet_mlcube
```

Go to mlcube directory and study what tasks MLCube implements.

```shell
cd ./mlcube
mlcube describe
```

### MLCube tasks

For the entire [IMAGENET](https://image-net.org/) dataset, you will need to download the complete dataset and place it in the workspace under the mlcube folder, then you can use the following tasks:

Process dataset.

```shell
mlcube run --task=process_data -Pdocker.build_strategy=always
```

Train RESNET.

```shell
mlcube run --task=train -Pdocker.build_strategy=always
```

Run compliance checker.

```shell
mlcube run --task=check_logs -Pdocker.build_strategy=always
```

### Running a small demo

To download the susample dataset and run the demo use the following command:

```shell
mlcube run --task=download_demo,demo -Pdocker.build_strategy=always
```

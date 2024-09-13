# Graph Neural Network

The benchmark reference for Graph Neural Network can be found in this [link](https://github.com/mlcommons/training/tree/master/graph_neural_network), and here is the PR for the minified benchmark implementation: [link](https://github.com/mlcommons/training/pull/762).

## Project setup

An important requirement is that you must have Docker installed.

```bash
# Create Python environment and install MLCube Docker runner 
virtualenv -p python3 ./env && source ./env/bin/activate && pip install pip==24.0 && pip install mlcube-docker
# Fetch the implementation from GitHub
git clone https://github.com/mlcommons/training && cd ./training
git fetch origin pull/762/head:feature/mlcube_graph_nn && git checkout feature/mlcube_graph_nn
cd ./graph_neural_network/mlcube
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

Train GNN.

```shell
mlcube run --task=train -Pdocker.build_strategy=always
```

### Execute the complete pipeline

You can execute the complete pipeline with one single command.

```shell
mlcube run --task=download_data,process_data,train -Pdocker.build_strategy=always
```

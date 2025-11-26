# Automotive - BEVFormer

The benchmark reference for BEVFormer can be found in this [link](https://github.com/mlcommons/mlperf_automotive/tree/master/automotive/camera-3d-detection), and here is the PR for the minified benchmark implementation: [link](https://github.com/mlcommons/mlperf_automotive/pull/87).

## Project setup

An important requirement is that you must have Docker installed.

```bash
# Create Python environment and install MLCube Docker runner 
virtualenv -p python3 ./env && source ./env/bin/activate && pip install pip==24.0 && pip install mlcube-docker
# Fetch the implementation from GitHub
git clone https://github.com/mlcommons/mlperf_automotive && cd ./mlperf_automotive
git fetch origin pull/87/head:feature/mlcube_bevformer && git checkout feature/mlcube_bevformer
cd ./automotive/camera-3d-detection/mlcube
```

Inside the mlcube directory run the following command to check implemented tasks.

```shell
mlcube describe
```

###  Extra requirements

You need to run these steps locally.

```shell
pip install mlc-scripts
```

Then run this command and follow the instructions.

```shell
mlcr get,bevformer,_mlc,_rclone
```

After this you will have a new configuration at `~/.config/rclone/rclone.conf`.

Finally you just need to copy that file into the `workpace` folder.

```shell
cp ~/.config/rclone/rclone.conf workspace
```

### MLCube tasks

* Demo tasks:

Download demo dataset and models.

```shell
mlcube run --task=download_demo -Pdocker.build_strategy=always
```

Train demo.

```shell
mlcube run --task=demo -Pdocker.build_strategy=always
```

### Execute the complete pipeline

You can execute the complete pipeline with one single command.

* Demo pipeline:

```shell
mlcube run --task=download_demo,demo -Pdocker.build_strategy=always
```

**Note**: To rebuild the image use the flag: `-Pdocker.build_strategy=always` during the `mlcube run` command.

# MNIST MLBox example


Execute in the mlbox root directory. You may need to run `docker` with sudo (`sudo docker ...`). Also, change or
remove http(s) variables.
```bash
# Build docker image
docker build ./examples/mnist/mlbox/build --build-arg http_proxy=${http_proxy} \
             --build-arg https_proxy=${https_proxy} -t mlperf/mlbox:mnist


# Setup python environment
virtualenv -p python3 ./env
source ./env/bin/activate
pip install mlspeclib
export PYTHONPATH=$(pwd)


# Run 'download' task
export MLBOX_DOCKER_ARGS="-e http_proxy=${http_proxy} -e https_proxy=${https_proxy}"
python3 mlbox_docker_run/docker_run.py --no-pull ./examples/mnist/mlbox/run/download.yaml


# Run 'train' task
python3 mlbox_docker_run/docker_run.py --no-pull ./examples/mnist/mlbox/run/train.yaml
```

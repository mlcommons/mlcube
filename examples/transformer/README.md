# Transformer MLCube

To run this using a runner, see the main README.

## Running Manually
Normally you would use a runner to do this, but to run manually,

Download data:
```
cd examples/transformer; sudo docker build -t xyhuang/mlcube-example-transformer:dev -f implementation/docker/dockerfiles/Dockerfile .
sudo nvidia-docker run -v workspace/:/input0 --net=host --privileged=true -t xyhuang/mlcube-example-transformer:dev --mlcube_task=downloaddata --raw_dir=/input0/translate_ende_raw
```

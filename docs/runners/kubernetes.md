# Kubernetes Runner

The Kubernetes Runner runs a MLCommons-Box on a Kubernetes cluster.

[Skip over to the fun part.](#prepare-a-kubernetes-cluster)

## Why Kubernetes?

One of the key goals of the MLCommons-Box project is to enable portability of ML models.
Kubernetes offers the a good set of abstractions to enable model training to be portable
across different compute platforms.

## Design

[Kubernetes Runner Proposal Doc](http://bit.ly/box-k8s-runner)

The Kubernetes runner takes in a kubernetes specific task file in the `run` directory and re-uses the Docker runner
platform config and prepares a Kubernetes Job manifest. The runner then creates the job on the Kubernetes cluster.

![Design](../assets/mlcommons-box-k8s.png)


The Kubernetes Runner takes in a MLBox run configuration file similar to other runners. With clear definitions of input
and output bindings.
Here's an example:

```yaml
schema_type: mlbox_invoke
schema_version: 1.0.0

task_name: kubernetes   # task name set to 'kubernetes'

input_binding:  # input parameters (name: value)
  data_dir:
    path: workspace/data
    k8s:
      pvc: mlbox-input
...
output_binding: # output parameters (name: value)
  model_dir:
    path: workspace/model
    k8s:
      pvc: mlbox-output
...
```

The Runner also re-uses the Docker platform config file. So it needs a Docker platform config file in the Box. Let's
revisit the Docker platform config.

```yaml
schema_type: mlcommons_box_platform
schema_version: 0.1.0

platform:
  name: "docker"
  version: ">=18.01"
container:
  image: "mlperf/mlbox:mnist"
```

With these two config files, the runner then constructs the following Kubernetes Job manifest. 

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  namespace: default
  generateName: mlcommons-box-mnist-
spec:
  template:
    spec:
      containers:
      - name: mlcommons-box-container
        image: mlperf/mlbox:mnist
        args:
        - --data_dir=/mnt/mlbox/mlbox-input/workspace/data
        - --model_dir=/mnt/mlbox/mlbox-output/workspace/model
        volumeMounts:
        - name: mlbox-input
          mountPath: /mnt/mlbox/mlbox-input
        - name: mlbox-output
          mountPath: /mnt/mlbox/mlbox-output
      volumes:
      - name: mlbox-input
        persistentVolumeClaim:
          claimName: mlbox-input
      - name: mlbox-output
        persistentVolumeClaim:
          claimName: mlbox-output
      restartPolicy: Never
  backoffLimit: 4
```

## Configure a Box for the runner

Prerequisites:

- A Kubernetes cluster
- `KUBECONFIG` for the cluster
- pre-created volumes for the Box

### Create a Task file

Based on the setup, create a specific task file for the Box.

#### Create a YAML file in the `run` directory

```bash
touch run/kubernetes.yaml
```

#### Set Schema for Task

```yaml
schema_type: mlbox_invoke
schema_version: 1.0.0
```

#### Set task name

```yaml
task_name: kubernetes
```

#### Set input and output bindings

```yaml
input_binding:  # input parameters (name: value)
  data_dir:
    path: workspace/data
    k8s:
      pvc: mlbox-input

output_binding: # output parameters (name: value)
  model_dir:
    path: workspace/model
    k8s:
      pvc: mlbox-output
```

## Run a box with the CLI

```bash
pip install mlcommons-box-k8s
mlcommons_box_k8s run \
  --mlbox=examples/mnist \
  --platform=examples/mnist/platforms/docker.yaml \
  --task=examples/mnist/run/kubernetes.yaml  \
  --loglevel INFO
```

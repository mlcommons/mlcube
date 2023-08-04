# Kubernetes Runner

!!! warning
    Work in progress. Some functionality described below may not be available.

The Kubernetes Runner runs a MLCube&reg; on a Kubernetes cluster.

## Why Kubernetes?

One of the key goals of the MLCube project is to enable portability of ML models. Kubernetes offers a good set of 
abstractions to enable model training to be portable across different compute platforms.

## Design

[Kubernetes Runner Proposal Doc](http://bit.ly/cube-k8s-runner)

The Kubernetes runner takes in a kubernetes specific task file in the `run` directory and re-uses the Docker runner
platform config and prepares a Kubernetes Job manifest. The runner then creates the job on the Kubernetes cluster.

![Design](../assets/mlcube-k8s.png)


## Configuration parameters

!!! attention
    Currently, users must create persistent volume claim (PVC) that points to an actual MLCube workspace directory.

```yaml
# By default, PVC name equals to the name of this MLCube (mnist, matmul, ...).
pvc: ${name}
# Use image name from docker configuration section.
image: ${docker.image}
```

The Kubernetes runner constructs the following Kubernetes Job manifest. 

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  namespace: default
  generateName: mlcube-mnist-
spec:
  template:
    spec:
      containers:
      - name: mlcube-container
        image: mlcommons/mlcube:mnist
        args:
        - --data_dir=/mnt/mlcube/mlcube-input/workspace/data
        - --model_dir=/mnt/mlcube/mlcube-output/workspace/model
        volumeMounts:
        - name: mlcube-input
          mountPath: /mnt/mlcube/mlcube-input
        - name: mlcube-output
          mountPath: /mnt/mlcube/mlcube-output
      volumes:
      - name: mlcube-input
        persistentVolumeClaim:
          claimName: mlcube-input
      - name: mlcube-output
        persistentVolumeClaim:
          claimName: mlcube-output
      restartPolicy: Never
  backoffLimit: 4
```


## Configuring MLCubes
This runner does not need configure step.


## Running MLCubes
Algorithm is following:

- Load Kubernetes configuration.
- Create job manifest (see above).
- Create job and wait for completion.

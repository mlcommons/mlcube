# Kubeflow Runner

!!! warning
    MLCube&reg; Kubeflow runner is work in progress. Some functionality described below may not be available.

Kubeflow supports two mandatory commands - `configure` and `run` with standard arguments - `mlcube`, `platform` and 
`task`. Users can configure SSH runner in system setting file, and override parameters on a command line.

!!! attention
    The `configure` command is not required, and does nothing when invoked.

## Configuration parameters
```yaml
# Use image name from docker configuration section
image: ${docker.image}
# PVC must point to the active MLCube workspace now.
pvc: '???'
# eg: set http://127.0.0.1:8000/pipeline when port forwarded svc/ml-pipeline-ui to port 8000
pipeline_host: ''
```

## Configuring MLCubes
This runner does not need configure step.


## Running MLCubes
To be done.

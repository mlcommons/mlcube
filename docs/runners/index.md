# Runners
A runner is a tool that runs MLCube cubes on one or multiple platforms. Examples of platforms are docker and
singularity containers, remote hosts, virtual machines in the cloud, etc.

A platform is configured in a platform configuration file. A cube can provide reference platform configurations that
users can modify to meet requirements of their infrastructures.

MLCube standard requires that all runners implement mandatory functionality. All reference runners implement it.
Users can develop their own runners to meet their specific requirements, such as security, authentication and
authorization policies and others.   


## Reference MLCube runners
Reference runners are:  
- `Docker Runner`: Runs cubes using docker runtime.  
- `Singularity Runner`: Runs cubes using singularity runtime.  
- `SSH Runner`: Runs cubes on remote hosts. SSH Runner uses other runners, such as Docker or Singularity runners, to
  run cubes on remote hosts.  


## Runner commands
Each runner exposes mandatory and optional functionality through a set of commands. This is similar to, for instance,
how Git implements its CLI (`git` followed by a specific command such as `checkout`, `pull`, `push` etc). Mandatory
MLCube runner commands are `configure` and `run`:  
- `configure`: Configure MLCube. Exact functionality depends on a runner type, but the goal is to ensure that 
  a cube is ready to run. The following are the examples of what can be done at configure phase: build docker or 
  singularity container, create python virtual environment, allocate and configure virtual machine in the cloud, copy
  cube to a remote host etc. Once configuration is successfully completed, it is assumed a runner can run that cube.  
- `run`: Run tasks defined in MLCube.  

Reference runners recognize three parameters - mlcube, platform and task.  
- `mlcube`: Path to a cube root directory. In future versions, this can be an URI with a specific protocol. Runners
  could support various MLCube implementations (excluding reference directory-based) such as docker/singularity 
  containers, GitHub repositories, compressed archives and others.  
- `platform`: Path to a YAML-based platform configuration file. If not present, a runner should use the
  default platforms to run a cube, or select the most appropriate or available in a user environment.  
- `task`: Path to a YAML-based task specification file. If not present, a runner can run the default task.  


## Command line interface
One way to run a MLCube is to follow the following template supported by all reference runners:
```
python -m RUNNER_PACKAGE --mlcube=MLCUBE_ROOT_DIRECTORY --platform=PLATFORM_FILE_PATH --task=TASK_FILE_PATH
```

Example command to configure MNIST Docker-based MLCube:
```
python -m mlcube_docker configure --mlcube=examples/mnist --platform=examples/mnist/platform/docker.yaml
```

Example command to run two tasks implemented by the MNIST Docker-based MLCube:
```
python -m mlcube_docker run --mlcube=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/download.yaml
python -m mlcube_docker run --mlcube=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/train.yaml
```

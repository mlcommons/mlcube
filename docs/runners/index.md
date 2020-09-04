# Runners
A runner is a tool that runs MLBox instances on one or multiple platforms. Examples of platforms are docker and
singularity containers, remote hosts, virtual machines in the cloud, etc.

A platform is configured in a platform configuration file. An MLBox can provide reference platform configurations that
users can modify to meet requirements of their infrastructures.

MLBox standard requires that all runners implement mandatory functionality. All reference runners implement it. Users
can develop their own runners to meet their specific requirements, such as security, authentication and authorization 
policies and others.   


## Reference MLBox runners
Reference MLBox runners are:  
- `Docker Runner`: Run MLBoxes using docker runtime.  
- `Singularity Runner`: Run MLBoxes using singularity runtime.  
- `SSH Runner`: Run MLBox on a remote host. SSH Runner uses other runners, such as Docker or Singularity runners, to
  run MLBoxes on remote hosts.  


## Runner commands
Each runner exposes mandatory and optional functionality through a set of commands. This is similar to, for instance,
how Git implements its API (`git` follows by a specific command such as `checkout`, `pull`, `push` etc). Mandatory
commands are `configure` and `run`:  
- `configure`: Configure MLBox. Exact functionality depends on a runner type, but the goal is to ensure that MLBox is
  ready to run. The following are the examples of what can be done at configure phase: build docker or singularity
  container, create python virtual environment, allocate and configure virtual machine in the cloud, copy MLBox to a
  remote host etc. Once configuration is successfully completed, it is assumed a runner can run MLBox.  
- `run`: Run MLBox's task.  

Reference MLBox runners recognize three parameters - mlbox, platform and task.  
- `mlbox`: Path to MLBox root directory. In future versions, this can be a MLBox URI with a specific protocol. Runners
  could support various MLBox implementations (excluding reference directory-based) such as docker/singularity 
  containers, GitHub repositories, compressed archives and others.  
- `platform`: Path to a YAML-based platform configuration file. If not present, MLBox runner should use the
  default platforms to run an MLBox, or select the most appropriate or available in a user environment.  
- `task`: Path to a YAML-based task specification file. If not present, MLBox can run the default task.  


## Command line interface
One way to run an MLBox is to follow the following template supported by all reference runners:
```
python -m RUNNER_PACKAGE --mlbox=MLBOX_ROOT_DIRECTORY --platform=PLATFORM_FILE_PATH --task=TASK_FILE_PATH
```

Example command to configure MNIST Docker-based MLBox:
```
python -m mlbox_docker_run configure --mlbox=examples/mnist --platform=examples/mnist/platform/docker.yaml
```

Example command to run two tasks implemented by the MNIST Docker-based MLBox:
```
python -m mlbox_docker_run run --mlbox=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/download.yaml
python -m mlbox_docker_run run --mlbox=examples/mnist --platform=examples/mnist/platform/docker.yaml --task=examples/mnist/run/train.yaml
```

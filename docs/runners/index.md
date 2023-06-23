# Runners
MLCube runners run MLCube cubes on one or multiple platforms. Examples of platforms are Docker and Singularity 
containers, Kubernetes, remote hosts, virtual machines in the cloud, etc. Every runner has a fixed set of configuration
parameters that users can change to configure MLCubes and runners for their environments. Concretely, runners can take
information from three different sources:

- [MLCube configuration](https://mlcommons.github.io/mlcube/getting-started/concepts/#mlcube-configuration) files that 
  are located in the root directory of each file-system based MLCube. Parameters in these files configure generic 
  parameters common for all environments, such as for instance, docker image names.
- [MLCube system settings](https://mlcommons.github.io/mlcube/getting-started/concepts/#system-settings) file that is 
  located (by default) in the user home directory (`~/mlcube.yaml`). This file is created automatically, and can be 
  used to configure parameters common for all MLCubes in a particular environments. They can include docker executable, 
  GPU and CPU docker arguments, user SSH and cloud credentials, etc.
- Optionally, runners can use parameters defined in `platform` section of MLCube configuration file. This section 
  usually contains information about such requirements as memory and persistent storage requirements, number of
  accelerators etc.

!!! important
    MLCube standard requires that all runners implement mandatory functionality. All reference runners implement it.
    Users can develop their own runners to meet their specific requirements, such as security, authentication and
    authorization policies, and others.   


## Reference MLCube runners
Reference runners are:

- [Docker Runner](https://mlcommons.github.io/mlcube/runners/docker-runner/): 
  runs cubes locally using docker runtime.  
- [GCP Runner](https://mlcommons.github.io/mlcube/runners/gcp-runner/): 
  runs cubes in Google cloud.  
- [Kubernetes Runner](https://mlcommons.github.io/mlcube/runners/kubernetes/): 
  runs cubes in Kubernetes.  
- [Kubeflow Runner](https://mlcommons.github.io/mlcube/runners/kubeflow/):
  runs cubes using Kubeflow.  
- [Singularity Runner](https://mlcommons.github.io/mlcube/runners/singularity-runner/): 
  runs cubes using singularity runtime.    
- [SSH Runner](https://mlcommons.github.io/mlcube/runners/ssh-runner/):
  runs cubes on remote hosts. SSH Runner uses other runners, such as Docker or Singularity runners, to run cubes on 
  remote hosts.  


## Runner commands
Each runner exposes mandatory and optional functionality through a set of commands. This is similar to, for instance,
how Git implements its CLI (`git` followed by a specific command such as `checkout`, `pull`, `push` etc.). Mandatory
MLCube runner commands are `configure` and `run`:  

- `configure`: Configure MLCube. Exact functionality depends on a runner type, but the goal is to ensure that 
  a cube is ready to run. The following are the examples of what can be done at configure phase: build docker or 
  singularity container, create python virtual environment, allocate and configure virtual machine in the cloud, copy
  cube to a remote host etc. Once configuration is successfully completed, it is assumed a runner can run that cube.  
- `run`: Run tasks defined in MLCube.  

Reference runners recognize three parameters - mlcube, platform and task.

- `mlcube`: Path to a cube root directory. In future versions, this can be a URI with a specific protocol. Runners
  could support various MLCube implementations (excluding reference directory-based) such as docker/singularity 
  containers, GitHub repositories, compressed archives and others.  
- `platform`: Name of a platform. By default, runners create standard platform configurations in MLCube system settings
  file with predefined names. Users can change those names and use them on a command line. For instance, they can have
  different names for an 8-way GPU server and a simple CPU-based server for SSH runner.  
- `task`: Name of a task, or comma-separated list of tasks.  


## Command line interface
One way to run a MLCube is to follow the following template supported by all reference runners:
```shell
mlcube COMMAND --mlcube=MLCUBE_ROOT_DIRECTORY --platform=PLATFORM_NAME --task=TASK_NAME
```

Example command to configure MNIST Docker-based MLCube:
```shell
mlcube configure --mlcube=examples/mnist --platform=docker
```

Example command to run two tasks implemented by the MNIST Docker-based MLCube:
```shell
mlcube run --mlcube=examples/mnist --platform=docker --task=download
mlcube run --mlcube=examples/mnist --platform=docker --task=train
```

## Configuration subsystem
Runners are configured using information from three different sources:

- The base configuration comes from the 
  [system settings](https://mlcommons.github.io/mlcube/getting-started/concepts/#system-settings) file. By default, 
  the location of this file is `${HOME}/mlcube.yaml`. It is created automatically whenever a user runs `mlcube` command 
  line tool. The purpose of this file is to provide system-wide configuration for runners that are specific to user and 
  their environment. This is kind of information that should not generally present in MLCube configuration files 
  (next item). It should include such information as docker executable (docker, sudo docker, nvidia-docker, podman, 
  etc.), docker-specific runtime arguments, user credentials for GCP and remote hosts, information about 
  remote hosts etc.
- The [MLCube configuration](https://mlcommons.github.io/mlcube/getting-started/concepts/#mlcube-configuration) file 
  that is available with each MLCube cube. This file contains (as of now) such parameters, as docker and singularity 
  image names, MLCube resource requirements and tasks. This information overrides information from system settings file.
- Configuration that is provided on a command line. Users are allowed (but not encouraged) to override parameters on
  the fly when they run MLCube cubes.

### MLCube System settings file
Example of MLCube system settings file (`${HOME}/mlcube.yaml`) is the following. As it was mentioned above, it is
created automatically by searching packages that start with `mlcube_`. Such packages must provide `get_runner_class`
function that must return a runner class derived from `Runner`. 
```yaml
# This section maps a runner name to a runner package. This is one way how developers can plug in
# their custom runners. Python package, or this type of association, could be one of many ways to
# implement runners. 
runners:
  docker:                      # MLCube Docker reference runner
    pkg: mlcube_docker
  gcp:                         # MLCube Google Cloud Platform reference runner
    pkg: mlcube_gcp
  k8s:                         # MLCube Kubernetes reference runner
    pkg: mlcube_k8s
  kubeflow:                    # MLCube KubeFlow reference runner
    pkg: mlcube_kubeflow
  singularity:                 # MLCube Singularity reference runner
    pkg: mlcube_singularity
  ssh:                         # MLCube SSH reference runner
    pkg: mlcube_ssh
# This section defines configurations for the above runners. It is a dictionary mapping platform
# name to a runner configuration. These names could be any names. For instance, users can have 
# two platforms for an SSH runner pointing to two different remote hosts. The platform names are
# those passed to mlcube tool using `--platform` command line argument.
platforms:
  # Docker runner configuration. The only parameter that is supposed to be present in MLCube
  # configuration files is image name (`image`). For other parameters, see Docker Runner
  # documentation page.
  docker:
    runner: docker
    image: ${docker.image}
    docker: docker
    env_args: {}
    gpu_args: ''
    cpu_args: ''
    build_args: {}
    build_context: .
    build_file: Dockerfile
    build_strategy: pull
  # Google Cloud Platform runner. None of these configuration parameters are supposed to be 
  # present in MLCube configuration files.  For other parameters, see GCP Runner documentation 
  # page.
  gcp:
    runner: gcp
    gcp:
      project_id: ''
      zone: ''
      credentials: ''
    instance:
      name: ''
      machine_type: ''
      disk_size_gb: ''
    platform: ''
  # Kubernetes runner. None of these configuration parameters are supposed to be present in 
  # MLCube configuration files.  For other parameters, see Kubernetes Runner documentation page.
  k8s:
    runner: k8s
    pvc: ${name}
    image: ${docker.image}
    namespace: default
  # Kubeflow runner. None of these configuration parameters are supposed to be present in 
  # MLCube configuration files.  For other parameters, see Kubeflow Runner documentation page.
  kubeflow:
    runner: kubeflow
    image: ${docker.image}
    pvc: ???
    namespace: default
    pipeline_host: ''
  # Singularity runner configuration. The only parameter that is supposed to be present in MLCube
  # configuration files is image name (`image`). For other parameters, see Singularity Runner
  # documentation page.
  singularity:
    runner: singularity
    image: ${singularity.image}
    image_dir: ${runtime.workspace}/.image
    singularity: singularity
    build_args: --fakeroot
    build_file: Singularity.recipe
  # SSH runner. None of these configuration parameters are supposed to be present in 
  # MLCube configuration files.  For other parameters, see SSH Runner documentation page.
  ssh:
    runner: ssh
    host: ''
    platform: ''
    remote_root: ''
    interpreter: {}
    authentication: {}
# Dedicated section to define future data `storage` layer. It's work in progress.
storage: {}
```

Users can and should update configuration parameters according to their environment. Also, please backup this file
regularly. One possibility is to move this file to a location that is regularly snapshoted. When non-standard path is
used, users must define a `MLCUBE_SYSTEM_SETTINGS` environment variable that points to this new location.

Users can also duplicate runner sections assigning names accordingly, like it was mentioned above. For instance,
users can have two ssh sections one for each different host:
```yaml
platforms:
  my_dev_server_1:
    runner: ssh
    # Other parameters ...
  my_dev_server_2:
    runner: ssh
    # Other parameters ...
```
and then
```shell
mlcube run --mlcube=. --task=MY_TASK --platform=my_dev_server_2
```

MLCube runtime provides minimal functionality to interact with system settings file:
```shell
# Print system settings file
mlcube config --list

# Query a value associated with the particular key
mlcube config --get runners
mlcube config --get platforms.docker

# Create a new fresh platform for this runner
mlcube config --create-platform ssh my_dev_server_1
mlcube config --get platforms.my_dev_server_1

# Rename platform
mlcube config --rename-platform my_dev_server_1 my_dev_server_2
mlcube config --get platforms.my_dev_server_2

# Remove platform from the system settings file
mlcube config --remove-platform my_dev_server_2

# Create a new platform copying configuration of one of existing platforms.
mlcube config --copy-platform EXISTING_PLATFORM NEW_PLATFORM

#  Rename existing runner
mlcube config --rename-runner OLD_NAME NEW_NAME

# Remove runner
mlcube config --remove-runner NAME
```

!!! attention
    Removed standard runners (MLCube reference runners) will be recreated when mlcube runs next time.
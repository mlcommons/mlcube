# MLCube Docker Runner
MLCube Docker Runner runs cubes (packaged Machine Learning (ML) workloads) in the docker environment. 

1. Create MLCube system settings file. It should be located in a user home directory: `${HOME}/mlcube.yaml`. If this 
   is not possible or not convenient, this file can be placed in any location given that environment variable
   `MLCUBE_SYSTEM_SETTINGS` points to this file. 
2. Put the following in this file:
   ```yaml
   docker:
     docker: "Docker run command. Examples: docker, nvidia-docker, sudo docker, podman, .... Default is `docker`."      
     env_args: "Dictionary of environment variables for docker (e.g. proxy: proxy_http:...). This is optional."
     build_strategy: auto
     gpu_args: "..."               # Docker run arguments when accelerator_count > 0.
     cpu_args: "..."               # Docker run arguments when accelerator_count == 0.
   ```
   Comments:
     - If no environment variables are needed, remove this key. 
     - Build strategy is set to auto to automatically build docker images. 
   
   Example configuration file:
   ```yaml
   docker:
     # Executable (docker, podman, sudo docker ...).
     docker: docker
     # Build a docker image every time a task is executed ("docker build ..." with cache).
     build_strategy: auto
     # Docker run arguments when accelerator_count == 0.
     cpu_args: >-
       --rm  --net=host --uts=host --ipc=host --ulimit stack=67108864 --ulimit memlock=-1
       --privileged=true --security-opt seccomp=unconfined
     # Docker run arguments when accelerator_count > 0.
     gpu_args: >-
       --rm  --gpus=all --net=host --uts=host --ipc=host --ulimit stack=67108864 --ulimit memlock=-1
       --privileged=true --security-opt seccomp=unconfined
     # Environmental variables for run phase (-e NAME=VALUE).
     env_args:
       http_proxy: "${oc.env:http_proxy}"
       https_proxy: "${oc.env:https_proxy}"
     # Arguments for build phase (--build-args NAME=VALUE).
     build_args:
       http_proxy: "${oc.env:http_proxy}"
       https_proxy: "${oc.env:http_proxy}"
   ```
   Comment:
     - `${oc.env:http_proxy}` means takes `http_proxy` environment variable. If not proxy is required, remove
       `env_args` and `build_args` sections.

## Deprecated
Read  Docker Runner documentation [here](../../docs/runners/docker-runner.md).
  
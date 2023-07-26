# Docker Runner
Docker runner uses docker/nvidia-docker/podman to run MLCube&reg; cubes. It supports two mandatory commands - `configure` and
`run` with standard arguments - `mlcube`, `platform` and `task`. Users can configure docker runner in MLCube 
configuration file, system setting file, and override parameters on a command line.


## Configuration parameters
MLCube reference docker runner supports the following configuration parameters (with default values):
```yaml
# Docker Image name, for instance "mlcommons/mnist:0.0.1"
image: ${docker.image}
# Docker executable (docker, podman, sudo docker ...).
docker: docker

# Environmental variables for run command (-e name=value).
env_args: {}               

# Docker run arguments when ${platform.accelerator_count} > 0.
gpu_args: ''
# Docker run arguments when ${platform.accelerator_count} == 0.
cpu_args: ''

# Docker build arguments (--build-arg name=value)
build_args: {}
# Docker build context relative to $MLCUBE_ROOT. Default is $MLCUBE_ROOT.
build_context: .
# Docker file relative to $MLCUBE_ROOT, default is `$MLCUBE_ROOT/Dockerfile`.
build_file: Dockerfile
# MLCube configuration strategy
#   'pull': never try to build, always pull
#   'auto': build if image not found and dockerfile found
#   'always': build even if image found
build_strategy: pull
```


## Configuring MLCubes
Docker runner uses `build_strategy` configuration parameter to decide on build strategy:

- `pull`: always try to pull docker image, never attempt to build.
- `auto`: use `build_context` and `build_file` to decide if `Dockerfile` exists. If it exists, build the image.
- `always`: build docker image always when running MLCube tasks.

Docker runner under the hood runs the following command line:  
```
${docker.docker} build ${docker.build_args} -t ${docker.image} -f ${recipe} ${context}
```  
where:

- `${docker.docker}` is the docker executable.
- `${docker.build_args}` docker build arguments.
- `${docker.image}` is the docker image name.  
- `${recipe}` is the `${docker.build_file}` relative to context
- `${context}` is the `${docker.build_context}` relative to MLCube root directory.

Users do not need to run the configure command explicitly, docker runner uses the following logic to decide what to do
before running any task. If strategy is `always`, build the docker image. Else, if docker image exists, do nothing, else
build or pull depending on what strategy is and if Dockerfile exists in MLCube directory. 


## Running MLCubes
Docker runner runs the following command:    
```
${docker.docker} run {run_args} ${docker.env_args} {volumes} ${docker.image} {task_args}
```  
where:

- `${docker.docker}` is the docker executable.
- `{run_args}` are either `${docker.cpu_args}` or `${docker.gpu_args}` depending on `${platform.num_accelerators}` value.
- `${docker.env_args}` are the docker environmental variables.
- `{volumes}` are the mount points that the runner automatically constructs based upon the task input/output
  specifications.  
- `${docker.image}` is the docker image name.  
- `{task_args}` is the task command line arguments, constructed automatically by the runner.  
 
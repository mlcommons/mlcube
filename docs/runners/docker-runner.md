# Docker Runner
Docker runner uses docker/nvidia-docker to run MLCommons-Box boxes. It supports two mandatory commands - `configure` and
`run` with standard arguments - `mlbox`, `platform` and `task`. Docker platform configuration is used to configure
docker runners.

## Platform Configuration File
Docker platform configuration file is a YAML file that follows `mlcommons_box_platform` ML schema. The configuration file for the
reference MNIST box is the following:
```yaml
schema_type: mlcommons_box_platform
schema_version: 0.1.0

platform:
  name: "docker"                                       # 'docker' or 'nvidia-docker'.
  version: ">=18.01"                                   # Reserved for future use.
configuration:
  image: "mlperf/mlbox:mnist"                          # Docker image name.
  parameters: "--rm --net=host --privileged=true"      # Docker 'run' parameters.
```

## Additional configuration
In current implementation, Docker runner uses `http_proxy` and `https_proxy` environmental variables (if set) during
configure and run phases:  
- __configure__: `docker build ... --build-args http_proxy=${http_proxy} --build-args https_proxy=${https_proxy} ...`  
- __run__: `docker run ... -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} ...`  


## Configuring MLBoxes
Docker runner uses `{MLCOMMONS_BOX_ROOT}/build` directory as the build context directory. This implies that all files
that must be packaged in a docker image, must be located in that directory, including source files, python requirements,
resource files, ML models etc. The docker recipe must have the standard name `Dockerfile`.

If `Dockerfile` file exists in `{MLCOMMONS_BOX_ROOT}/build`, the Docker runner assumes that it needs to `build` a docker
image. If that file does not exist, the Docker runner will `pull` the docker image with the specified name.

Docker runner under the hood runs the following command line:  
```
cd {build_path}; docker build {env_args} -t {image_name} -f Dockerfile .
```  
where:  
- `{build_path}` is `{MLCOMMONS_BOX_ROOT}/build` root directory.  
- `{env_args}` is the arguments retrieved from user environment. Currently, only `http_proxy` and `https_proxy` are
  supported.  
-  `{image_name}` is the image name defined in the platform configuration file.  

When pulling and image, the command is the following: `docker pull {image_name}`. 

> The `configure` command is optional and users do not necessarily need to be aware about it. The Docker runner
> auto-detects if docker image exists before running a task, and if it does not exist, the docker runner runs the 
> `configure` command. During the `configure` phase, docker runner does not check if docker image exists. This means the
> following. If some of the implementation files have been modified, to rebuild the docker image users need to run
> the `configure` command explicitly.


## Running MLBoxes
Docker runner runs the following command:    
```
{docker_runner} run {container_params} {volumes} {env_args} {image_name} {args}
```  
where:    
- `{docker_runner}` is either docker or nvidia-docker, it is specified in the docker platform configuration file 
  (platform -> name).  
- `{container_params}` are the container parameters specified in the docker platform configuration file (configuration
  -> parameters). If they are not definem, the default parameters are used (`--rm --net=host --privileged=true`).
- `{volumes}` are the mount points that the runner automatically constructs based upon the task input/output
  specifications.  
- `{env_args}` is the arguments retrieved from user environment, currently, only `http_proxy` and `https_proxy` are
  supported.  
- `{image_name}` is the image name from the platform configuration file (configuration -> image).  
- `{args}` is the task command line arguments, constructed automatically by the runner.  
 
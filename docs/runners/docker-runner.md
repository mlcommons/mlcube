# Docker Runner
Docker runner uses docker/nvidia-docker to run MLCommons-Box boxes. It supports two mandatory commands - `configure` and
`run` with standard arguments - `mlbox`, `platform` and `task`. Docker platform configuration is used to configure
docker runner.

## Platform Configuration File
Docker platform configuration file is a YAML file that follows `mlbox_docker` ML schema. The configuration file for the
reference MNIST box is the following:
```yaml
schema_version: 1.0.0
schema_type: mlbox_docker

image: mlperf/mlbox:mnist   # Docker image name
docker_runtime: docker      # Docker executable: docker or nvidia-docker
```

## Additional configuration
In current implementation, Docker runner uses `http_proxy` and `https_proxy` environmental variables (if set) during
configure and run phases:  
- __configure__: `docker build ... --build-args http_proxy=${http_proxy} --build-args https_proxy=${https_proxy} ...`  
- __run__: `docker run ... -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} ...`  


## Build command
Docker runner uses `{MLCOMMONS_BOX_ROOT}/build` directory as the build context directory. This implies that all files
that must be packaged in a docker image, must be located in that directory, including source files, python requirements,
resource files, ML models etc. The docker recipe must have the standard name `Dockerfile`.

In current implementation, only docker `build` is supported (i.e., Dockerfile must present). In future releases, Docker
runner will support docker `pull` as well.

Docker runner under the hood runs the following command line:  
```
cd {build_path}; docker build {env_args} -t {image_name} -f Dockerfile .
```  
where:  
- `{build_path}` is `{MLCOMMONS_BOX_ROOT}/build` root directory.  
- `{env_args}` is the arguments retrieved from user environment. Currently, only `http_proxy` and `https_proxy` are
  supported.  
-  `{image_name}` is the image name defined in the platform configuration file.  


## Run command
Docker runner runs the following command:    
```
{docker_runtime} run --rm --net=host --privileged=true {volumes} {env_args} {image_name} {args}
```  
where:    
- `{docker_exec}` is the docker_runtime value from the Docker platform configuration file.  
- `{volumes}` are the mount points that the runner automatically constructs based upon the task input/output
  specifications.  
- `{env_args}` is the arguments retrieved from user environment, currently, only `http_proxy` and `https_proxy` are
  supported.  
- `{image_name}` is the image name from the platform configuration file.  
- `{args}` is the task command line arguments, constructed automatically by the runner.  
 
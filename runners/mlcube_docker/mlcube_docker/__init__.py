"""MLCube reference docker runner.

# Introduction
Docker runner runs MLCubes using docker or its alternatives/competitors such as podman. MLCube configuration file
must provide `docker` section with runner configuration. The only mandatory parameter is image name (image):
```yaml
docker:
    image: ubuntu:18.04
```
Other supported parameters are listed in the default configuration (`mlcube_docker.docker_run.Config.DEFAULT`).

# Configure
MLCube docker runner builds or pulls docker images at configure phase (`mlcube configure ...`). As with other runners,
users do not need to run this command explicitly. MLCube docker runner automatically identifies if it needs to configure
MLCubes before running each task.

> Docker runner will automatically run the configure command when running tasks in the following two
> cases: (1) build strategy is 'always' or (2) docker does not exist locally. This means that if source code has
> changed, the mlcube won't rebuild the image.

The MLCube docker runner parameter `mlcube_docker.docker_run.Config.BuildStrategy` (`build_strategy`) defines how
configuration is performed.

# Run
Docker runner supports tasks with and without custom entrypoints.

For task that do not define entrypoints, Docker runner assumes docker images define entrypoints. These entrypoints are
defined in Dockerfile build recipes, and are  executable scripts that accepts task name as their first positional
arguments. Other task-specific arguments follow task name positional argument. In other words, task name and task
arguments are COMMAND in docker terminology that docker will pass to image entry point.
If image entry point is `python /workspace/mnist.py`, and current task is `download` with the single output directory
parameter `data_dir` with value equal to `/datasets/mnist/`, the MLCube docker runner will build the following command:
```shell
docker run ... IMAGE_NAME download --data_dir=/datasets/mnist/
```
This will result in the following inside the docker container:
```shell
python /workspace/mnist.py download --data_dir=/datasets/mnist/
```

When tasks define their custom entry points, MLCube docker runner will override image entrypoint and will not be passing
task name as the first positional argument to this custom entrypoint script. Looking at the example presented above, if
the `download` task defines `/workspace/download.py` entrypoint, the MLCube docker runner will build the following
command:
```shell
docker run ... --entrypoint=/workspace/download.py IMAGE_NAME --data_dir=/datasets/mnist/
```
This will result in the following inside the docker container:
```shell
python /workspace/download.py --data_dir=/datasets/mnist/
```
"""


def get_runner_class():
    """Return docker runner python class.

    Returns:
        DockerRun class.
    """
    from mlcube_docker.docker_run import DockerRun
    return DockerRun

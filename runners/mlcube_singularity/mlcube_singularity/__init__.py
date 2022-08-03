"""MLCube reference singularity runner.

# Introduction
Singularity runner runs MLCubes using singularity. MLCube configuration can provide `singularity` section with runner
configuration. The only mandatory parameter is image name (image):
```yaml
singularity:
    image: ubuntu-18.04.sif
```
If no `singularity` section exists in mlcube.yaml, but `docker` section exists, the MLCube singularity runner will try
to use that information. This will work for the following two cases:
- Docker image does not need to be built locally, and is available at docker hub (in other words, can be pulled).
- Docker section references docker archive (using `tar_file` docker configuration parameter).

Other supported parameters are listed in the default configuration: `mlcube_singularity.singularity_run.Config.DEFAULT`.

# Configure
If SIF image file exists, no actions are performed (this means singularity runner will never rebuild the image file if,
for instance, source files have changed). If no file exists, singularity will build SIF image either from docker image
or docker archive file, or using local source files and Singularity recipe.

# Run
At run phase, the MLCube runner rune the `configure` command if SIF file does not exist. The runner runs tasks with and
without custom entrypoints similar to Docker runner.
If a task does not define its custom entrypoint, MLCube singularity runner assumes the image defines default entry
point (`runscript`) that accepts a task name as its first positional argument, and task-specific arguments follow.
The singularity runner `runs` the task in the following way:
```shell
singularity run ... TASK_NAME TASK_ARGS
```
If a task defines its entrypoint, the MLCube singularity runner will use the following command to `execute` the task:
```
singularity run ... ENTRY_POINT TASK_ARGS
```
Similarly to docker runner, no task name is provided.
"""


def get_runner_class():
    from mlcube_singularity.singularity_run import SingularityRun
    return SingularityRun

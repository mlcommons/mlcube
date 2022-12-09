# MLCube concepts

### Command Line Arguments
MLCube runtime and MLCube runners accept multiple command line arguments. They can be classified into two categories:

- Fixed command-specific parameters such as `--mlcube`, `--platform` and `--task` for the MLCube's `run` command, or
  `create_platform` and `rename_platform` for the `config` command.
- Parameters that override system settings or MLCube configuration. These parameters start with `-P` and should follow
  [OmegaConf](https://omegaconf.readthedocs.io/)'s format (MLCube uses this library to manage its settings and 
  configurations). For instance, to override docker runner settings and instruct it to always build MLCube images,
  one should provide the following command line argument: `-Pdocker.build_strategy=always`.

These command line arguments override system settings and MLCube configuration parameters. 
The [Command Line Interface](https://mlcommons.github.io/mlcube/getting-started/cli/) section provides detailed 
description of MLCube commands and their arguments.

### Effective MLCube configuration
`Effective MLCube configuration` is the actual configuration that MLCube runners use to run MLCubes. This effective
configuration is built using the following algorithm. A platform configuration for a runner is retrieved from system 
settings (users provide the platform name on a command line by passing `--platform=PLATFORM_NAME` argument). Then, 
the MLCube configuration is loaded from the MLCube project to run, and this configuration can override default 
configuration retrieved from system settings. The source for this configuration is specified by a user on a command line
using `--mlcube=MLCUBE_PATH` argument. The third source of configuration is the command line. Users can provide 
configuration parameters that override default behavior of a MLCube runner, or default parameters of the MLCube project.
These parameters start with `-P`, for instance, `-Pdocker.build_strategy=always`. These parameters have the highest 
priority and override any other parameters loaded so far.

### MLCube Configuration
`MLCube Configuration` provide MLCube-specific configuration, such as implemented `tasks` and, optionally, specific 
platform (hardware) requirements, for instance, GPU and host memory required to run the tasks. This configuration 
overrides system settings. For MLCubes that are distributed via GitHub (with source files), this configuration is
stored in a YAML file with default location being `${MLCUBE_ROOT}/mlcube.yaml`. The 
[MLCube configuration](https://mlcommons.github.io/mlcube/getting-started/mlcube-configuration/) 
section provides detailed description.

### MLCube Configuration Parameter
`MLCube configuration paramter` is a configuration parameter for MLCube runners or MLCube projects that has (usually)
a type from the following set: (integer, floating point number, string, bool). Every MLCube runner and all MLCube 
projects have such parameters, usually organized in a hierarchy. Users can also provide these parameters on a command
line when they interact with MLCube runtime to override default values for these parameters. MLCube uses 
[OmegaConf](https://omegaconf.readthedocs.io/) library to manage its configuration. When users provide these parameters
on a command line, they need to follow OmegaConf rules, in particular, nested parameters should use `.` symbol. Also,
when providing these parameters on a command line, these parameters must have `-P` prefix. Several examples: 
```shell
# Overriding top level parameter. Here, the `description` is a parameter in a global namespace. 
-Pdescription="MLCube project description"

# Overriding nested parameter. Here, the `build_strategy` is a parameter defined in the `docker` namespace.   
-Pdocker.build_strategy=always
```

### MLCube Home Directory
`MLCube home directory` is the synonym for [MLCube Root Directory](#mlcube-root-directory).

### MLCube Runtime
The `MLCube Runtime` term is used to describe the core MLCube library with MLCube runners. MLCube runtime is responsible
for managing MLCube system settings and MLCube configurations, and run MLCubes in various environments.

### MLCube Root Directory
`MLCube root directory` is the directory that contains MLCube configuration file (`mlcube.yaml`). This definition 
applies to MLCubes that are distributed, for instance, via GitHub.

### MLCubes
The term `MLCubes` (or `MLCube project` in singular form) refers to Machine Learning projects packaged and distributed 
using MLCube stack.

### Platform
A `platform` is a configured instance of a MLCube runner. Every runner has a default configured instance with the same
name as runner. For instance, the MLCube docker runner (named `docker`) has a default platform named `docker` as well.
Users may find it useful to have multiple configured instances (platforms) of one MLCube runner. For instance, if a user
has personal and corporate accounts in some cloud provider, they can have multiple platforms - one for each account.
Users directly interact with platforms via command line argument `--platform`. System settings provide platform 
configurations, and users can manually edit system settings to add new platforms, or use MLCube's runtime `config` 
command to perform basic operations with system settings, such as creating a new platform. See System Settings 
description for more detailed explanation of MLCube runners and platforms, and how they relate to each other.

### Runner
`MLCube runners` are workhorses of MLCube runtime. They run MLCubes in different environments, such as docker and 
singularity, remote on-prem or cloud compute nodes, and orchestration engines such as Kubernetes and KubeFlow. As part
of MLCube ecosystem, we provide multiple MLCube reference runners. Users do not directly interact with MLCube runners,
instead they interact with `platforms`, which are configured instances of MLCube runners.

### System Settings
MLCube `System Settings` configure MLCube and MLCube runners at a system level. The term `system level` here implies 
that these settings are not tied to particular MLCubes (MLCube compliant ML projects). Instead, these settings are 
used by MLCube runners on every machine where MLCube runtime is configured to use these settings. By default, system
settings are stored in a YAML file with default location being `${MLCUBE_ROOT}/mlcube.yaml`. The location can be
overriden by exporting the `MLCUBE_SYSTEM_SETTINGS` environment variable. Detailed description of system settings
is [here](https://mlcommons.github.io/mlcube/getting-started/system-settings/).

### Task
MLCube projects expose their functionality via `tasks`. A task implements one particular function, such as downloading
a machine learning dataset, preprocessing this dataset, training a machine learning model, testing a machine learning 
model or registering a machine learning model with the external model registry. It's up to developers to decide how they
want to organize their projects into tasks. A close analogy would be machine learning pipelines composed of multiple
steps organized into directed acyclic graph. Tasks in MLCubes are like steps on these pipelines, except that MLCube 
runtime at this point is not aware about task dependencies, and so the MLCube task model could be described as 
`bag of tasks` (similarly to `bag of words` term used in natural language processing to describe machine learning models
that do not take into account positions of words in sentences).

The MLCube examples [project](https://github.com/mlcommons/mlcube_examples) implements several MLCubes, including 
[MNIST MLCube](https://github.com/mlcommons/mlcube_examples/blob/master/mnist/mlcube.yaml) that implements two tasks:
`download` (download MNIST dataset) and `train` (train a simple classifier).

Users can can instruct [MLCube runtime](#mlcube-runtime) to execute a particular task or tasks by providing `--task` 
command line argument:

- `mlcube run --mlcube=. --task=download --platform=docker`: execute one task (`download`). 
- `mlcube run --mlcube=. --task=download,train --platform=docker`: execute two tasks named(`download` and `train`).

MLCube runtime executes tasks in the order provided by users. In the above example, MLCube will run the `download` task,
and then - the `train` task.

### Workspace
A `workspace` is a directory where input and output artifacts are stored. By default, its location is 
`${MLCUBE_ROOT}/workspace`. Users can override this parameter on a command line by providing the `--workspace` argument.
Users need to provide this parameter each time they run MLCube task, even when these tasks are logically grouped into 
one execution. A better alternative would be to run multiple tasks at the same time (see [task section](#task)).

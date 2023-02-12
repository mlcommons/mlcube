# MLCube Configuration

MLCube configuration provides information about MLCube's authors, requirements and  
[tasks](https://mlcommons.github.io/mlcube/getting-started/concepts/#task). This is example configuration for
the [MNIST MLCube](https://github.com/mlcommons/mlcube_examples/tree/master/mnist):

```yaml
name: mnist
description: MLCommons MNIST MLCube example
authors:
  - {name: "First Second", email: "first.second@company.com", org: "Company Inc."}

platform:
  accelerator_count: 0
  accelerator_maker: NVIDIA
  accelerator_model: A100-80GB
  host_memory_gb: 40
  need_internet_access: True
  host_disk_space_gb: 100

docker:
  image: mlcommons/mnist:0.0.1

singularity:
  image: mnist-0.0.1.sif

tasks:
  download:
    parameters:
      inputs:
        data_config: {type: file, default: data.yaml}
      outputs:
        data_dir: {type: directory, default: data}
        log_dir: {type: directory, default: logs}
  train:
    parameters:
      inputs:
        data_dir: {type: directory, default: data}
        train_config: {type: file, default: train.yaml}
      outputs:
        log_dir: {type: directory, default: logs}
        model_dir: {type: directory, default: model}
```


## Metadata
MLCube configuration can contain metadata about MLCube developers. The following fields are allowed:
 
- `name (type=string)`  MLCube name.
- `description (type=string)`  MLCube description.
- `authors (type=list)`  List of MLCube developers / authors. Each item is a dictionary with the following fields:
  - `name (type=string)`  Author full name.
  - `email (type=string)`  Author email.
  - `org (type=string)`  Author affiliation.


## Resources
The `platform` section (optional) can provide information about resources that MLCubes require. 

!!! warning
    Parameters defined in this section are not supported yet by MLCube runners. 
 
This section is intended to be used by MLCube 
[runners](https://mlcommons.github.io/mlcube/getting-started/concepts/#runner). For instance, cloud runners can use
information about accelerators, disk space and memory to provision appropriate resources. The exact fields of this
section are to be defined.


## Tasks
This `tasks` section provides description of what's implemented in an MLCube. This section is a dictionary that maps
a task name to a task configuration. In the example above, two tasks are defined - `download` and `train`. 

Each task configuration is a dictionary with two parameters:

- `entrypoing (type=string)` Optional task-specific entrypoint (e.g., executable script, for instance, inside an MLCube 
  container). If not present, it is assumed that global entry point is defined (for instance, via Docker's entry point 
  configuration - see [example](https://github.com/mlcommons/mlcube_examples/blob/master/mnist/Dockerfile)).
- `parameters (type=dictionary)` Optional specification of input and output parameters. If present, can contain two
  optional fields - `inputs` and `outputs`. Each field specifies task's input and output parameters. This specification
  is a dictionary mapping from a parameter name to a parameter description. In the above example, the `download` task
  defines one input parameter (`data_config`) and two output parameters (`data_dir` and `log_dir`). Each parameter 
  description is a dictionary with the following fields:
    - `type (type=string)` Specifies parameter type, and must be one of `file` or `directory`.
    - `default (type=string)` Parameter value: path to a directory of path to a file. 
        - Paths can contain `~` (user home directory) and environment variables (e.g., `${HOME}`). MLCube does not 
          encourage the use of environment variables  since this makes MLCube less portable and reproducible. The use 
          of `~` should be OK though.
        - Paths can be absolute or relative. Relative paths are always relative to current  
          [MLCube workspace](https://mlcommons.github.io/mlcube/getting-started/concepts/#workspace) directory. 
          In the example above,  the `data_conig` parameter's default value for the `download` task is a short form of 
          `${workspace}/data.yaml`. 
    - `opts (type=string)` This optional field specifies file or path access options (e.g., mount options for container
      runtimes). Valid values are `rw` (read and write) and `ro` (read only). When parameter is a file, these options 
      are set for a volume associated with the file's parent directory. When read-only option is specified for
      an output parameter, MLCube runner will use it and will log to a log file. When conflicting options are 
      found, MLCube will log a warning message and will use the `rw` option. 


## Examples
More example configurations of MLCubes can be found in the mlcube_examples 
[repository](https://github.com/mlcommons/mlcube_examples). In particular, 
the [getting-started](https://github.com/mlcommons/mlcube_examples/tree/master/getting-started) example shows the use
of the [entrypoint](https://github.com/mlcommons/mlcube_examples/blob/master/getting-started/mlcube/mlcube.yaml) 
specification.
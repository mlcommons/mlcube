# MLCube System Settings
MLCube system settings configure MLCube and MLCube runners at a system level. The term `system level` here implies that
these settings are not tied to particular MLCubes (MLCube compliant ML projects). Instead, these settings are used by
MLCube runners on every machine where MLCube runtime is configured to use these settings.

## Introduction
When MLCube runners run MLCubes, they need to know not only the content of MLCubes (tasks that MLCubes provide), but 
also non-standard or custom settings of a user environment. Effective MLCube configuration that MLCube runners end up
using is constructed by merging configurations from the following sources:

- `System settings` provide non-standard and/or user-specific parameters for MLCube runners. For instance, in system
  settings users can indicate that they are required to use `sudo` to run docker. Or they can configure MLCube SSH or
  GCP (Google Cloud Platform) runners with their credentials to be able to run MLCubes on specific remote servers, 
  either on-prem, or in the cloud.
- `MLCube configuration` provide MLCube-specific configuration, such as implemented tasks and, optionally, specific
  platform (hardware) requirements, for instance, GPU and host memory required to run the tasks. This configuration
  overrides system settings.
- `Command line parameters` that users provide when they run MLCubes. These parameters have the highest priority and 
  override system settings and MLCube configuration.

## Location
MLCube system settings are stored in a YAML file. Default location of this file is `${HOME}/mlcube.yaml`. This file is
created or updated every time users run any of MLCube commands. When users install a new MLCube runner (for instance, 
the singularity runner `pip install mlcube-singularity`), MLCube will update the system settings file with this new 
runner next time MLCube runs. Users can directly modify this file. In addition, MLCube runtime provides `config` 
command (`mlcube config --help`) to perform typical operations, such as creating a new MLCube runner configuration off 
existing one. Users can override the location of this file by defining `MLCUBE_SYSTEM_SETTINGS` environment variable. 

## MLCube System Settings 
The MLCube system settings are stored in a YAML file. This file has the following schema:
```yaml
runners:
  # A dictionary with metadata on installed MLCube runners. This section is updated (if 
  # necessary) every time MLCube runs (this means that this section is not updated once 
  # a new runner is installed). Every key in this dictionary is a runner name (must be 
  # unique across all MLCube runners), and every value is (usually) a dictionary providing 
  # runner metadata. In general, it is runner-specific. This section does not provide a 
  # specific configuration for instances of MLCube runners, and users should not modify 
  # content of this section - it is maintained automatically by MLCube runtime.
  docker:
    # MLCube provides several reference runners including docker and singularity runners. 
    # All reference runners are implemented in Python and are distributed as separate python 
    # packages on pypi (e.g., `pip install mlcube-docker`). All these reference runners use 
    # the same metadata schema. Their metadata is a dictionary with just one field - `pkg`. 
    # Names of MLCube runners in this section are not directly exposed to users via command 
    # line API.
    pkg: mlcube_docker
    # All MLCube reference runners are described with a dictionary with one field (`pkg`) 
    # that points to a Python package name.

platforms:
  # This section (a dictionary) configures instances of MLCube runners. Why there might be 
  # more than one instance of a particular runner? For instance, users might have two Google 
  # Cloud Platform accounts - personal and corporate. Or they might have access to a number 
  # of on-prem compute nodes via ssh, and so they will have respective number of MLCube SSH 
  # runner instances configured here. There is always a default MLCube runner instance that 
  # has the same name as the runner itself (e.g., for Docker runner the name of a default 
  # MLCube docker runner is `docker`). This default section is created automatically by 
  # MLCube runtime if it does not exist.
  # Every MLCube runner has its own schema (see MLCube runners documentation) with its own 
  # unique set of configuration parameters.
  # Names of MLCube runner instances defined here are directly exposed to users via command 
  # line argument `--platform`:
  #    - By default, a default MLCube runner instance is configured with the same name as 
  #      its MLCube runner class name: docker, singularity etc.
  #    - When users configure their own unique MLCube runner instances (either via `mlcube 
  #      config create_platform` command, or manually modifying this file(*)), these instances 
  #      become available to use, i.e., something like is possible:
  #        $ mlcube run --mlcube=. --task=train --platform=my_mlcube_runner_instance_name
  #    (*): To configure a new runner instance manually, duplicate default configuration with 
  #         a new name and change its parameters.
  singularity:
    # This is the example of a default configuration for a MLCube reference singularity runner.
    # This runner instance, as any other instance, defines the `runner` key which servers as 
    # a foreign key to the `runners` section.
    runner: singularity
    # MLCube runner class (defined in `runners` section).
    image: ${singularity.image}
    # Image name, usually defined in MLCube configuration file.
    image_dir: ${runtime.workspace}/.image
    # Default build directory for MLCubes distributed with sources.
    singularity: singularity
    # Singularity executable.
    build_args: --fakeroot
    # Build arguments.
    build_file: Singularity.recipe
    # Default Singularity build file for MLCubes distributed with sources

  singularity-1.5.3:
    # This is an example of another MLCube singularity runner instance. Maybe, a user has 
    # an outdated version that requires sudo and does not support --fakeroot argument.
    # Then, this user use this name on a command line to run MLCubes with singularity runner:
    #        $ mlcube run --mlcube=. --task=train --platform=singularity-1.5.3
    # BTW, users can create this section by running the following command (they need to edit 
    # it manually though anyway):
    #        $ mlcube config create_platform singularity singularity-1.5.3 
    runner: singularity
    image: ${singularity.image}
    image_dir: ${runtime.workspace}/.image
    singularity: sudo singularity
    build_args:
    build_file: Singularity.recipe
```
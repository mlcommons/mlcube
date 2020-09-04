# SSH Runner
SSH runner uses other runners to run MLBoxes on remote hosts. It uses `ssh` and `rsync` internally. It supports two
mandatory commands - `configure` and `run` with standard arguments - `mlbox`, `platform` and `task`. SSH platform
configuration is used to configure SSH runner.

> This runner is being actively developed and not features described on this page  may be supported.


## Platform Configuration File
SSH platform configuration file is a YAML file. The configuration file for the reference MNIST MLBox is the following:
```yaml
host: REMOTE_HOST     # Remote host IP address.
user: USER            # User name, assuming passwordless authentication using keys has been set up.
platform: docker.yaml # How to run MLBox
env:                  # This is for syncing MLBox library itself (library, runners etc.)
    path: ./mlbox     # Path on a remote node, this is the default value. Relative paths are relative to use home dir.
    sync: true
    interpreter:      # Environment for running runners, mlbox can have its own interpreter. Dependencies must be inst.
        type: system
        python: python3.6   # Can also be an absolute path to user python environment (virtualenv, conda etc.)
    variables: {}    # Environmental variables (will be used by docker build/run), remove '{}' if variables present.
        # http_proxy:
        # https_proxy:
mlbox:                # Remote location of the MLBox to run
    path:             # Null, the path will be set to ./.mlbox/mlboxes/mnist-${version}
    sync: true
```

SSH runner uses IP or name of a remote host (`host`) and ssh tool to login and execute shell commands on remote hosts. 
It uses user name (`user`) for authentication. If passwordless login is not configured, SSH runner asks for password
many times during configure and run phases.  
  
SSH runner depends on other runners to run MLBoxes. The `platform` field specifies what runner should be used on a 
remote host. This is a file name relative to `{MLBOX_ROOT}/platforms`.  

In current implementation, SSH runner synchronizes both MLBox library and MLBox workload between local and remote hosts.
This is optional.


## Build command
During the `build` phase, the following steps are performed.  
1. If MLBox library (source tree) needs to be synchronized, SSH runner:  
   - Uses `ssh` to create root directory for the MLBox library.  
   - `Uses` `rsync` to synchronize the following MLBox directories: `mlcommons_box` and `runners`.  
2. If MLBox workload needs to be synchronized, SSH runner:  
   - Uses `ssh` to create root directory for the MLBox workload.  
   - `Uses` `rsync` to synchronize the entire content of the MLBox workload.  
3. The only supported remote python environment is the `system`, and SSH runner assumes that all dependencies have been
   installed. Two required python packages that are not common are `typer` and `mlspeclib`.  
4. SSH runner uses `platform` file and runs standard `configure` command on a remote host. Only reference Docker and
   Singularity runners are supported now.  


## Run command
During the run phase, the SSH runner performs the following steps:  
1. It uses `ssh` to run standard `run` command on a remote host.  
2. It uses `rsync` to synchronize back the content of the `{MLBOX_ROOT}/workspace` directory.   

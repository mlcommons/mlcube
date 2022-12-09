# SSH Runner

!!! warning
    Work in progress. Some functionality described below may not be available.

SSH runner uses other runners to run MLCube cubes on remote hosts. It uses `ssh` and `rsync` internally. It
supports two mandatory commands - `configure` and `run` with standard arguments - `mlcube`, `platform` and `task`. Users 
can configure SSH runner in system setting file, and override parameters on a command line.

## Configuration parameters
```yaml
# Remote host name or IP address
host: ''
# Platform (runner) to use on remote host
platform: ''
# Root path for MLCubes on remote host
remote_root: ''
# Remote python interpreter. It's a dictionary. 
# - Must contain:
#   - `type`: interpreter type (system, virtualenv)
# - When type is system (system-wide interpreter), additional parameters must be:
#   - `python`: python executable, maybe full path or just `python`.
#   - `requirements`: is a whitespace-separated list of python dependencies.
# - When type is virtualenv (python environment created with virtualenv tool), 
#   additional parameters must be:
#   - `python`: python executable
#   - `requirements`: is a whitespace-separated list of python dependencies.
#   - `location`: path where virtual environment must be created.
#   - `name`: name of the virtual environment.
interpreter: {}          
# Authentication on remote host. It's a dictionary that contain the following fields:
#   - `identify_file`: if present, will be used as part of the connection 
#     string ('-i {identity_file}')
#   - `user`: username for the remote host, will be used as '{user}@{host}'
authentication: {}
```

SSH runner uses IP or name of a remote host (`host`) and ssh tool to log in and execute shell commands on remote hosts. 
If passwordless login is not configured, SSH runner asks for password many times during configure and run phases.  

  
## Configuring MLCubes

!!! attention
    This runner must be configured by users explicitly: `mlcube configure --mlcube=. --platform=ssh`

During the `configure` phase, the following steps are performed.

- Based upon configuration, SSH runner creates and/or configures python on a remote host using `ssh`. This includes
  execution of such commands as `virtualenv -p ...` and/or `source ... && pip install ...` on a remote host.
- SSH runner copies mlcube directory to a remote host.
- SSH runner runs another runner specified in a platform configuration file on a remote host to configure it. 


## Running MLCubes
During the run phase, the SSH runner performs the following steps:

- It uses `ssh` to run standard `run` command on a remote host.  
- It uses `rsync` to synchronize back the content of the `{MLCUBE_ROOT}/workspace` directory.   

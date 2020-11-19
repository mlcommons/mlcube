# SSH Runner
SSH runner uses other runners to run MLCube cubes on remote hosts. It uses `ssh` and `rsync` internally. It
supports two mandatory commands - `configure` and `run` with standard arguments - `mlcube`, `platform` and `task`. SSH
platform configuration is used to configure SSH runner.

> This runner is being actively developed and not all features described on this page may be supported.


## Platform Configuration File
SSH platform configuration file is a YAML file. The configuration file for the reference MNIST cube is the following:
```yaml
# Possible values are hostname or IP address. It can also be a host alias if there is a corresponding section
# exists in ~/.ssh/config. The hostname should be possible to use with tools like ssh, rsync and scp.
host: REMOTE_HOST


# Authentication section is optional, and can be null, empty or non-empty dictionary. If value is null or empty 
# string/dict, it is assumed the authentication is not required, or is configured in user environment 
# (e.g. ~/.ssh/config). SSH runner will not provide any additional information on a command line for ssh, rsync or scp.
# If the value is a dictionary, optional fields that SSH runner recognizes are user name on a remote host (user) and 
# path to a user private key file (identity_file). If all fields are present, the following connection string is used 
# by the SSH runner: `-i $identity_file $user@$host`.
authentication:
    user: USER
    identity_file: /opt/mlcube/ssh/gcp_identity


# The platform field points to a platform configuration to be used on a remote host. This file must be located inside 
# $mlcube_root/platforms directory. The idea is that the SSH runner delivers an MLCube to a remote host and then use 
# another MLCube runner such as Docker or Singularity runner to run that MLCube there.
platform: docker.yaml


# The interpreter section defines python interpreter on a remote host to use to run other runners there. This is not 
# environment for MLCubes, this is environment for runners to run MLCubes. Two options are supported - `system` and 
# `virtualenv` interpreters.

# The system interpreter is a python already available on a remote host. It can be just an executable (python, 
# python3.8) or a full path to a user existing environment. Three fields should be provided: type (system in this case), 
# python executable, possibly, with fully specified path, and dependencies in the form of a string (requirements).
interpreter:
    type: "system"
    python: "python3.6"
    requirements: "mlcube-docker==0.2.2"

# The virtualenv interpreter does not have to exist. SSH runner can create this one. This interpreter has the same 
# fields with two additional ones - location (base path for a python environment) and name (basically, a folder name 
# inside the location path).
# interpreter:
#     type: "virtualenv"
#     python: "python3.6"
#     requirements: "mlcube-docker==0.2.1"
#     location: "${HOME}/mlcube/environments"
#     name: "mlcube-docker-0.2.1"
```

SSH runner uses IP or name of a remote host (`host`) and ssh tool to login and execute shell commands on remote hosts. 
If passwordless login is not configured, SSH runner asks for password many times during configure and run phases.  
  
SSH runner depends on other runners to run MLCube cubes. The `platform` field specifies what runner should be
used on a remote host. This is a file name located in `{MLCUBE_ROOT}/platforms`.  

In current implementation, SSH runner synchronizes only an mlcube workload between local and remote hosts. Runners
are assumed to be either available on remote hosts or specified as package dependencies in python interpreter 
configuration section. 


## Configure command
During the `build` phase, the following steps are performed.
1. Based upon configuration, SSH runner creates and/or configures python on a remote host using `ssh`. This includes
   execution of such commands as `virtualenv -p ...` and/or `source ... && pip install ...` on a remote host. Default
   path for a python environment on a remote host is `${HOME}/mlcube/environments/`.   
2. SSH runner copies mlcube directory to a remote host. Default path on a remote host is `${HOME}/mlcube/cubes/`.
3. SSH runner runs another runner specified in a platform configuration file on a remote host to configure it. 


## Run command
During the run phase, the SSH runner performs the following steps:  
1. It uses `ssh` to run standard `run` command on a remote host.  
2. It uses `rsync` to synchronize back the content of the `{MLCUBE_ROOT}/workspace` directory.   

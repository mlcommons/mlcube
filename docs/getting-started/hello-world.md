# Hello World
Hello World MLCube is an example of a Docker-based cube.  


## QuickStart
Get started with MLCube Docker runner with below commands.   

### Create python environment
```
virtualenv -p python3.6 ./env && source ./env/bin/activate
```

### Install MLCube Docker runner
```
pip install mlcube-docker      # Install.
mlcube config --get runners    # Check it was installed.
mlcube config --list           # Show system settings for local MLCube runners.
```
Depending on how your local system is configured, it may be required to change the following settings:
- `platforms.docker.docker` (string): A docker executable. Examples are `docker`, `nvidia-docker`, `sudo docker`,
  `podman` etc.
- `platforms.docker.env_args` (dictionary) and `platforms.docker.build_args` (dictionary). Environmental variables
  for docker run and build phases. Http and https proxy settings can be configured here.
A custom configuration could look like:
```yaml
platforms:
  docker:
    docker: sudo docker
    env_args:
      http_proxy: http://proxy.company.com:8088
      https_proxy: https://proxy.company.com.net:8088
    build_args:
      http_proxy: http://proxy.company.com:8088
      https_proxy: https://proxy.company.com:8088
```

### Run Hello World MLCube example
```
# The hello_world MLCube is part of the mlcube_examples GitHub repository.
git clone https://github.com/mlcommons/mlcube_examples.git && cd ./mlcube_examples/hello_world

# Run Hello World MLCube on a local machine with Docker runner.
# Show available tasks
mlcube describe

# Run Hello World example tasks. Very first run can take some time to download (or build)
# the MLCube docker image.
mlcube run --mlcube=. --task=hello --platform=docker   # No output expected.
mlcube run --mlcube=. --task=bye --platform=docker     # No output expected.
cat ./workspace/chats/chat_with_alice.txt              # You should some log lines in this file.
cat 
```
If above mlcube runs fail (with the error message saying there is no docker image available, try to change the system
settings file by changing `platforms.docker.build_strategy` to `auto`.

## Setup Docker
MLCube Docker runner used Docker runtime, and they must be available in the system.
Installation guides for various operating systems can be found [here](https://docs.docker.com/engine/install/). This
example was tested on a system where users are in the docker group and run docker without `sudo`. To add yourself to a
docker group, run the following:
```
sudo groupadd docker             # Add the docker group if it doesn't already exist.
sudo gpasswd -a ${USER} docker   # Add the connected user "${USER}" to the docker group. Change 
                                 # the user name to match your preferred user.
sudo service docker restart      # Restart the Docker daemon.
newgrp docker                    # Either do a `newgrp docker` or log out/in to activate the 
                                 # changes to groups.
```

## Configuring Hello World MLCube
Cubes need to be configured before they can run. MLCube runners do that automatically, and users do not need to run
the configure step manually. If for some reason this needs to be done, for instance, to pre-build or pull docker images
(if these processes take too much time), MLCube runtime implements `configure` command. The Hello World cube is a 
Docker-based cube, and users can configure the MLCube by running the following command:
```
mlcube configure --mlcube=. --platform=docker
```
The Docker runner will build or will pull the docker image for the Hello World cube. As it is mentioned above, this step
is optional and is only required when MLCubes need to be rebuilt. This can happen when users change implementation files
and want to re-package their ML project into MLCube. In other situations, MLCube runners can auto-detect if `configure`
command needs to be run before running MLCube tasks.


## Running Hello World MLCube 
In order to run the Hello World cube, users need to provide the path to the root directory of the cube, platform
and task names. Run the following two commands one at a time:
```
cat ./workspace/chats/chat_with_alice.txt

mlcube run --mlcube=. --platform=docker --task=hello
cat ./workspace/chats/chat_with_alice.txt
 
mlcube run --mlcube=. --platform=docker --task=bye
cat ./workspace/chats/chat_with_alice.txt
```
Hello World creates a file `workspace/chats/chat_with_alice.txt` that contains the following:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
```

 
## Modifying MLCube tasks


### Override parameters on a command line 
One way to change the parameters of MLCubes is to override them on a command line. Create a new file
`workspace/names/mary.txt` with the following content: `Mary`. Then, run the following:
```shell
mlcube run --mlcube=. --platform=docker --task=hello name=names/mary.txt chat=chats/chat_with_mary.txt
cat workspace/chats/chat_with_mary.txt

mlcube run --mlcube=. --platform=docker --task=bye name=names/mary.txt chat=chats/chat_with_mary.txt
cat workspace/chats/chat_with_mary.txt
```
You should observe the output similar to this one:
```shell
[2021-09-30 18:49:46.896509]  Hi, Mary! Nice to meet you.
[2021-09-30 18:49:56.883266]  Bye, Mary! It was great talking to you.
```


### Providing a better greeting message
Because how Hello World cube was implemented, the greeting message is always the following: `Nice to meet you.`. We will
update the implementation so that if this is not the first time Alice says `hello`, the  MLCube will respond: `Nice to 
see you again.`.

Modify the file `hello_world.py`. Update the function named `get_greeting_message` on line 14. It should have the
following implementation:
```python
import os

def get_greeting_message(chat_file: str) -> str:
    return "Nice to meet you." if not os.path.exists(chat_file) else "Nice to see you again."
```
Reconfigure the MLCube:
```
mlcube configure --mlcube=. --platform=docker
```
And run two `hello` tasks again:
```shell
rm ./workspace/chats/chat_with_alice.txt

mlcube run --mlcube=. --platform=docker --task=hello,bye
mlcube run --mlcube=. --platform=docker --task=hello,bye

cat ./workspace/chats/chat_with_alice.txt
```
The MLCube recognized it was not the first time it talked to Alice, and changed the greeting:
```
[2021-09-30 20:04:36.977032]  Hi, Alice! Nice to meet you.
[2021-09-30 20:04:40.851157]  Bye, Alice! It was great talking to you.
[2021-09-30 20:04:47.228554]  Hi, Alice! Nice to see you again.
[2021-09-30 20:04:51.031609]  Bye, Alice! It was great talking to you.
```

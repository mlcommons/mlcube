# Hello World
## Docker runtime
Hello World MLBox is an example of a docker-based MLBox, and docker runtime must be installed in a system. Installation 
guides for various operating systems can be found [here](https://docs.docker.com/engine/install/). This example was 
tested on a system where users are in the docker group and run docker without `sudo`. To add yourself to a docker group, 
run the following:
```
sudo groupadd docker             # Add the docker group if it doesn't already exist.
sudo gpasswd -a ${USER} docker   # Add the connected user "${USER}" to the docker group. Change the user name to match your preferred user.
sudo service docker restart      # Restart the Docker daemon.
newgrp docker                    # Either do aÂ newgrp dockerÂ or log out/in to activate the changes to groups.
```

 
## Host python environment
Hello World is an example of a simple python program distributed as an MLBox. This tutorial covers the case when MLBox 
library and Hello World MLBox are cloned from the GitHub repository:
```
git clone https://github.com/mlperf/mlbox ./mlbox
cd ./mlbox
```

Python >= 3.6 is required together with runners' python dependencies:
```
virtualenv -p python3.8 ./env
source ./env/bin/activate
pip install typer mlspeclib
export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/mlbox_singularity_run:$(pwd)/runners/mlbox_docker_run
```

Optionally, setup host environment by providing the correct `http_proxy` and `https_proxy` environmental variables.
```
export http_proxy=...
export https_proxy=...
```

## Configuring MLBox
MLBoxes need to be configured before they can run. To do so, users need to run the MLBox runner with `configure` 
command providing path to a MLBox root directory and path to a platform configuration file. Hello World MLBox is a 
docker-based MLBox, so users provide path to a Docker platform configuration file that sets a number of parameters,
including docker image name:
```
python -m mlbox_docker_run configure --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml
```
Docker runner will build a docker image for the Hello World MLBox.


## Running MLBox
In order to run MLBox, users need to provide the path to the root directory of the MLBox, platform configuration file
and path to a task definition file. Run the following two commands one at a time:
```
python -m mlbox_docker_run run --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml --task=examples/hello_world/run/alice/hello.yaml
python -m mlbox_docker_run run --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml --task=examples/hello_world/run/alice/bye.yaml
```
MLBox creates a file `examples/hello_world/workspace/chats/chat_with_alice.txt` that contains the following:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
```
 
## Modifying MLBox

### Adding new user 
Create a new file `examples/hello_world/workspace/names/donald.txt` with the following content: `Donald`.

Create a new file `examples/hello_world/run/donald/hello.yaml` with the following content:
```yaml
schema_type: mlbox_invoke
schema_version: 1.0.0

task_name: hello

input_binding:
        name: $WORKSPACE/names/donald.txt

output_binding:
        chat: $WORKSPACE/chats/chat_with_donald.txt
```
  
Create a new file `examples/hello_world/run/donald/bye.yaml` with the following content:
```yaml
schema_type: mlbox_invoke
schema_version: 1.0.0

task_name: bye

input_binding:
        name: $WORKSPACE/names/donald.txt

output_binding:
        chat: $WORKSPACE/chats/chat_with_donald.txt
```

Run the following two commands one at a time:
```
python -m mlbox_docker_run run --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml --task=examples/hello_world/run/donald/hello.yaml
python -m mlbox_docker_run run --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml --task=examples/hello_world/run/donald/bye.yaml
```
MLBox creates a file `examples/hello_world/workspace/chats/chat_with_donald.txt` that contains the following:
```
[2020-09-03 09:23:09.569558]  Hi, Donald! Nice to meet you.
[2020-09-03 09:23:20.076845]  Bye, Donald! It was great talking to you.
```


### Providing a better greeting message
The way how Hello World MLBox application was implemented, the greeting message is always the following: 
`Nice to meet you.`. We will update the implementation so that if this is not the first time Alice says `hello`, the 
MLBox will respond: `Nice to see you again.`.

Modify the file `examples/hello_world/build/hello_world.py`. Update the function named `get_greeting_message` at line
14. It should have the following implementation:
```python
def get_greeting_message(chat_file: str) -> str:
    return "Nice to meet you." if not os.path.exists(chat_file) else "Nice to see you again."
```

Since we updated a file in `build` subdirectory, we need to re-configure the MLBox:
```
python -m mlbox_docker_run configure --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml
```
Now, run two `hello` task again:
```
python -m mlbox_docker_run run --mlbox=examples/hello_world --platform=examples/hello_world/platform/docker.yaml --task=examples/hello_world/run/alice/hello.yaml
```
The MLBox recognized it was not the first time it talked to Alice, and changed the greeting:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
[2020-09-03 09:32:41.369367]  Hi, Alice! Nice to see you again.
```

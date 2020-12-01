# Hello World
Hello World MLCube is an example of a docker-based cube.  


## QuickStart
Get started with MLCube Docker runner with below commands.   

### Create python environment
```
virtualenv -p python3 ./env && source ./env/bin/activate
```

### Install MLCube Docker runner
```
pip install mlcube-docker
```

### Run Hello World MLCube example
```
# hello_world MLCube is present in mlcube_examples repo.
git clone https://github.com/mlcommons/mlcube_examples.git && cd ./mlcube_examples/hello_world

Run Hello World MLCube on a local machine with Docker runner
# Configure Hello World MLCube
mlcube_docker configure --mlcube=. --platform=platforms/docker.yaml

# Run Hello World training tasks: download data and train the model
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/alice/hello.yaml
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/alice/bye.yaml
```

## Setup Docker
MLCube Docker runner used Docker runtime and they must be available in the system.
Installation guides for various operating systems can be found [here](https://docs.docker.com/engine/install/). This
example was tested on a system where users are in the docker group and run docker without `sudo`. To add yourself to a
docker group, run the following:
```
sudo groupadd docker             # Add the docker group if it doesn't already exist.
sudo gpasswd -a ${USER} docker   # Add the connected user "${USER}" to the docker group. Change the user name to match your preferred user.
sudo service docker restart      # Restart the Docker daemon.
newgrp docker                    # Either do a `newgrp docker` or log out/in to activate the changes to groups.
```

## Configuring Hello World MLCube
Cubes need to be configured before they can run. To do so, users need to run a MLCube runner with `configure` 
command providing path to a cube root directory and path to a platform configuration file. The Hello World cube is a 
docker-based cube, so users provide path to a MLCube Docker platform configuration file that sets a number of
parameters, including docker image name:
```
mlcube_docker configure --mlcube=. --platform=platforms/docker.yaml
```
The Docker runner will build a docker image for the Hello World cube. In general, this step is optional and is only
required when MLCube needs to be rebuild. This can happen when users change implementation files and want to
re-package their ML project into MLCube. In other situations, MLCube runners can auto-detect if
`configure` command needs to be run before running a MLCube task.


## Running Hello World MLCube 
In order to run the Hello World cube, users need to provide the path to the root directory of the cube, platform
configuration file and path to a task definition file. Run the following two commands one at a time:
```
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/alice/hello.yaml
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/alice/bye.yaml
```
Hello World creates a file `workspace/chats/chat_with_alice.txt` that contains the following:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
```
 
## Modifying MLCube tasks

### Adding new user 
Create a new file `workspace/names/foo.txt` with the following content: `Foo`.

Create a new file `run/foo/hello.yaml` with the following content:
```yaml
schema_type: mlcube_invoke
schema_version: 1.0.0

task_name: hello

input_binding:
        name: $WORKSPACE/names/foo.txt

output_binding:
        chat: $WORKSPACE/chats/chat_with_foo.txt
```
  
Create a new file `run/foo/bye.yaml` with the following content:
```yaml
schema_type: mlcube_invoke
schema_version: 1.0.0

task_name: bye

input_binding:
        name: $WORKSPACE/names/foo.txt

output_binding:
        chat: $WORKSPACE/chats/chat_with_foo.txt
```

Run the following two commands one at a time:
```
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/foo/hello.yaml
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/foo/bye.yaml
```
The Hello World cube creates a file `workspace/chats/chat_with_foo.txt` that contains the
following:
```
[2020-09-03 09:23:09.569558]  Hi, Foo! Nice to meet you.
[2020-09-03 09:23:20.076845]  Bye, Foo! It was great talking to you.
```


### Providing a better greeting message
Because how Hello World cube was implemented, the greeting message is always the following: `Nice to meet you.`. We will
update the implementation so that if this is not the first time Alice says `hello`, the  MLCube will respond: `Nice to 
see you again.`.

Modify the file `build/hello_world.py`. Update the function named `get_greeting_message` on line
14. It should have the following implementation:
```python
def get_greeting_message(chat_file: str) -> str:
    return "Nice to meet you." if not os.path.exists(chat_file) else "Nice to see you again."
```

Since we updated a file in the `build` subdirectory, we need to re-configure the Hello World cube:
```
mlcube_docker configure --mlcube=. --platform=platforms/docker.yaml
```
Now, run two `hello` task again:
```
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/alice/hello.yaml
```
The MLCube recognized it was not the first time it talked to Alice, and changed the greeting:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
[2020-09-03 09:32:41.369367]  Hi, Alice! Nice to see you again.
```

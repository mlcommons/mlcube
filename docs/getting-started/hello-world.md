# Hello World
## Docker runtime
Hello World MLCommons-Box is an example of a docker-based box. Docker runtime must be installed in a system.
Installation guides for various operating systems can be found [here](https://docs.docker.com/engine/install/). This
example was tested on a system where users are in the docker group and run docker without `sudo`. To add yourself to a
docker group, run the following:
```
sudo groupadd docker             # Add the docker group if it doesn't already exist.
sudo gpasswd -a ${USER} docker   # Add the connected user "${USER}" to the docker group. Change the user name to match your preferred user.
sudo service docker restart      # Restart the Docker daemon.
newgrp docker                    # Either do a `newgrp docker` or log out/in to activate the changes to groups.
```

 
## Host python environment
Hello World is an example of a simple python program distributed as an MLCommons-Box docker-based box. Follow the steps
outlined in the `Introduction` section to create your Python virtual environment, download example MLCommons-Box boxes
and install standard MLCommons-Box runners. Go to the folder containing MLCommons-Box example boxes and change directory
to Hello World Box:
```
cd ./hello_world
```


## Configuring Hello World MLCommons-Box
Boxes need to be configured before they can run. To do so, users need to run a MLCommons-Box runner with `configure` 
command providing path to a box root directory and path to a platform configuration file. The Hello World box is a 
docker-based box, so users provide path to a MLCommons-Box Docker platform configuration file that sets a number of
parameters, including docker image name:
```
mlcommons_box_docker configure --mlbox=. --platform=platforms/docker.yaml
```
The Docker runner will build a docker image for the Hello World box. In general, this step is optional and is only
required when MLCommons-Box needs to be rebuild. This can happen when users change implementation files and want to
re-package their ML project into MLCommons-Box. In other situations, MLCommons-Box runners can auto-detect if
`configure` command needs to be run before running a MLBox task.


## Running Hello World MLCommons-Box 
In order to run the Hello World box, users need to provide the path to the root directory of the box, platform
configuration file and path to a task definition file. Run the following two commands one at a time:
```
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/alice/hello.yaml
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/alice/bye.yaml
```
Hello World creates a file `workspace/chats/chat_with_alice.txt` that contains the following:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
```
 
## Modifying MLCommons-Box

### Adding new user 
Create a new file `workspace/names/donald.txt` with the following content: `Donald`.

Create a new file `run/donald/hello.yaml` with the following content:
```yaml
schema_type: mlbox_invoke
schema_version: 1.0.0

task_name: hello

input_binding:
        name: $WORKSPACE/names/donald.txt

output_binding:
        chat: $WORKSPACE/chats/chat_with_donald.txt
```
  
Create a new file `run/donald/bye.yaml` with the following content:
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
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/donald/hello.yaml
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/donald/bye.yaml
```
The Hello World box creates a file `workspace/chats/chat_with_donald.txt` that contains the
following:
```
[2020-09-03 09:23:09.569558]  Hi, Donald! Nice to meet you.
[2020-09-03 09:23:20.076845]  Bye, Donald! It was great talking to you.
```


### Providing a better greeting message
Because how Hello World box was implemented, the greeting message is always the following: `Nice to meet you.`. We will
update the implementation so that if this is not the first time Alice says `hello`, the  MLBox will respond: `Nice to 
see you again.`.

Modify the file `build/hello_world.py`. Update the function named `get_greeting_message` on line
14. It should have the following implementation:
```python
def get_greeting_message(chat_file: str) -> str:
    return "Nice to meet you." if not os.path.exists(chat_file) else "Nice to see you again."
```

Since we updated a file in the `build` subdirectory, we need to re-configure the Hello World box:
```
mlcommons_box_docker configure --mlbox=. --platform=platforms/docker.yaml
```
Now, run two `hello` task again:
```
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/alice/hello.yaml
```
The MLBox recognized it was not the first time it talked to Alice, and changed the greeting:
```
[2020-09-03 09:13:14.236945]  Hi, Alice! Nice to meet you.
[2020-09-03 09:13:20.749831]  Bye, Alice! It was great talking to you.
[2020-09-03 09:32:41.369367]  Hi, Alice! Nice to see you again.
```

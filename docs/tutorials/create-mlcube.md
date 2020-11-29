# Tutorial Create an MLCube 
Interested in getting started with MLCube? Follow the instructions in this tutorial.    
## Step 1: SETUP   
Get MLCube, MLCube examples and MLCube Templates, and CREATE a Python environment.
```
# You can clone the mlcube examples and templates from GtiHub
git clone https://github.com/mlcommons/mlcube_examples
git clone --branch feature/mlbox-template https://github.com/sergey-serebryakov/mlbox.git 
# Create a python environment
virtualenv -p python3 ./env && source ./env/bin/activate
# Install mlcube, mlcube-docker  
pip install mlcube mlcube-docker cookiecutter 
```

## Step 2: CONFIGURE MLCUBE USING THE TEMPLATE FILES 
Let's use the 'matmult' example, that we downloaded in the previous step, to illustrate how to make an MLCube. Matmul is a simple matrix multiply example written in Python with TensorFlow. 
When you create an MLCube for your own model you will use your own code, data and dockerfile.
 
```
cd mlcube_examples
# create a directory for your new mlcube
mkdir my_mlcube
# copy the templates for an MLCube
cp -R ../mlbox/examples/template/. my_mlcube/. 
# copy the matmul.py,Dockerfile and requirements.txt to your my_mlcube/build directory
cp -R  matmul/build  my_mlcube
# copy input file for matmul to workspace directory
cp -R  matmul/workspace  my_mlcube

```

Edit the template files 
 
Start by editing the mlcube.yml file.  Replace 'mlcube_name' with your own MLCube name and enter your name as author. 
```
cd ./my_mlcube
# NOTE: The following line will not be necessary once all instances of "mlbox" are replaced by "mlcube" in the template branch 
cp mlbox.yaml mlcube.yaml
```

The lines you need to edit are shown in **bold** in the mlcube.yaml file shown here:
<pre><code> 
# This YAML file marks a directory to be an MLCube directory. When running MLCubes with runners, MLCube path is
# specified using `--mlcube` runner command line argument.
# The most important parameters that are defined here are (1) name, (2) author and (3) list of MLCube tasks.
schema_version: 1.0.0
schema_type: mlcube_root

# MLCube name (string). Replace it with your MLCube name (e.g. "mlcube_matmul" as shown here).
name: <strong>mlcube_matmul</strong>
# MLCube author (string). Replace it with your MLBox name (e.g. "MLPerf Best Practices Working Group").
author: <strong>MLPerf Best Practices Working Group</strong>

version: 0.1.0
mlcube_spec_version: 0.1.0

# List of MLCube tasks supported by this MLBox (list of strings). Every task:
#    - Has a unique name (e.g. "download").
#    - Is defined in a YAML file in the `tasks` sub-folder (e.g. "tasks/download.yaml").
#    - Task name is passed to an MLBox implementation file as the first argument (e.g. "python mnist.py download ...").
# Every task is described by lists of input and output parameters. Every parameter is a file system path (directory or
# file) characterized by two fields - name and value.
# By default, if a file system path is a relative path (i.e. does not start with `/`), it is considered to be relative
# to the `workspace` sub-folder.
# Once all tasks are listed below, create a YAML file for each task in the 'tasks' sub-folder and change them
# appropriately.
# NEXT: study `tasks/task_name.yaml`, note: in the case of matmul we only need one task.
tasks:
<strong>  - tasks/matmul.yaml</strong>
  # - 'tasks/download.yaml'
  # - 'tasks/train.yaml'

</code></pre>



Now we will edit file ./my_mlcube/tasks/task_name.yaml and save it to file  matmul.yaml in the 'tasks' directory 
```
cd ./tasks
```
The lines you need to edit are shown in **bold** in the task_name.yaml file shown here:
<sub><sup><span style="color:blue">After editing task_name.yml save the file to matmul.yaml.</span></sup></sub>   
<pre><code> 
# This YAML file defines the task that this MLCube supports. A task is a piece of functionality that MLCube can run. Task
# examples are `download data`, `pre-process data`, `train a model`, `test a model` etc. MLCube runtime invokes MLCube
# entry point and provides (1) task name as the first argument, (2) task input/output parameters (--name=value) in no
# particular order. Inputs, outputs or both can be empty lists. For instance, when MLCube runtime runs an MLCube task:
#            python my_mlcube_entry_script.py download --data_dir=DATA_DIR_PATH --log_dir=LOG_DIR_PATH
#    - `download` is the task name.
#    - `data_dir` is the output parameter with value equal to DATA_DIR_PATH.
#    - `log_dir` is the output parameter with value equal to LOG_DIR_PATH.
# This file only defines parameters, and does not provide parameter values. This is internal MLCube file and is not
# exposed to users via command line interface.
schema_version: 1.0.0
schema_type: mlcube_task

# List of input parameters (list of dictionaries).
inputs:
   <strong> - name: parameters_file
      type: file</strong> 

# List of output parameters (list of dictionaries). Every parameter is a dictionary with two mandatory fields - `name`
# and `type`. The `name` must have value that can be used as a command line parameter name (--data_dir, --log_dir). The
# `type` is a categorical parameter that can be either `directory` or `file`. Every intput/output parameter is always
# a file system path.
# Only parameters with their types are defined in this file. Run configurations defined in the `run` sub-folder
# associate parameter names and their values. There can be multiple run configurations for one task. One example is
# 1-GPU and 8-GPU training configuration for some `train` task.
# NEXT: study `run/task_name.yaml`.
outputs:
   <strong> - name: output_file</strong> 
      <strong>type: file</strong> 

</code></pre>
Now we will edit file ./my_mlcube/run/docker.yaml and save it to file matmul.yaml in the run directory 
```
cd ../run
```

The lines you need to edit are shown in **bold** in the task_name.yaml file shown here:
<pre><code> 
# A run configuration assigns values to task parameters. Since there can be multiple run configurations for one
# task (i.e., 1-GPU and 8-GPU training), run configuration files do not necessarily have to have the same name as their
# tasks. Three sections need to be updated in this file - `task_name`, `input_binding` and `output_binding`.
# Users use task configuration files to ask MLCube runtime run specific task using `--task` command line argument.
schema_type: mlcube_invoke
schema_version: 1.0.0

# Name of a task.
# task_name: task_name
task_name: <strong>matmul</strong> 

# Dictionary of input bindings (dictionary mapping strings to strings). Parameters must correspond to those in task
# file (`inputs` section). If not parameters are provided, the binding section must be an empty dictionary.
input_binding:
        <strong>parameters_file: $WORKSPACE/shapes.yaml</strong> 

# Dictionary of output bindings (dictionary mapping strings to strings). Parameters must correspond to those in task
# file (`outputs` section). Every parameter is a file system path (directory or a file name). Paths can be absolute
# (starting with `/`) or relative. Relative paths are assumed to be relative to MLCube `workspace` directory.
# Alternatively, a special variable `$WORKSPACE` can be used to explicitly refer to the MLCube `workspace` directory.
# MLCube root directory (`--mlcube`) and run configuration file (`--task`) define MLCube task to run. One step left is
# to specify where MLCube runs - on a local machine, remote machine in the cloud etc. This is done by providing platform
# configuration files located in the MLCube `platforms` sub-folder.
# NEXT: study `platforms/docker.yaml`.
output_binding:
        <strong>output_file: $WORKSPACE/matmul_output.txt</strong> 

</code></pre>




Now we will edit file ./my_mlcube/platforms/docker.yaml 

```
cd ../platforms
```
Edit the docker image name in docker.yaml.  Change "image: "mlperf/mlbox_mnist:v1.0" to "mlperf/mlcube_matmul:v1.0"
<pre><code> 
# Platform configuration files define where and how runners run MLBoxes. This configuration file defines a Docker
# runtime for MLBoxes. One field need to be updated here - `container.image`. This platform file defines local docker
# execution environment.
# MLCommons-Box Docker runner uses image name to either `pull` or `build` a docker image. The rule is the following:
#   - If the following file exists (`build/Dockerfile`), Docker image will be built.
#   - Else, docker runner will pull a docker image with the specified name.
# Users provide platform files using `--platform` command line argument.
schema_type: mlcommons_box_platform
schema_version: 0.1.0

platform:
  name: "docker"
  version: ">=18.01"
container:   
<strong>   image: "mlperf/mlcube_matmul:v1.0"</strong> 
</code></pre>

##Step 3. DEFINE A CONTAINER FOR YOUR MODEL WITH A DOCKERFILE
You will need a docker image to create an MLCube.  We will use the Dockerfile for 'matmul' to create a docker container image:   
<sub><sup><span style="color:blue">Note: the last line of the Dockerfile must be    
"ENTRYPOINT ["python3", "/workspace/your_mlcube_name.py"]" as shown below.</span></sup></sub> 

Now we will edit the my_mlcube/build/Dockerfile
```
cd ../build 
```
<pre><code> 
# Sample Dockerfile for matmul (Matrix Multiply)
FROM ubuntu:18.04
MAINTAINER MLPerf MLBox Working Group

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            software-properties-common \
            python3-dev \
            curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

<strong>COPY matmul.py /workspace/matmul.py</strong>

<strong>ENTRYPOINT ["python3", "/workspace/matmul.py"]</strong>
</code></pre>
## Step 3: BUILD THE DOCKER IMAGE
Edit the mlcube.yaml file setting the name of your MLCube, the author and the tasks ("download", "train", etc)
```
# After you have created a repository on https://hub.docker.com or another public repository 
#docker build --tag matmul:1.0 .
#docker push yourusername/matmul 
cd ..
mlcube_docker configure --mlcube=. --platform=platforms/docker.yaml
```
## Step 4: TEST YOUR MLCUBE
```
mlcube_docker run --mlcube=. --platform=platforms/docker.yaml --task=run/matmul.yaml
ls ./workspace
cat ./workspace/matmul_output.txt
```

# MNIST
The [MNIST dataset](http://yann.lecun.com/exdb/mnist/) is a collection of 60,000 handwritten digits widely used for
training statistical, Machine Learning (ML) and Deep Learning (DL) models. The MNIST MLCommons-Box example demonstrates
how data scientists, ML and DL researchers and developers can distribute their ML projects (including training,
validation and inference code) as MLCommons-Box boxes. MLCommons-Box establishes a standard to package user workloads,
and provides unified command line interface. In addition, MLCommons-Box provides a number of reference runners - python
packages that can run boxes on different platforms including docker and singularity.

> A data scientist has been working on a machine learning project. The goal is to train a simple neural network to
> classify collection of 60,000 small images into 10 classes. 


## MNIST training code
Training a ML model is a process involving multiple steps such as getting data, analyzing and cleaning data, 
splitting into train/validation/test data sets, running hyper-parameter optimization experiments and performing final
model testing. It is a relatively small and well studied dataset that provides standard train/test split. In this simple
example a developer needs to implement two steps - (1) downloading data and (2) training a model. We'll call these steps
as `tasks`. Each task requires several parameters, such as URL of the data set that we need to download, location on a
local disk where the data set will be serialized, path to a directory that will contain training artifacts such as log
files, training snapshots and ML models. We can characterize these two tasks in the following way:  
- `Data Download` task:  
  - __Inputs__: None. We'll assume the download URL is defined in the source code.  
  - __Outputs__: Directory to serialize the data set (`data_dir`) and directory to serialize log files (`log_dir`).  
- `Training` task:  
  - __Inputs__: Directory with MNIST data set (`data_dir`), training hyper-parameters defined in a file
    (`parameters_file`).  
  - __Outputs__:  Directory to store training results (`model_dir`) and directory to store log files (`log_dir`).  

We have intentionally made all input/output parameters to be file system artifacts. By doing so, we support
reproducibility. Instead of command line arguments that can easily be lost, we store them in files. There are many
different ways to implement the MNIST example. For simplicity, we assume the following:  
- We use one python file.  
- Task name (download, train) is a command line positional parameter.  
- Both tasks write logs, so it makes sense to add parameter accepting directory for log files.  
- The download task accepts additional data directory parameter.   
- The train task accepts such parameters as data and model directories, path to a file with hyper-parameter.
- Configurable hyper-parameters are: (1) optimizer name, (2) number of training epochs and (3) global batch size. 


Then, our implementation could look like this. Parse command line and identify task. If it is `download`, call a
function that downloads data sets. If it is `train`, train a model. This is sort of single entrypoint implementation
where we run one script asking to perform various tasks. We run our script (mnist.py) in the following way:
```
python mnist.py download --data_dir=PATH --log_dir=PATH
python mnist.py train --data_dir=PATH --log_dir=PATH --model_dir=PATH --parameters_file=PATH
```


## MLCommons-Box implementation
Packaging our MNIST training script as a MLCommons-Box is done in several steps. We will be using a directory-based 
box where a directory is structured in a certain way and contains specific files that make it MLCommons-Box compliant.
We need to create an empty directory on a local disk. Let's assume we call it `mnist` and we'll use
`{MLCOMMONS_BOX_ROOT}` to denote a full path to this directory. This is called a box root directory. At this point this
directory is empty:
```
mnist/
```


### Build location
The box directory has a sub-directory called `build` (`{MLCOMMONS_BOX_ROOT}/build`) that stores project source files,
resources required for training, other files to recreate run time (such as requirements.txt, docker and singularity
recipes etc.). We need to create the build directory and copy two files: mnist.py that implements training and
requirements.txt that lists python dependencies. By doing so, we are enforcing reproducibility. A developer of this 
box wants to make it easier to run their training workload in a great variety of environments including universities, 
commercial companies, HPC-friendly organizations such as national labs. One way to achieve it is to use container
runtime such as docker or singularity. So, we'll provide both docker file and singularity recipe that we'll put into
`build` directory as well. Thus, we'll make this directory a build context. The box directory now looks like:
```
mnist/
  build/
    mnist.py
    requirements.txt
    Dockerfile
    Singularity.recipe
```
A good test at this point would be ensure that project is runnable from the build directory, and docker and singularity
images can be built.  


### MLCommons-Box definition file
At this point we are ready to create a box definition file. This is the first definition file that makes some folder a
MLCommons-Box folder. This is a YAML file that provides information such as name, author, version, named as `mlbox.yaml`
and located in the box root directory . The most important section is the one that lists what tasks are implemented in
this box:
```yaml
schema_version: 1.0.0                            # We use MLSpec library to validate YAML definition files. This is the
schema_type: mlbox_root                          # specification of the schema that this file must be consistent with. 

name: mnist                                      # Name of this box.
author: MLPerf Best Practices Working Group      # A developer of the box.
version: 0.1.0                                   # MLBox version.
mlbox_spec_version: 0.1.0                        # TODO: What is it?

tasks:                                           # Tasks are defined in external YAML files located in tasks folder.
  - 'tasks/download.yaml'                        #    "Download data set" task definition file.
  - 'tasks/train.yaml'                           #    "Training a model" task definition file.
```
At this point, the directory looks like:
```
mnist/
  build/ {mnist.py, requirements.txt, Dockerfile, Singularity.recipe}
  mlbox.yaml
```


### Task definition file
The box definition file references two tasks defined in the `tasks` subdirectory. Each YAML file there defines a 
task supported by the box. Task files are named the same as tasks. We need to create a tasks directory and two files
inside that directory - `download.yaml` and `train.yaml`.

Each task file defines input and output specifications for each task. The download task (download.yaml) is defined:
```yaml
schema_version: 1.0.0           # Task schema definition. Leave this two fields as is.
schema_type: mlbox_task

inputs: []                      # Since this task does not have any inputs, the section is empty.

outputs:                        # This task produces two artifacts - downloaded data and log files.
        - name: data_dir        #    This parameter accepts path to a directory where data set will be serialized.
          type: directory       #    We implicitly specify that this is a directory

        - name: log_dir         #    This parameter accepts path to a directory with log files this task writes.
          type: directory       #    We implicitly specify that this is a directory
```
Names of these parameters are the same that are accepted by mnist.py:
```
python mnist.py download --data_dir=PATH --log_dir=PATH
```

The train task (`train.yaml`) is defined in the following way:
```yaml
schema_version: 1.0.0                # Task schema definition. Leave this two fields as is.
schema_type: mlbox_task

inputs:                              # These are the task inputs.
        - name: data_dir             #    This parameter accepts path to a directory where data set will be serialized.
          type: directory            #    We implicitly specify that this is a directory

        - name: parameters_file      #    A file containing training hyper-parameters.
          type: file                 #    This is a file.

outputs:                             # These are the task outputs.
        - name: log_dir              #    This parameter accepts path to a directory with log files this task writes.
          type: directory            #    We implicitly specify that this is a directory

        - name: model_dir            #    Path to a directory where training artifacts are stored.
          type: directory            #    We implicitly specify that this is a directory
```
Names of these parameters are the same that are accepted by mnist.py:
```
python mnist.py train --data_dir=PATH --log_dir=PATH --model_dir=PATH --parameters_file=PATH
```
At this point, the MLBox directory looks like:
```
mnist/
  build/ {mnist.py, requirements.txt, Dockerfile, Singularity.recipe}
  tasks/ {download.yaml, train.yaml}
  mlbox.yaml
```


### Workspace
The workspace is a directory inside box (`workspace`) where, by default, input/output file system artifacts are
stored. The are multiple reasons to have one. One is to formally have default place for data sets, configuration
and log files etc. Having all these parameters in one place makes it simpler to run boxes on remote hosts and then
sync results back to users' local machines.

We need to be able to provide collection of hyper-parameters and formally define a directory to store logs, models and
MNIST data set. To do so, we create the directory tree `workspace/parameters`, and then create a file 
(`default.parameters.yaml`) with the following content:
```yaml
optimizer: "adam"
train_epochs: 5
batch_size: 32
```  
At this point, the box directory looks like:
```
mnist/
  build/ {mnist.py, requirements.txt, Dockerfile, Singularity.recipe}
  tasks/ {download.yaml, train.yaml}
  workspace/
    parameters/
      default.parameters.yaml
  mlbox.yaml
```


### Run configurations
The MLCommons-Box definition file (`mlbox.yaml`) provides paths to task definition files that formally define tasks
input/output parameters. A run configuration assigns values to task parameters. One reason to define and "implement" 
parameters in different files is to be able to provide multiple configurations for the same task. One example could be 
one-GPU training configuration and 8-GPU training configuration. Since we have two tasks - download and train - we need 
to define at least two run configurations. Run configurations are defined in the `run` subdirectory.  

Run configuration for the download task looks like:
```yaml
schema_type: mlbox_invoke                     # Run (invoke) schema definition. Leave this two fields as is.
schema_version: 1.0.0

task_name: download                           # Task name

input_binding: {}                             # No input parameters for this task.

output_binding:                               # Output parameters, format is "parameter: value"
        data_dir: $WORKSPACE/data             #    Path to serialize downloaded MNIST data set
        log_dir: $WORKSPACE/download_logs     #    Path to log files.
```
The `$WORKSPACE` token is replaced with actual path to the box workspace. File system paths are relative to the
workspace directory. This makes it possible to provide absolute paths for cases when data sets are stored on shared
drives. Run configuration for the train task looks like:
```yaml
schema_type: mlbox_invoke                     # Run (invoke) schema definition. Leave this two fields as is.
schema_version: 1.0.0

task_name: train                              # Task name

input_binding:                                # Input parameters (name: value)
        data_dir: $WORKSPACE/data
        parameters_file: $WORKSPACE/parameters/default.parameters.yaml

output_binding:                               # Output parameters (name: value)
        log_dir: $WORKSPACE/train_logs
        model_dir: $WORKSPACE/model
```
At this point, the box directory looks like:
```
mnist/
  build/ {mnist.py, requirements.txt, Dockerfile, Singularity.recipe}
  tasks/ {download.yaml, train.yaml}
  workspace/parameters/default.parameters.yaml
  run/
    download.yaml
    train.yaml
  mlbox.yaml
```


### Platform configurations
Platform configurations define how MLCommons-Box boxes run. Docker, Singularity, SSH and cloud runners have their own 
configurations. For instance, Docker platform configuration at minimum provides image name and docker executable 
(docker / nvidia-docker). SSH platform configuration could provide IP address of a remote host, login credentials etc.
Platform configurations are supposed to be used by runners, and each runner has its own platform schema. The `Runners`
documentation section provides detailed description of reference runners together with platform configuration schemas. 
Since we wanted to support Docker and Singularity runtimes, we provide `docker.yaml` and `singularity.yaml` files in
the `platforms` subdirectory that is default location to store these types of files. Docker platform configuration is
the following:
```yaml
schema_version: 1.0.0
schema_type: mlbox_docker

image: mlperf/mlbox:mnist   # Docker image name
docker_runtime: docker      # Docker executable: docker or nvidia-docker

```

Singularity platform configuration is the following:
```yaml
schema_version: 1.0.0
schema_type: mlbox_singularity

image: /opt/singularity/mlperf_mlbox_mnist-0.01.simg   # Path to or name of a Singularity image.
```
At this point, the box directory looks like:
```
mnist/
  build/ {mnist.py, requirements.txt, Dockerfile, Singularity.recipe}
  tasks/ {download.yaml, train.yaml}
  workspace/parameters/default.parameters.yaml
  run/ {download.yaml, train.yaml}
  platforms/
    docker.yaml
    singularity.yaml
  mlbox.yaml
```


## MNIST MLCommons-Box directory structure summary
```yaml
mnist/                                   # MLBox root directory.
    build/                               # Project source code, resource files, Docker/Singularity recipes.
        mnist.py                         #    Python source code training simple neural network using MNIST data set.
        requirements.txt                 #    Python project dependencies.
        Dockerfile                       #    Docker recipe.
        Singularity.recipe               #    Singularity recipe.
    tasks/                               # Task definition files - define functionality that MLBox supports
        download.yaml                    #    Download MNIST data set.
        train.yaml                       #    Train neural network.
    workspace/                           # Default location for data sets, logs, models, parameter files.
        parameters/                      #    Model hyper-parameters can be stored at any location.
          default.parameters.yaml        #       This is just what is used in this implementation.
    run/                                 # Run configurations - bind task parameters and values.
        download.yaml                    #    Concrete run specification for the download task.
        train.yaml                       #    Concrete run specification for the train task.
    platforms/                           # Platform definition files - define how MLBox runs.
        docker.yaml                      #    Docker runtime definition.
        singularity.yaml                 #    Singularity runtime definition. 
  mlbox.yaml                             # MLBox definition file.
```


## Running MNIST MLCommons-Box
We need to setup the Python virtual environment. These are the steps outlined in the `Introduction` section except we do
not clone GitHub repository with the example MLCommons-Box boxes. 
```
# Create Python Virtual Environment
virtualenv -p python3 ./env && source ./env/bin/activate

# Install MLCommons-Box Docker and Singularity runners 
pip install mlcommons-box-docker mlcommons-box-singularity

# Optionally, setup host environment by providing the correct `http_proxy` and `https_proxy` environmental variables.
# export http_proxy=...
# export https_proxy=..
``` 

> Before running MNIST box below, it is probably a good idea to remove tasks' outputs from previous runs that are
> located in the `workspace` directory. All directories except `parameters` can be removed.


### Docker Runner
Configure MNIST box:
```
mlcommons_box_docker configure --mlbox=. --platform=platforms/docker.yaml
```

Run two tasks - `download` (download data) and `train` (train tiny neural network):
```
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/download.yaml
mlcommons_box_docker run --mlbox=. --platform=platforms/docker.yaml --task=run/train.yaml
```


### Singularity Runner
Update path to store Singularity image. Open `platforms/singularity.yaml` and update the `image` value
that is set by default to `/opt/singularity/mlperf_mlbox_mnist-0.01.simg` (relative paths are supported, they are
relative to `workspace`).  


Configure MNIST box:
```
mlcommons_box_singularity configure --mlbox=. --platform=platforms/singularity.yaml
```

Run two tasks - `download` (download data) and `train` (train tiny neural network):
```
mlcommons_box_singularity run --mlbox=. --platform=platforms/singularity.yaml --task=run/download.yaml
mlcommons_box_singularity run --mlbox=. --platform=platforms/singularity.yaml --task=run/train.yaml
```

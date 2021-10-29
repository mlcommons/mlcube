# MNIST
The [MNIST dataset](http://yann.lecun.com/exdb/mnist/) is a collection of 60,000 handwritten digits widely used for
training statistical, Machine Learning (ML) and Deep Learning (DL) models. The MNIST MLCube example demonstrates
how data scientists, ML and DL researchers and developers can distribute their ML projects (including training,
validation and inference code) as MLCube cubes. MLCube establishes a standard to package user workloads,
and provides unified command line interface. In addition, MLCube provides a number of reference runners - python
packages that can run cubes on different platforms including 
[Docker](https://mlcommons.github.io/mlcube/runners/docker-runner/),
[Singularity](https://mlcommons.github.io/mlcube/runners/singularity-runner/),
[KubeFlow](https://mlcommons.github.io/mlcube/runners/kubeflow/)
and several others.

> A data scientist has been working on a machine learning project. The goal is to train a simple neural network to
> classify the collection of 60,000 small images into 10 classes. 

> The source files for this MNIST example can be found on  GitHub in MLCube Example [repository](https://github.com/mlcommons/mlcube_examples).

## MNIST training code
Training an ML model is a process involving multiple steps such as downloading data, analyzing and cleaning data, 
splitting data into train/validation/test data sets, running hyper-parameter optimization experiments and performing final
model testing. MNIST dataset is a relatively small and well studied dataset that provides standard train/test split. In this simple
example a developer needs to implement two steps - (1) downloading data and (2) training a model. We call these steps
as `tasks`. Each task requires several parameters, such as a URL of the data set that we need to download, location on a
local disk where the data set will be downloaded to, path to a directory that will contain training artifacts such as log
files, training snapshots and Machine Learning models. We can characterize these two tasks in the following way:  

- `Download` task:
     - __Inputs__: A yaml file (`data_config`) with two parameters - dataset URI and dataset hash.
     - __Outputs__: Directory to serialize the data set (`data_dir`) and directory to serialize log files (`log_dir`).
- `Training` task:
     - __Inputs__: Directory with MNIST data set (`data_dir`), training hyper-parameters defined in a file
       (`train_config`).
     - __Outputs__:  Directory to store training results (`model_dir`) and directory to store log files (`log_dir`).

We have intentionally made all input/output parameters to be file system artifacts. By doing so, we support
reproducibility. Instead of command line arguments that can easily be lost, we store them in files. There are many
ways to implement the MNIST example. For simplicity, we assume the following:  

- We use one python file.  
- Task name (download, train) is a command line positional parameter.  
- Both tasks write logs, so it makes sense to add a parameter that defines a directory for log files.  
- The download task accepts additional data directory parameter.   
- The train task accepts such parameters as data and model directories, path to a file with hyper-parameter.
- Configurable hyper-parameters are: (1) optimizer name, (2) number of training epochs and (3) global batch size. 


Then, our implementation could look like this. Parse command line arguments and identify a task to run. If it is 
the `download` task, call a function that downloads data sets. If it is the `train` task, train a model. This is sort 
of single entrypoint implementation where we run one script asking to perform various tasks. We run our script (mnist.py)
in the following way:
```
python mnist.py download --data_config=PATH --data_dir=PATH --log_dir=PATH
python mnist.py train --train_config=PATH --data_dir=PATH --model_dir=PATH --log_dir=PATH
```


## MLCube implementation
Packaging our MNIST training script as a MLCube is done in several steps. We will be using a directory-based 
cube where a directory is structured in a certain way and contains specific files that make it MLCube compliant.
We need to create an empty directory on a local disk. Let's assume we call it `mnist` and we'll use
`{MLCUBE_ROOT}` to denote a full path to this directory. This is called an MLCube root directory. At this point this
directory is empty:
```
mnist/
```


### Build location
The MLCube root directory will contain project source files, resources required for training, other files to recreate 
run time (such as requirements.txt, docker and singularity recipes etc.). We need to copy two files: mnist.py that 
implements training and requirements.txt that lists python dependencies. By doing so, we are enforcing reproducibility. 
A developer of this MLCube wants to make it easier to run their training workload in a great variety of environments 
including universities, commercial companies, HPC-friendly organizations such as national labs. One way to achieve it is 
to use container runtime such as docker or singularity. So, we'll provide both docker file and singularity recipe that 
we'll put into the MLCube root directory as well. Thus, we'll make this directory a build context. For reasons that we
will explain later, we also need to add .dockerignore file (that contains single line - `workspace/`). The MLCube 
directory now looks like:
```
mnist/
  .dockerignore
  Dockerfile
  mnist.py
  requirements.txt
  Singularity.recipe
```
A good test at this point would be to ensure that project is runnable from the build directory, and docker and 
singularity images can be built.  


### MLCube definition file
At this point we are ready to create a cube definition file. This is the first definition file that makes a folder to be
an MLCube folder. This is a YAML file that provides information such as name, author, version, named as `mlcube.yaml`
and located in the cube root directory . The most important section is the one that lists what tasks are implemented in
this cube:
```yaml
# Name of this MLCube.
name: mnist
# Brief description for this MLCube.
description: MLCommons MNIST MLCube example
# List of authors/developers. 
authors:
  - name: "First Second"
    email: "first.second@company.com"
    org: "Company Inc."

# Platform description. This is where users can specify MLCube resource requirements, such as 
# number of accelerators, memory and disk requirements etc. The exact structure and intended 
# usage of information in this section is work in progress. This section is optional now.
platform:
  accelerator_count: 0
  accelerator_maker: NVIDIA
  accelerator_model: A100-80GB
  host_memory_gb: 40
  need_internet_access: True
  host_disk_space_gb: 100

# Configuration for docker runner (additional options can be configured in system settings file).
docker:
  image: mlcommons/mnist:0.0.1

# Configuration for singularity runner (additional options can be configured in system settings 
# file).
singularity:
  image: mnist-0.0.1.simg

# Section where MLCube tasks are defined.
tasks:
  # `Download` task. It has one input and two output parameters.
  download:
    parameters:
      inputs: {data_config: data.yaml}
      outputs: {data_dir: data/, log_dir: logs/}
  # `Train` task. It has two input and two output parameters.
  train:
    parameters:
      inputs: {data_dir: data/, train_config: train.yaml}
      outputs: {log_dir: logs/, model_dir: model/}
```
At this point, the directory looks like:
```
mnist/
  .dockerignore
  Dockerfile
  mlcube.yaml
  mnist.py
  requirements.txt
  Singularity.recipe
```


### Workspace
The workspace is a directory inside cube (`workspace`) where, by default, input/output file system artifacts are
stored. There are multiple reasons to have one. One is to formally have default place for data sets, configuration
and log files etc. Having all these parameters in one place makes it simpler to run cubes on remote hosts and then
sync results back to users' local machines.

We need to be able to provide URI and hash of the MNIST dataset, collection of hyper-parameters and formally define a 
directory to store logs, models and MNIST data set. To do so, we create the directory tree `workspace/`, and then create 
two files with the following content (`data.yaml`):
```yaml
uri: https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz
hash: 731c5ac602752760c8e48fbffcf8c3b850d9dc2a2aedcf2cc48468fc17b673d1
```
and `train.yaml`:
```yaml
optimizer: "adam"
train_epochs: 5
batch_size: 32
```  
At this point, the cube directory looks like:
```yaml
mnist/
  workspace/
    data.yaml
    train.yaml
  .dockerignore
  Dockerfile
  mlcube.yaml
  mnist.py
  requirements.txt
  Singularity.recipe
```


## MNIST MLCube directory structure summary
```yaml
mnist/
  workspace/          # Default location for data sets, logs, models, parameter files.
    data.yaml         #   URI and hash of MNIST dataset.
    train.yaml        #   Train hyper-parameters.
  .dockerignore       # Docker ignore file that prevents workspace directory to be sent to docker server.
  Dockerfile          # Docker recipe.
  mlcube.yaml         # MLCube definition file.
  mnist.py            # Python source code training simple neural network using MNIST data set.
  requirements.txt    # Python project dependencies.
  Singularity.recipe  # Singularity recipe.
```


## Running MNIST MLCube
We need to set up the Python virtual environment. These are the steps outlined in the `Introduction` section except we 
do not clone GitHub repository with the example MLCube cubes. 
```
# Create Python Virtual Environment
virtualenv -p python3.6 ./env && source ./env/bin/activate

# Install MLCube Docker and Singularity runners 
pip install mlcube-docker mlcube-singularity
``` 

> Before running MNIST cube below, it is probably a good idea to remove tasks' outputs from previous runs that are
> located in the `workspace` directory. All directories except can be removed.


### Docker Runner
Configure MNIST cube (this is optional step, docker runner checks if image exists, and if it does not, runs `configure`
phase automatically):
```
mlcube configure --mlcube=. --platform=docker
```

Run two tasks - `download` (download data) and `train` (train tiny neural network):
```
mlcube run --mlcube=. --platform=docker --task=download
mlcube run --mlcube=. --platform=docker --task=train
```


### Singularity Runner
Configure MNIST cube:
```
mlcube configure --mlcube=. --platform=singularity
```

Run two tasks - `download` (download data) and `train` (train tiny neural network):
```
mlcube run --mlcube=. --platform=singularity --task=download
mlcube run --mlcube=. --platform=singularity --task=train
```

# Tutorial Create an MLCube 
<div style="text-align:center"><span style="color:black; font-family:Georgia; font-size:2em;">Interested in getting started with MLCube? Follow the instructions in this tutorial, or watch the video below.</span></div>
[![Watch the video](http://img.youtube.com/vi/hQRBLW6giRc/0.jpg)](https://www.youtube.com/embed/hQRBLW6giRc)
## Step 1: SETUP   
Create a python environment and get MLCube.
```
virtualenv -p python3 ./env && source ./env/bin/activate
pip install mlcube mlcube-docker cookiecutter 
```
## Step 2: DEFINE A CONTAINER FOR YOUR MODEL with a DOCKERFILE  
Let's download the 'matmult' example to illustrate how to make an MLCube. This is a simple matrix multiply written in python and tensorflow. 
When you create an MLCube for your own model you will use your own code, data and dockerfile.
 
You can clone the mlcube examples from GtiHub:
```
cd $HOME
git clone https://github.com/mlcommons/mlcube_examples
cd mlcube_examples
# create a directory for your new mlcube
mkdir -p my_mlcube/build 
cd my_mlcube/build
# copy the matmul.py,Dockerfile and requirements.txt to your my_mlcube/build directory
cp $HOME/mlcube_examples/matmul/build/*  . 

```
You will need a docker image to create an MLCube.  We will use the Dockerfile for 'matmul' to create a docker container image:   
<sub><sup><span style="color:blue">Note: the last line of the Dockerfile must be    
"ENTRYPOINT ["python3", "/workspace/your_mlcube_name.py"]" as shown below.</span></sup></sub> 
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

COPY matmul.py /workspace/matmul.py

<strong>ENTRYPOINT ["python3", "/workspace/matmul.py"]</strong>
</code></pre>
## Step 3: BUILD & PUSH YOUR DOCKER IMAGE TO A PUBLIC REPO 
```
# After you have created a repository on https://hub.docker.com or another public repository 
docker build --tag matmul:1.0 .
docker push yourusername/matmul 
```
## Step 4: GET MLCUBE TEMPLATES
Create templates for your project.  Answer two quesitons - MLCube name and authors.
```  
# Previously we could Clone MLCube Templates
#git clone https://github.com/sergey-serebryakov/mlbox/tree/feature/mlbox-template/examples/template 

cookiecutter https://github.com/mlperf/mlcube_cookiecutter.git
```
## Step 4: USE TEMPLATE FILES TO SET UP MLCUBE
```
cd ./platforms
# Edit the docker.yaml file specifiing the platform name you want (docker or kubernetes or ssh)
```  
```
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
  # image: "mlperf/mlbox_mnist:0.0.2"
```
## Step 4: TEST YOUR MLCUBE

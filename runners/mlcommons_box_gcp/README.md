# MLCommons-Box Google Compute Platform (GCP) Runner

... describe scenario here ...
What are the requirements?

- What's docker error code 137
- Users have GCP accounts. If not, what happens?
- Users have running instances.
- SSH authentication
  - Users provide the username and private key path to use via platform files and env variables `MLBOX_SSH_KEY`.
  - Users use .ssh/config:
    ```
    Host myshortname realname.example.com
        HostName realname.example.com
        IdentityFile ~/.ssh/realname_rsa # private key for realname
        User remoteusername
    
    Host myother realname2.example.org
        HostName realname2.example.org
        IdentityFile ~/.ssh/realname2_rsa  # different private key for realname2
        User remoteusername
    ```
- GCP instance has docker installed.
- GCP instance has system python with mlcommons_box dependencies.
- SSH/GCP - platform files - what is in the file?
- How to initialize remote python environment?

## Virtual machine
```
Project:
    Name: My First Project
    ID: atomic-envelope-293722

base image: ubuntu-1804-bionic-v20201014
Machine type: f1-micro (1 vCPU, 0.6 GB memory)
Zone: us-central1-a
Storage: 20 GB
OS: 18.04.5 LTS
```


## Installing docker
```shell script
sudo snap install docker

sudo addgroup --system docker
sudo adduser ${USER} docker
newgrp docker

sudo snap disable docker
sudo snap enable docker

sudo apt-get update
yes | sudo apt-get install python3-pip virtualenv
sudo apt-get clean

# not required with the new SSH runner
sudo pip3 install click==7.1.2 mlspeclib==1.0.0

```


## Machine Image
Name: mlcommons-box-demo-f1-micro


## Accessing VM via ssh
New users need to enable SSH access via third-party tools (like Putty). One way to do so is to add public ssh key via 
[metadata](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys). Generate public/private key pair.
Make sure to set `key comment` to your GCP user name. Then use the following command to shh into VM:
```shell script
ssh -i PATH_TO_GCP_PRIVATE_KEY GCP_USER_NAME@IP_ADDRESS
``` 


python -m mlcommons_box_ssh configure --mlbox=. --platform=platforms/ssh_gcp.yaml
python -m mlcommons_box_ssh run --mlbox=. --platform=platforms/ssh_gcp.yaml --task=run/alice/hello.yaml
python -m mlcommons_box_ssh run --mlbox=. --platform=platforms/ssh_gcp.yaml --task=run/alice/bye.yaml
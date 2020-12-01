# Google Compute Platform (GCP) Runner

> __DISCLAIMER__ MLCube is under active development. Allocating and using instances in clouds are associated with
> costs. Users of GCP runners should be aware about it, especially, taking into account capability of GCP runners to
> automatically create and start remote instances. GCP RUNNERS in current implementation DO NOT stop/destroy remote
> instances. Users are encouraged to visit web consoles to identify what virtual instances exist and run.


> GCP runner can update users' `${HOME}/.ssh/config` configuration files.

GCP runner is a frontend runner for running MLCubes in Google cloud. It is called a frontend runner because it does not
actually run cubes, but ensures that a remote instance is up and running, and then uses other runners to actually run
MLCubes. The following chain of runners is supported and has been tested:
1. A user interacts with GCP runners. These runners are responsible for creating remote instances (if they do not 
   exist), start them, install required software stack (such as docker or singularity).
2. Once a remote instance is up and running, GCP runners delegates further execution to other runners, such as 
   [SSH runners](https://mlcommons.github.io/mlcube/runners/ssh-runner/). SSH runners are responsible for delivering
   MLCubes to remote instances. SSH runners then delegate the actual execution of cubes on those remote instances to
   such runners as [docker runner](https://mlcommons.github.io/mlcube/runners/docker-runner/) or 
   [singularity runner](https://mlcommons.github.io/mlcube/runners/singularity-runner/).
 
The described scenario assumes the presence of the following platform configuration files: GCP, SSH and one of Docker or
Singularity. As MLCube project evolves, other paths may become possible to run cubes in clouds such as GCP.

## Pre-requisites
To use GCP runners, users need to have a GCP account. The following account details must be known and available in
advance:
1. Project ID.
2. Zone.
3. Service account [JSON file](https://cloud.google.com/docs/authentication/production#create_service_account).
4. Users should configure their GCP accounts so that ever new virtual instance is automatically deployed with user 
   public key making it available through SSH access automatically.


## Creating remote instances
Remote instances for running MLCubes can be created manually or automatically. 
1. To create a virtual instance manually, go to GCP console, select `Compute Engine` and then `VM instances`. Write
   down an instance name.
2. To create a virtual instance automatically, a GCP platform file needs be configured. A limited functionality is
   supported. Basically, users can only specify `machine type` and `disk size`. Ubuntu 18.04 OS will be used as a base
   image.

## Platform configuration file
The following is an example of the actual GCP platform configuration file used in one of the tutorials:
```yaml
# GCP login credentials
gcp:
    # These are your project ID and zone names. 
    project_id: 'atomic-envelope-293722'
    zone: 'us-central1-a'
    credentials:
        # As described above, ensure you have servuce account activated and download your JSON key file.
        file: '${HOME}/.gcp/service_account_key_file.json'
        scopes: ['https://www.googleapis.com/auth/cloud-platform']


# Instance parameters.
#    If existing remote instance is used, only `name` field is used. Other fields are not taken into account.
#    If users want GCP runners to automatically create remote instances, all three fields must present. Instance name
#       is arbitrary name for this instance. Machine type must be the valid GCP machine type. Ubuntu 18.04 is used
#       as a base OS. 
instance:
    name: 'mlcube-gcp-instance-n1s4'
    machine_type: 'n1-standard-4'
    disk_size_gb: 100

# As described above, primary role of GCP runners is to ensure a remote instance exists before delegating the actual
# `MLCube run` functionality to other runners. Currently, the only available option is a SSH runner (that assumes 
# remote instances are available vis SSH i.e. they have public IPs). The `platform` field below specifies what runner
# the GCP runner should be using once GCP virtual instance has been created. A SSH runner needs to be configured
# separately (see sections below for some recommendations and best practices). 
platform: 'ssh.yaml'
``` 

## GCP runner `configure` phase
GCP runners execute the following steps during the configure phase:
1.  Check that SSH access has been configured. A runner loads users `${HOME}/.ssh/config` file and verifies it 
    contains a section for the remote instance there (specified by the name). The configuration section must define 
    `User` and `IdentityFile`.
2. GCP runner connects to GCP using provided project ID, zone name and `credentials` (file name and scopes).
3. GCP runner checks if a remote instance exists with the provided name. If it does not exist, it creates it using three
   parameters described above - instance name, machine type and disk size.
4. If a remote instance is not running, GCP runner starts it.
5. GCP runner retrieves a remote instance's meta data that includes public IP address. If public IP address does not 
   match `HostName` in ssh configuration file, __GCP RUNNER UPDATES USER SSH CONFIG FILE__.
6. Currently, GCP runner automatically installs such packages, as `docker`, `python3` and `virtualenv`.
7. GCP runner calls SSH runner to continue configuring remote instance in a MLCube-specific way.


##  GCP runner `run` phase
GCP runner does not implement any specific logic and redirects its functionality to a SSH runner.   


## Recommendations
1. One remote instance can be used to run different MLCubes. Names of remote instances can reflect their type, for
   instance, `gcp_free_micro_instance`, `gcp_4_cpu_instance`, `gcp_1_gpu_instance`, `gcp_8_gpu_instance` etc.
2. Following the above guidelines, these instances must be configured with key-based SSH access (GCP and SSH runners
   depend on this). Each remote instance must have a section in the `{HOME}/.ssh/config` that should look like:
   ```
   Host mlcube-gcp-instance-n1s4
       HostName {{PUBLIC_IP_ADDRESS}}
       IdentityFile ~/.ssh/gcp_rsa
       User {{GCP_USER_LOGIN_NAME}}
   ```
   GCP runner will update the `HostName` value if actual IP address differs from existing one. Other fields are never
   updated by GCP runners. Section like this one is sufficient to partially configure GCP and fully configure SSH
   runners.
3. After every GCP run, decide if a remote instance needs to be stopped/destroyed. If so, go to web console.  

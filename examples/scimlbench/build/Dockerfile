FROM ubuntu:18.04
MAINTAINER MLPerf MLBox Working Group

# Remove all stopped containers: docker rm $(docker ps -a -q)
# Remove containers like none:none: docker rmi $(docker images | grep none | awk '{print $3}')

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            software-properties-common \
            python3-dev \
	    wget \
	    cmake \
	    g++-4.8 \
	    git \
	    vim \
 	    ca-certificates \
	    libibverbs1 \
	    librdmacm1 \
      	    ibverbs-providers \
	    build-essential \
            curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py


RUN mkdir /tmp/openmpi && \
    cd /tmp/openmpi && \
    wget https://www.open-mpi.org/software/ompi/v4.0/downloads/openmpi-4.0.0.tar.gz && \
    tar zxf openmpi-4.0.0.tar.gz && \
    cd openmpi-4.0.0 && \    
    ./configure --enable-orterun-prefix-by-default && \
    make -j $(nproc) all && \
    make install && \
    ldconfig && \
    rm -rf /tmp/openmpi

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

RUN HOROVOD_WITH_TENSORFLOW=1 pip install --no-cache-dir horovod

# Install OpenSSH for MPI to communicate between containers
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client openssh-server && \
    mkdir -p /var/run/sshd

# Allow OpenSSH to talk to containers without asking for confirmation
RUN cat /etc/ssh/ssh_config | grep -v StrictHostKeyChecking > /etc/ssh/ssh_config.new && \
    echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config.new && \
    mv /etc/ssh/ssh_config.new /etc/ssh/ssh_config

COPY em_denoise_data.zip /workspace/data/em_denoise_data.zip
#RUN apt-get update && apt-get install zip unzip
COPY main.py /workspace/main.py
ENTRYPOINT ["python3", "/workspace/main.py"]

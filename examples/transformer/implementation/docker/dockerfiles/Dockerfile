FROM nvidia/cuda:10.0-cudnn7-runtime-ubuntu18.04

WORKDIR /mlcube

ENV HOME /mlcube
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    python3.6 \
    python3.6-dev \
    python3-pip \
    python3-setuptools

COPY implementation /mlcube/implementation
COPY tasks /mlcube/tasks

RUN pip3 install wheel && pip3 install -r implementation/src/requirements.txt
# Install mlperf logging lib
RUN pip3 install "git+https://github.com/mlperf/logging.git@44d26ff1341eaf7ed5a7105176c8ccc36e088d59"

ENTRYPOINT ["implementation/src/scripts/mlcube_entry.sh"]

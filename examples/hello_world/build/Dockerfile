FROM ubuntu:18.04
MAINTAINER MLPerf MLCube Working Group

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

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY hello_world.py /workspace/hello_world.py
ENTRYPOINT ["python3", "/workspace/hello_world.py"]

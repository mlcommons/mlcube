FROM ubuntu:16.04
MAINTAINER MLPerf MLBox Working Group

# Remove all stopped containers: docker rm $(docker ps -a -q)
# Remove containers like none:none: docker rmi $(docker images | grep none | awk '{print $3}')

RUN apt-get update && apt-get install -y --no-install-recommends python3-dev python3-pip curl

RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

RUN pip3 --no-cache-dir install tensorflow==2.1.0

COPY mnist.py /workspace/mnist.py

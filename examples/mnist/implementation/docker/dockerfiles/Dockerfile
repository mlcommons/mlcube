FROM ubuntu:16.04
MAINTAINER MLPerf MLBox Working Group

# Remove all stopped containers: docker rm $(docker ps -a -q)
# Remove containers like none:none: docker rmi $(docker images | grep none | awk '{print $3}')

RUN apt-get update && apt-get install -y --no-install-recommends python3-dev python3-pip curl

RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

COPY implementation/src/requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

COPY implementation/src/mnist.py /workspace/mnist.py
ENTRYPOINT ["python3", "/workspace/mnist.py"]
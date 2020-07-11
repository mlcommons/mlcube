
# Pull base image.
FROM ubuntu:20.04

RUN apt update
RUN apt-get -y install python3

ADD src/ src/
ADD internal_docker_mlbox_main.py /internal_docker_mlbox_main.py

RUN which python3

ENTRYPOINT ["/usr/bin/python3", "internal_docker_mlbox_main.py"]


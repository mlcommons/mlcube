
FROM nvidia/cuda:10.2-base

RUN apt update
RUN apt-get -y install python3

ADD internal_docker_* /

ENTRYPOINT ["/usr/bin/python3", "/internal_docker_mlbox_main.py"]

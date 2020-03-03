FROM nvcr.io/nvidia/tensorflow:18.07-py3
MAINTAINER MLPerf MLBox Working Group

# Remove all stopped containers: docker rm $(docker ps -a -q)
# Remove containers like none:none: docker rmi $(docker images | grep none | awk '{print $3}')


COPY implementation/src/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY implementation/src/mlbox_runner.py /workspace/nvidia-examples/cnn/mlbox_runner.py

WORKDIR /workspace/nvidia-examples/cnn
ENTRYPOINT ["python", "mlbox_runner.py"]

Here is a starting point to create your MLBox's Docker Image.

Here are some notes to get started:
- Feel free to replace Dockerfile with an existing one you use!
- Make sure to use internal_docker_mlbox_main.py as your main file (even in a
  different docker).


1. Each task in your MLBox has a separate main file which was generated:
examples/nvidia_smi/mlbox/build/internal_docker_mlbox_task_nvidia_smi.py
Edit these files to call your model.

2. Build your docker;
sudo docker build . -t mlperf/mlbox:nvidia_smi

3. Try running your docker (may want to -f for overwriting output files);
python3 mlbox_docker_run/docker_run.py --no-pull examples/nvidia_smi/mlbox/run/nvidia_smi.yaml


4. Once  your docker works, upload it to the respository.
docker push mlperf/mlbox:nvidia_smi

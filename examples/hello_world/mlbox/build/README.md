Here is a starting point to create your MLBox's Docker Image.

Here are some notes to get started:
- Feel free to replace Dockerfile with an existing one you use!
- Make sure to use internal_docker_mlbox_main.py as your main file (even in a
  different docker).


1. Each task in your MLBox has a separate main file which was generated:
examples/hello_world/mlbox/build/internal_docker_mlbox_task_hello.py, examples/hello_world/mlbox/build/internal_docker_mlbox_task_goodbye.py
Edit these files to call your model.

2. Build your docker;
sudo docker build . -t mlperf/mlbox:hello_world

3. Try running your docker;
TODO mlbox runner command

4. Once  your docker works, upload it to the respository.
docker push mlperf/mlbox:hello_world

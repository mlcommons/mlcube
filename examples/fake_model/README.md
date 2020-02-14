# MLBox Hello World

Perform the following steps to run the hello-world example.

- Build the container
  ```sh
  docker build -t mlcommons/mlbox-helloworld:latest .
  ```

- Update config file with local environment information
  Open `helloworld_config.yaml` and edit the paths inside as instructed.

- Run the MLBox
  ```sh
  mlbox run --config helloworld_config.yaml
  ```

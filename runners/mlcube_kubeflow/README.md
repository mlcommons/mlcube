# Kubeflow Runner

1. Create MLCube system settings file. It should be located in a user home directory: `${HOME}/mlcube.yaml`. If this 
   is not possible or not convenient, this file can be placed in any location given that environment variable
   `MLCUBE_SYSTEM_SETTINGS` points to this file. 
2. Put the following in this file:
   ```yaml
   kubeflow:
     image: ${docker.image}
     pvc: "Persistent Volume Claim name (?). Actual location must be `workspace` directory of MLCube to run". 
     pipeline_host: 'KF-Pipeline Host URL'      
                 
   ```
   The `pvc` field above has the default value equal to MLCube name (mnist, matmul etc.).
   Set `pipeline_host` field to Kubeflow Pipeline host endpoint.
   
   eg: Set `pipeline_host` to `http://127.0.0.1:8000/pipeline` if Kubeflow Pipelines is used locally by port-forwarding `svc/ml-pipeline-ui` in namespace `kubeflow` to port 8000 
   What to do:
     - Update `k8s.pvc` value.
     - Update `kubeflow.pipeline_host` value
     - Keep `k8s.image` value as it is shown above (`${docker.image}`).
3. Clone MLCube from GitHub repo and run with `--platform=kubeflow`. With Kubeflow runner, tasks field should not be specified as all tasks are pipelined automatically.

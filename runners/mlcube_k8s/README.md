# Kubernetes Runner

1. Create MLCube system settings file. It should be located in a user home directory: `${HOME}/mlcube.yaml`. If this 
   is not possible or not convenient, this file can be placed in any location given that environment variable
   `MLCUBE_SYSTEM_SETTINGS` points to this file. 
2. Put the following in this file:
   ```yaml
   k8s:
     image: ${docker.image}
     pvc: "Persistent Volume Claim name (?). Actual location must be `workspace` directory of MLCube to run".                  
   ```
   The `pvc` field above has the default value equal to MLCube name (mnist, matmul etc.).
   What to do:
     - Update `k8s.pvc` value.
     - Keep `k8s.image` value as it is shown above (`${docker.image}`).
3. Clone MLCube from GitHub repo and run with `--platform=k8s`


## Deprecated
[Documentation](https://mlcommons.github.io/mlcube/runners/kubernetes/)

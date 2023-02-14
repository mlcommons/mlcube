from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Job
from diagrams.onprem import client, container
from diagrams.custom import Custom

# A helper script to generate a K8S diagram for documentation. This
# image should be copied `to PROJECT_ROOT/docs/assets/mlcube-k8s.png`.

with Diagram(name="MLCube-k8s", show=False):
    with Cluster("Kubernetes Runner"):
        yaml_icon = "yaml.jpg"
        config = [
            container.Docker("container"),
            Custom("Task file", yaml_icon)
        ]
    client.User("User") >> config >> Job("k8s")

from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Job
from diagrams.onprem import client, container
from diagrams.custom import Custom

with Diagram(name="MLCommons-Box-k8s", show=False):
    with Cluster("Kubernetes Runner"):
        yaml_icon = "yaml.jpg"
        config = [
            container.Docker("container"),
            Custom("Task file", yaml_icon)
        ]
    client.User("User") >> config >> Job("k8s")

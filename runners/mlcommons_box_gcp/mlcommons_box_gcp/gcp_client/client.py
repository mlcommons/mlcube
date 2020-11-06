import click
from mlcommons_box_gcp.gcp_client.instance import (Instance, Status)
from mlcommons_box_gcp.gcp_client.service import Service


@click.group(name='mlcommons_box_gcp_client')
def cli():
    """ """
    pass


@cli.command(name='list', help='List instances.')
@click.option('--project-id', required=True, type=str, help='Project identifier.')
@click.option('--zone', required=True, type=str, help='Zone.')
def list_instances(project_id: str, zone: str):
    service = Service(project_id=project_id, zone=zone)
    print("Instances:")
    for instance in service.list_instances():
        print(f"\t{Instance(instance)}")


@cli.command(name='status', help='List instances.')
@click.option('--project-id', required=True, type=str, help='Project identifier.')
@click.option('--zone', required=True, type=str, help='Zone.')
@click.argument('name', required=True, type=str)
def instance_status(project_id: str, zone: str, name: str):
    service = Service(project_id=project_id, zone=zone)
    print(Instance(service.get_instance(name=name)))


@cli.command(name='start', help='List instances.')
@click.option('--project-id', required=True, type=str, help='Project identifier.')
@click.option('--zone', required=True, type=str, help='Zone.')
@click.argument('name', required=True, type=str)
def instance_start(project_id: str, zone: str, name: str):
    service = Service(project_id=project_id, zone=zone)
    instance = Instance(service.get_instance(name=name))
    if instance.name is None:
        print(f"Instance '{name}' does not exist.")
    elif instance.status == Status.RUNNING:
        print(f"Instance '{name}' is already running: {instance}")
    else:
        service.wait_for_operation(service.start_instance(instance.name))
        print(f"Instance '{name}' has started: {Instance(service.get_instance(name))}")


@cli.command(name='stop', help='List instances.')
@click.option('--project-id', required=True, type=str, help='Project identifier.')
@click.option('--zone', required=True, type=str, help='Zone.')
@click.argument('name', required=True, type=str)
def instance_stop(project_id: str, zone: str, name: str):
    service = Service(project_id=project_id, zone=zone)
    instance = Instance(service.get_instance(name=name))
    if instance.name is None:
        print(f"Instance '{name}' does not exist.")
    elif instance.status != Status.RUNNING:
        print(f"Instance '{name}' is not running: {instance}")
    else:
        service.wait_for_operation(service.stop_instance(instance.name))
        print(f"Instance '{name}' has stopped: {Instance(service.get_instance(name))}")


@cli.command(name='create', help='List instances.')
@click.option('--project-id', required=True, type=str, help='Project identifier.')
@click.option('--zone', required=True, type=str, help='Zone.')
def instance_create(project_id: str, zone: str):
    service = Service(project_id=project_id, zone=zone)
    service.wait_for_operation(service.create_instance())


@cli.command(name='delete', help='List instances.')
@click.option('--project-id', required=True, type=str, help='Project identifier.')
@click.option('--zone', required=True, type=str, help='Zone.')
@click.argument('name', required=True, type=str)
def instance_delete(project_id: str, zone: str, name: str):
    service = Service(project_id=project_id, zone=zone)
    instance = Instance(service.get_instance(name=name))
    if instance.name is None:
        print(f"Instance '{name}' does not exist.")
    else:
        service.wait_for_operation(service.delete_instance(instance.name))
        print(f"Instance '{name}' has been deleted: {Instance(service.get_instance(name))}")


if __name__ == '__main__':
    cli()

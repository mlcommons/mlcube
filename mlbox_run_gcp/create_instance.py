# Lint as: python3
"""Creates a GCP Instance based on an MLBox platform.

"""


class VMConfig:
    def __init__(self, project, zone, name, machine_type, image):
      self.project = project
      self.zone = zone
      self.name = name
      self.machine_type = machine_type
      self.source_disk_image = image

    def get_config(self):
        self.config = {
            'name': self.name,
            'machineType': self.machine_type,

            # Specify the boot disk and the image to use as a source.
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': self.source_disk_image,
                    }
                }
            ],

            # Specify a network interface with NAT to access the public
            # internet.
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],

            # Allow the instance to access cloud storage and logging.
            'serviceAccounts': [{
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/logging.write'
                ]
            }],
            'metadata': {}
        }
        return self.config



def main():
  pass


if __name__ == '__main__':
  main()

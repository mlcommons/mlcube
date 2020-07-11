from mlspeclib import MLObject, MLSchema
from pathlib import Path
import pprint

MLSchema.populate_registry()
MLSchema.append_schema_to_registry(Path("schemas"))

(sample_instantiated_object, err) = MLObject.create_object_from_file('sample_docker_schema.yaml')

pp = pprint.PrettyPrinter(indent=4)
if err != {}:
    pp.pprint(err)
else:
    pp.pprint(sample_instantiated_object.tasks)


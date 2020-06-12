from mlspeclib import MLObject, MLSchema
from pathlib import Path
import pprint

MLSchema.populate_registry()
MLSchema.append_schema_to_registry(Path("schemas"))

(sample_instantiated_object, err) = MLObject.create_object_from_file('sample_instantiated_schema.yaml')

pp = pprint.PrettyPrinter(indent=4)
if err != {}:
    pp.pprint(err)
else:
    pp.pprint(sample_instantiated_object.tasks)

(sample_task_object, err) = MLObject.create_object_from_file('tasks/download_data.yaml')

if err != {}:
    pp.pprint(err)
else:
    pp.pprint(sample_task_object.inputs)
    pp.pprint(sample_task_object.outputs)

load_path = Path('tasks').glob("*.yaml")
load_list = list(load_path)

for this_file in load_list:
    file_text = this_file.read_text()
    (loaded_object, err) = MLObject.create_object_from_string(file_text)
    if err != {}:
        print(f"ERROR LOADING FILE: {this_file}")
        pp.pprint(err)
        print("\n\n")
    else:
        print(f"File loaded: {this_file}")
        pp.pprint(loaded_object)
        print("\n\n")


from mlspeclib import MLObject, MLSchema
from pathlib import Path

MLSchema.populate_registry()
MLSchema.append_schema_to_registry(Path("schemas"))

(sample_instantiated_object, err) = MLObject.create_object_from_file('sample_instantiated_schema.yaml')

load_path = Path('tasks').glob("*.yaml")
load_list = list(load_path)

for task_file in load_list:
    if task_file.exists() == False:
        raise FileNotFoundError(f"No task file named '{str(task_file)}'' exists.")
    
    task_file_text = task_file.read_text()

    (loaded_task_file_object, err) = MLObject.create_object_from_string(task_file_text)
    if err != {}:
        print(f"ERROR LOADING FILE: {task_file_text}")
        pp.pprint(err)
        print("\n\n")
    else:
        print(f"File loaded: {task_file_text}")
        pp.pprint(loaded_task_file_object)
        print("\n\n")

## 
# START DOING RUNNER STUFF DOWN HERE
# 
# loaded_task_file_object.inputs.raw_dir
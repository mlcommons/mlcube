"""mlcube
"""
__version__ = "0.1.0"
name = "mlcube"

import importlib
import pkgutil

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules()
    if name.startswith('mlcube_')
}


def validate_type(obj, expected_type) -> None:
    if not isinstance(obj, expected_type):
        raise TypeError(f"Actual object type ({type(obj)}) != expected type ({expected_type}).")

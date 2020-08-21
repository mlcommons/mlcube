"""mlcommons-box
"""
__version__ = "0.1.0"
name = "mlcommons_box"

import importlib
import pkgutil

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules()
    if name.startswith('mlcommons_box_')
}

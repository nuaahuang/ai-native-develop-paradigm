import os
import importlib

__all__ = []

for filename in os.listdir(os.path.dirname(__file__)):
    if filename.endswith('_api.py') and filename != '__init__.py':
        module_name = filename[:-3]
        __all__.append(module_name)
        try:
            importlib.import_module(f'.{module_name}', __name__)
        except ImportError:
            pass

__version__ = '1.0.0'

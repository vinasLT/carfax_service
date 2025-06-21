import os
import importlib
from .base import Base


current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.startswith('_') or filename == 'base.py' or not filename.endswith('.py'):
        continue
    module_name = filename[:-3]
    importlib.import_module(f"{__name__}.{module_name}")
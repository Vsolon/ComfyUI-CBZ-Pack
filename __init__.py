"""Top-level package for cbz_pack."""

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]

__author__ = """Vsolon"""
__email__ = "you@gmail.com"
__version__ = "0.0.1"

# Import main nodes
from .src.cbz_pack.nodes import NODE_CLASS_MAPPINGS as MAIN_NODES
from .src.cbz_pack.nodes import NODE_DISPLAY_NAME_MAPPINGS as MAIN_DISPLAY_NAMES

# Import debug nodes
from .src.cbz_pack.debug_nodes import NODE_CLASS_MAPPINGS as DEBUG_NODES
from .src.cbz_pack.debug_nodes import NODE_DISPLAY_NAME_MAPPINGS as DEBUG_DISPLAY_NAMES

# Combine both mappings
NODE_CLASS_MAPPINGS = {**MAIN_NODES, **DEBUG_NODES}
NODE_DISPLAY_NAME_MAPPINGS = {**MAIN_DISPLAY_NAMES, **DEBUG_DISPLAY_NAMES}

WEB_DIRECTORY = "./web/js"

print("Loaded nodes:", NODE_CLASS_MAPPINGS)
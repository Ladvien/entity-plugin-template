"""Entity Plugin Template - Template for creating Entity Framework plugins.

This package provides template implementations and examples for creating
custom Entity Framework plugins.
"""

from .simple_plugin import SimplePlugin
from .async_plugin import AsyncPlugin
from .configured_plugin import ConfiguredPlugin
from .stateful_plugin import StatefulPlugin

__all__ = [
    "SimplePlugin",
    "AsyncPlugin",
    "ConfiguredPlugin",
    "StatefulPlugin",
]

__version__ = "0.1.0"
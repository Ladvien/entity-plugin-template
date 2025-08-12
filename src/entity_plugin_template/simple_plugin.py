"""Simple Plugin Template - Basic plugin implementation example."""

from __future__ import annotations

from typing import Any

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext


class SimplePlugin(Plugin):
    """A simple plugin that demonstrates basic plugin structure.
    
    This plugin shows the minimal requirements for creating an Entity Framework
    plugin. It simply passes messages through with optional logging.
    """
    
    # Define which workflow stages this plugin supports
    supported_stages = ["INPUT", "OUTPUT"]
    
    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        """Initialize the plugin.
        
        Args:
            resources: Shared resources like LLM clients, memory, etc.
            config: Optional configuration dictionary
        """
        super().__init__(resources, config)
        
        # Access configuration with defaults
        self.log_messages = self.config.get("log_messages", False)
        self.prefix = self.config.get("prefix", "[SimplePlugin]")
    
    async def execute(self, context: PluginContext) -> PluginContext:
        """Execute the plugin logic.
        
        Args:
            context: The plugin execution context containing message and metadata
            
        Returns:
            Modified context after plugin execution
        """
        # Log the message if configured
        if self.log_messages:
            print(f"{self.prefix} Processing: {context.message}")
        
        # Add metadata to track this plugin's execution
        context.metadata["simple_plugin_executed"] = True
        
        # Optionally modify the message
        if self.config.get("add_prefix", False):
            context.message = f"{self.prefix} {context.message}"
        
        # Return the (potentially modified) context
        return context
    
    def validate(self) -> bool:
        """Validate plugin configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check that prefix is a string if provided
        if "prefix" in self.config and not isinstance(self.config["prefix"], str):
            return False
        
        # Check that log_messages is a boolean if provided
        if "log_messages" in self.config and not isinstance(self.config["log_messages"], bool):
            return False
        
        return True
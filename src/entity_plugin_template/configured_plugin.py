"""Configured Plugin Template - Shows advanced configuration with Pydantic."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext


class ProcessingMode(Enum):
    """Available processing modes for the plugin."""
    FAST = "fast"
    BALANCED = "balanced"
    THOROUGH = "thorough"


class PluginConfig(BaseModel):
    """Strongly-typed configuration model using Pydantic.
    
    This demonstrates how to create robust configuration schemas
    with validation, defaults, and documentation.
    """
    
    # Required fields
    api_key: str = Field(
        description="API key for external service",
        min_length=10
    )
    
    # Optional fields with defaults
    mode: ProcessingMode = Field(
        default=ProcessingMode.BALANCED,
        description="Processing mode affecting speed vs accuracy"
    )
    
    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens to process",
        ge=1,
        le=10000
    )
    
    temperature: float = Field(
        default=0.7,
        description="Temperature for text generation",
        ge=0.0,
        le=2.0
    )
    
    enable_cache: bool = Field(
        default=True,
        description="Enable result caching"
    )
    
    cache_ttl: Optional[int] = Field(
        default=3600,
        description="Cache TTL in seconds",
        ge=0
    )
    
    custom_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers for API requests"
    )
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v.startswith(("sk-", "api-")):
            raise ValueError("API key must start with 'sk-' or 'api-'")
        return v
    
    @field_validator("cache_ttl")
    @classmethod
    def validate_cache_ttl(cls, v: Optional[int], info) -> Optional[int]:
        """Validate cache TTL only if cache is enabled."""
        if info.data.get("enable_cache") and v is None:
            return 3600  # Default TTL if cache enabled but TTL not specified
        return v


class ConfiguredPlugin(Plugin):
    """Plugin demonstrating advanced configuration patterns.
    
    This plugin shows how to:
    - Use Pydantic for configuration validation
    - Handle complex configuration scenarios
    - Provide meaningful error messages
    - Support configuration hot-reloading
    """
    
    supported_stages = ["PARSE", "THINK", "REVIEW"]
    
    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        """Initialize with validated configuration."""
        super().__init__(resources, config)
        
        # Parse and validate configuration
        try:
            self.plugin_config = PluginConfig(**self.config)
        except Exception as e:
            raise ValueError(f"Invalid plugin configuration: {e}")
        
        # Initialize cache if enabled
        self.cache = {} if self.plugin_config.enable_cache else None
        
        # Set up processing strategy based on mode
        self._setup_processing_strategy()
    
    def _setup_processing_strategy(self):
        """Configure processing based on selected mode."""
        strategies = {
            ProcessingMode.FAST: {
                "iterations": 1,
                "depth": "shallow",
                "timeout": 5.0
            },
            ProcessingMode.BALANCED: {
                "iterations": 3,
                "depth": "medium",
                "timeout": 15.0
            },
            ProcessingMode.THOROUGH: {
                "iterations": 5,
                "depth": "deep",
                "timeout": 30.0
            }
        }
        
        self.strategy = strategies[self.plugin_config.mode]
    
    async def execute(self, context: PluginContext) -> PluginContext:
        """Execute with configuration-driven behavior."""
        
        # Check cache if enabled
        if self.cache is not None:
            cache_key = self._get_cache_key(context)
            if cache_key in self.cache:
                context.metadata["cache_hit"] = True
                context.message = self.cache[cache_key]
                return context
        
        # Process based on configuration
        result = await self._process_with_strategy(context)
        
        # Update cache if enabled
        if self.cache is not None:
            cache_key = self._get_cache_key(context)
            self.cache[cache_key] = result
            
            # Schedule cache expiration
            if self.plugin_config.cache_ttl:
                # In production, use proper cache with TTL support
                pass
        
        context.message = result
        context.metadata["processing_mode"] = self.plugin_config.mode.value
        context.metadata["iterations_used"] = self.strategy["iterations"]
        
        return context
    
    async def _process_with_strategy(self, context: PluginContext) -> str:
        """Process message according to configured strategy."""
        result = context.message
        
        for i in range(self.strategy["iterations"]):
            # Simulate processing with configured parameters
            if self.strategy["depth"] == "deep":
                result = f"[Deep analysis {i+1}] {result}"
            elif self.strategy["depth"] == "medium":
                result = f"[Analysis {i+1}] {result}"
            else:
                result = f"[Quick {i+1}] {result}"
        
        return result
    
    def _get_cache_key(self, context: PluginContext) -> str:
        """Generate cache key from context."""
        # Simple cache key - in production, consider more factors
        return f"{context.stage}:{context.message[:100]}"
    
    def update_config(self, new_config: dict[str, Any]):
        """Support configuration hot-reloading.
        
        Args:
            new_config: New configuration dictionary
        """
        try:
            self.plugin_config = PluginConfig(**new_config)
            self._setup_processing_strategy()
            
            # Reset cache if cache settings changed
            if self.plugin_config.enable_cache and self.cache is None:
                self.cache = {}
            elif not self.plugin_config.enable_cache:
                self.cache = None
                
        except Exception as e:
            raise ValueError(f"Configuration update failed: {e}")
    
    def get_metrics(self) -> dict:
        """Return plugin metrics.
        
        Returns:
            Dictionary of current metrics
        """
        metrics = {
            "mode": self.plugin_config.mode.value,
            "cache_enabled": self.plugin_config.enable_cache,
            "cache_size": len(self.cache) if self.cache else 0,
            "max_tokens": self.plugin_config.max_tokens,
            "temperature": self.plugin_config.temperature
        }
        
        return metrics
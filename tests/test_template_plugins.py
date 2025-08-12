"""Tests for template plugin implementations."""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from entity_plugin_template import (
    AsyncPlugin,
    ConfiguredPlugin,
    SimplePlugin,
    StatefulPlugin,
)
from entity_plugin_template.configured_plugin import PluginConfig, ProcessingMode


class TestSimplePlugin:
    """Test the SimplePlugin template."""
    
    @pytest.fixture
    def resources(self):
        """Create mock resources."""
        return {
            "llm": MagicMock(),
            "memory": MagicMock()
        }
    
    @pytest.fixture
    def context(self):
        """Create mock context."""
        context = MagicMock()
        context.message = "Test message"
        context.stage = "INPUT"
        context.metadata = {}
        return context
    
    def test_initialization(self, resources):
        """Test plugin initialization."""
        plugin = SimplePlugin(resources, {"log_messages": True})
        assert plugin.log_messages is True
        assert plugin.prefix == "[SimplePlugin]"
    
    def test_initialization_with_defaults(self, resources):
        """Test initialization with default config."""
        plugin = SimplePlugin(resources, {})
        assert plugin.log_messages is False
        assert plugin.prefix == "[SimplePlugin]"
    
    @pytest.mark.asyncio
    async def test_execute_basic(self, resources, context):
        """Test basic execution."""
        plugin = SimplePlugin(resources, {})
        result = await plugin.execute(context)
        
        assert result.metadata["simple_plugin_executed"] is True
        assert result.message == "Test message"
    
    @pytest.mark.asyncio
    async def test_execute_with_prefix(self, resources, context):
        """Test execution with prefix addition."""
        plugin = SimplePlugin(resources, {"add_prefix": True, "prefix": "[TEST]"})
        result = await plugin.execute(context)
        
        assert result.message == "[TEST] Test message"
    
    def test_validation_valid(self, resources):
        """Test configuration validation with valid config."""
        plugin = SimplePlugin(resources, {"prefix": "test", "log_messages": True})
        assert plugin.validate() is True
    
    def test_validation_invalid_prefix(self, resources):
        """Test validation with invalid prefix type."""
        plugin = SimplePlugin(resources, {"prefix": 123})
        assert plugin.validate() is False
    
    def test_validation_invalid_log_messages(self, resources):
        """Test validation with invalid log_messages type."""
        plugin = SimplePlugin(resources, {"log_messages": "yes"})
        assert plugin.validate() is False


class TestAsyncPlugin:
    """Test the AsyncPlugin template."""
    
    @pytest.fixture
    def resources(self):
        """Create mock resources."""
        return {"llm": MagicMock()}
    
    @pytest.fixture
    def context(self):
        """Create mock context."""
        context = MagicMock()
        context.message = "Test query"
        context.stage = "THINK"
        context.metadata = {}
        return context
    
    def test_initialization(self, resources):
        """Test async plugin initialization."""
        plugin = AsyncPlugin(resources, {"timeout": 10.0, "max_retries": 5})
        assert plugin.timeout == 10.0
        assert plugin.max_retries == 5
        assert plugin.concurrent_limit == 5
    
    @pytest.mark.asyncio
    async def test_fetch_data(self, resources):
        """Test async data fetching."""
        plugin = AsyncPlugin(resources, {})
        result = await plugin._fetch_data("test query")
        
        assert result["query"] == "test query"
        assert "results" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, resources, context):
        """Test batch processing with concurrency."""
        plugin = AsyncPlugin(resources, {"enable_batch_processing": True})
        context.metadata["items"] = ["item1", "item2", "item3"]
        
        result = await plugin.execute(context)
        
        assert "batch_results" in result.metadata
        assert len(result.metadata["batch_results"]) == 3
        assert all(r.startswith("processed_") for r in result.metadata["batch_results"])
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, resources, context):
        """Test retry operation with failures."""
        plugin = AsyncPlugin(resources, {"enable_retry": True})
        
        result = await plugin.execute(context)
        
        assert "retry_success" in result.metadata
        assert result.metadata["retry_success"] is True
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, resources, context):
        """Test timeout handling."""
        plugin = AsyncPlugin(resources, {"timeout": 0.001})  # Very short timeout
        
        with patch.object(plugin, '_fetch_data', new_callable=AsyncMock) as mock_fetch:
            async def slow_fetch(query):
                await asyncio.sleep(1.0)
                return {"query": query}
            
            mock_fetch.side_effect = slow_fetch
            result = await plugin.execute(context)
            
            assert "fetch_error" in result.metadata
            assert result.metadata["fetch_error"] == "Operation timed out"


class TestConfiguredPlugin:
    """Test the ConfiguredPlugin template."""
    
    @pytest.fixture
    def resources(self):
        """Create mock resources."""
        return {"llm": MagicMock()}
    
    @pytest.fixture
    def context(self):
        """Create mock context."""
        context = MagicMock()
        context.message = "Test message"
        context.stage = "THINK"
        context.metadata = {}
        return context
    
    def test_config_validation_valid(self):
        """Test Pydantic config validation with valid data."""
        config = PluginConfig(
            api_key="sk-test123456",
            mode=ProcessingMode.FAST,
            max_tokens=500
        )
        
        assert config.api_key == "sk-test123456"
        assert config.mode == ProcessingMode.FAST
        assert config.max_tokens == 500
        assert config.temperature == 0.7  # Default
    
    def test_config_validation_invalid_api_key(self):
        """Test config validation with invalid API key."""
        with pytest.raises(ValidationError) as exc_info:
            PluginConfig(api_key="invalid")
        
        assert "API key must start with" in str(exc_info.value)
    
    def test_config_validation_invalid_temperature(self):
        """Test config validation with out-of-range temperature."""
        with pytest.raises(ValidationError) as exc_info:
            PluginConfig(api_key="sk-test123", temperature=3.0)
        
        assert "less than or equal to 2.0" in str(exc_info.value)
    
    def test_plugin_initialization(self, resources):
        """Test plugin initialization with config."""
        config = {
            "api_key": "sk-test123456",
            "mode": "thorough",
            "enable_cache": True
        }
        
        plugin = ConfiguredPlugin(resources, config)
        
        assert plugin.plugin_config.mode == ProcessingMode.THOROUGH
        assert plugin.cache is not None
        assert plugin.strategy["iterations"] == 5
    
    @pytest.mark.asyncio
    async def test_execute_with_cache(self, resources, context):
        """Test execution with caching enabled."""
        config = {
            "api_key": "sk-test123456",
            "enable_cache": True
        }
        
        plugin = ConfiguredPlugin(resources, config)
        
        # First execution
        result1 = await plugin.execute(context)
        assert "cache_hit" not in result1.metadata
        
        # Second execution with same context
        context.metadata = {}  # Reset metadata
        result2 = await plugin.execute(context)
        assert result2.metadata.get("cache_hit") is True
    
    def test_config_hot_reload(self, resources):
        """Test configuration hot-reloading."""
        initial_config = {
            "api_key": "sk-test123456",
            "mode": "fast"
        }
        
        plugin = ConfiguredPlugin(resources, initial_config)
        assert plugin.plugin_config.mode == ProcessingMode.FAST
        
        # Update configuration
        new_config = {
            "api_key": "api-newkey123",
            "mode": "thorough",
            "max_tokens": 2000
        }
        
        plugin.update_config(new_config)
        
        assert plugin.plugin_config.mode == ProcessingMode.THOROUGH
        assert plugin.plugin_config.max_tokens == 2000
        assert plugin.strategy["iterations"] == 5
    
    def test_get_metrics(self, resources):
        """Test metrics retrieval."""
        config = {
            "api_key": "sk-test123456",
            "mode": "balanced",
            "enable_cache": True
        }
        
        plugin = ConfiguredPlugin(resources, config)
        metrics = plugin.get_metrics()
        
        assert metrics["mode"] == "balanced"
        assert metrics["cache_enabled"] is True
        assert metrics["cache_size"] == 0
        assert metrics["temperature"] == 0.7


class TestStatefulPlugin:
    """Test the StatefulPlugin template."""
    
    @pytest.fixture
    def resources(self):
        """Create mock resources."""
        return {"llm": MagicMock()}
    
    @pytest.fixture
    def context(self):
        """Create mock context."""
        context = MagicMock()
        context.message = "Test message"
        context.stage = "THINK"
        context.metadata = {}
        return context
    
    def test_initialization(self, resources):
        """Test stateful plugin initialization."""
        plugin = StatefulPlugin(resources, {"max_history_size": 50})
        
        assert plugin.max_history_size == 50
        assert plugin.execution_count == 0
        assert len(plugin.conversation_history) == 0
        assert plugin.last_execution_time is None
    
    @pytest.mark.asyncio
    async def test_execution_tracking(self, resources, context):
        """Test execution count and history tracking."""
        plugin = StatefulPlugin(resources, {})
        
        # First execution
        result1 = await plugin.execute(context)
        assert result1.metadata["execution_count"] == 1
        assert result1.metadata["history_size"] == 1
        assert result1.metadata["time_since_last"] is None
        
        # Second execution
        await asyncio.sleep(0.1)  # Ensure time difference
        result2 = await plugin.execute(context)
        assert result2.metadata["execution_count"] == 2
        assert result2.metadata["history_size"] == 2
        assert result2.metadata["time_since_last"] > 0
    
    @pytest.mark.asyncio
    async def test_history_size_limit(self, resources, context):
        """Test conversation history size limiting."""
        plugin = StatefulPlugin(resources, {"max_history_size": 3})
        
        # Execute 5 times
        for i in range(5):
            context.message = f"Message {i}"
            await plugin.execute(context)
        
        # Should only keep last 3
        assert len(plugin.conversation_history) == 3
        assert plugin.conversation_history[0]["message"] == "Message 2"
        assert plugin.conversation_history[-1]["message"] == "Message 4"
    
    @pytest.mark.asyncio
    async def test_pattern_detection(self, resources, context):
        """Test pattern analysis in conversation history."""
        plugin = StatefulPlugin(resources, {})
        
        # Create repetitive pattern
        for i in range(3):
            context.message = "Same message"
            await plugin.execute(context)
        
        # Check for pattern detection
        result = await plugin.execute(context)
        patterns = result.metadata.get("detected_patterns", {})
        assert "repetitive_messages" in patterns
    
    @pytest.mark.asyncio
    async def test_context_switch_detection(self, resources, context):
        """Test context switch detection."""
        plugin = StatefulPlugin(resources, {})
        
        # Build history
        for i in range(3):
            context.message = f"Related message {i}"
            await plugin.execute(context)
        
        # Switch context
        context.message = "By the way, completely different topic"
        result = await plugin.execute(context)
        
        assert result.metadata.get("context_switch_detected") is True
        assert len(plugin.context_memory.get("context_switches", [])) == 1
    
    @pytest.mark.asyncio
    async def test_state_persistence(self, resources, context):
        """Test state saving and loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            # Create plugin with persistence
            plugin1 = StatefulPlugin(resources, {
                "enable_persistence": True,
                "state_file": state_file
            })
            
            # Execute a few times
            for i in range(3):
                context.message = f"Message {i}"
                await plugin1.execute(context)
            
            # Create new plugin instance that should load state
            plugin2 = StatefulPlugin(resources, {
                "enable_persistence": True,
                "state_file": state_file
            })
            
            # Check state was loaded
            assert plugin2.execution_count == 3
            assert len(plugin2.conversation_history) == 3
            assert plugin2.last_execution_time is not None
            
        finally:
            # Clean up
            os.unlink(state_file)
    
    def test_get_state_summary(self, resources):
        """Test state summary retrieval."""
        plugin = StatefulPlugin(resources, {})
        
        # Add some state
        plugin.execution_count = 5
        plugin.conversation_history = [{"message": "test"} for _ in range(3)]
        plugin.context_memory["test_key"] = "test_value"
        
        summary = plugin.get_state_summary()
        
        assert summary["execution_count"] == 5
        assert summary["history_size"] == 3
        assert "test_key" in summary["memory_keys"]
    
    def test_clear_state(self, resources):
        """Test state clearing."""
        plugin = StatefulPlugin(resources, {})
        
        # Add some state
        plugin.execution_count = 5
        plugin.conversation_history = [{"message": "test"}]
        plugin.context_memory["key"] = "value"
        
        # Clear state
        plugin.clear_state()
        
        assert plugin.execution_count == 0
        assert len(plugin.conversation_history) == 0
        assert len(plugin.context_memory) == 0
# Entity Plugin Template

A comprehensive template for creating Entity Framework plugins with best practices and examples.

## 🚀 Quick Start

Use this template to create your own Entity Framework plugin:

```bash
# Clone this template
git clone https://github.com/Ladvien/entity-plugin-template.git my-plugin
cd my-plugin

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## 📚 Template Plugins

This template includes four example plugin implementations demonstrating different patterns:

### 1. SimplePlugin
**Location:** `src/entity_plugin_template/simple_plugin.py`

A minimal plugin showing the basic structure:
- Basic initialization and configuration
- Simple message processing
- Configuration validation
- Metadata tracking

```python
from entity_plugin_template import SimplePlugin

plugin = SimplePlugin(
    resources={"llm": llm_client},
    config={
        "log_messages": True,
        "prefix": "[MyApp]"
    }
)
```

### 2. AsyncPlugin
**Location:** `src/entity_plugin_template/async_plugin.py`

Demonstrates async operations and external API integration:
- Async/await patterns
- Timeout handling
- Concurrent operations with rate limiting
- Retry logic with exponential backoff
- Batch processing

```python
from entity_plugin_template import AsyncPlugin

plugin = AsyncPlugin(
    resources={"llm": llm_client},
    config={
        "timeout": 30.0,
        "max_retries": 3,
        "concurrent_limit": 5,
        "enable_batch_processing": True
    }
)
```

### 3. ConfiguredPlugin
**Location:** `src/entity_plugin_template/configured_plugin.py`

Shows advanced configuration with Pydantic:
- Strongly-typed configuration with validation
- Enum-based modes
- Caching implementation
- Configuration hot-reloading
- Metrics collection

```python
from entity_plugin_template import ConfiguredPlugin

plugin = ConfiguredPlugin(
    resources={"llm": llm_client},
    config={
        "api_key": "sk-your-api-key",
        "mode": "balanced",  # fast, balanced, thorough
        "max_tokens": 1000,
        "temperature": 0.7,
        "enable_cache": True,
        "cache_ttl": 3600
    }
)

# Hot-reload configuration
plugin.update_config({"mode": "thorough"})

# Get metrics
metrics = plugin.get_metrics()
```

### 4. StatefulPlugin
**Location:** `src/entity_plugin_template/stateful_plugin.py`

Demonstrates state management across executions:
- Conversation history tracking
- Pattern detection
- Context switch detection
- State persistence to disk
- Memory management

```python
from entity_plugin_template import StatefulPlugin

plugin = StatefulPlugin(
    resources={"llm": llm_client},
    config={
        "max_history_size": 100,
        "enable_persistence": True,
        "state_file": "plugin_state.json"
    }
)

# Get state summary
summary = plugin.get_state_summary()

# Clear state
plugin.clear_state()
```

## 🏗️ Creating Your Own Plugin

### Step 1: Choose a Template
Select the template that best matches your needs:
- **SimplePlugin** - For basic transformations and filters
- **AsyncPlugin** - For plugins that call external APIs
- **ConfiguredPlugin** - For plugins with complex configuration
- **StatefulPlugin** - For plugins that need memory/history

### Step 2: Copy and Rename
```bash
cp src/entity_plugin_template/simple_plugin.py src/entity_plugin_template/my_plugin.py
```

### Step 3: Implement Your Logic

```python
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext

class MyCustomPlugin(Plugin):
    """Your plugin description."""
    
    supported_stages = ["THINK", "DO"]  # Stages where plugin runs
    
    def __init__(self, resources, config=None):
        super().__init__(resources, config)
        # Your initialization
    
    async def execute(self, context: PluginContext) -> PluginContext:
        # Your plugin logic
        context.message = self.process(context.message)
        return context
    
    def process(self, message: str) -> str:
        # Your processing logic
        return message.upper()
```

### Step 4: Add Tests
Create tests for your plugin in `tests/`:

```python
import pytest
from entity_plugin_template import MyCustomPlugin

class TestMyCustomPlugin:
    def test_initialization(self):
        plugin = MyCustomPlugin({}, {"setting": "value"})
        assert plugin.config["setting"] == "value"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        plugin = MyCustomPlugin({}, {})
        context = create_mock_context("hello")
        result = await plugin.execute(context)
        assert result.message == "HELLO"
```

### Step 5: Update Package Exports
Edit `src/entity_plugin_template/__init__.py`:

```python
from .my_plugin import MyCustomPlugin

__all__ = [
    # ... existing exports ...
    "MyCustomPlugin",
]
```

## 📋 Plugin Best Practices

### 1. Configuration
- Use Pydantic for complex configuration
- Provide sensible defaults
- Validate configuration in `__init__`
- Document all configuration options

### 2. Error Handling
- Never let exceptions escape `execute()`
- Log errors appropriately
- Provide fallback behavior
- Add error details to context metadata

### 3. Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Respect rate limits
- Add timeouts to external calls

### 4. State Management
- Minimize stateful behavior
- Use context metadata for passing data
- Clean up resources properly
- Consider thread safety

### 5. Testing
- Test all configuration options
- Test error conditions
- Mock external dependencies
- Test async behavior

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=entity_plugin_template

# Run specific test file
pytest tests/test_template_plugins.py

# Run specific test
pytest tests/test_template_plugins.py::TestSimplePlugin::test_initialization
```

## 📖 Documentation

### Plugin Lifecycle

1. **Initialization** - Plugin is created with resources and config
2. **Validation** - Configuration is validated
3. **Registration** - Plugin is registered with workflow
4. **Execution** - Plugin processes messages in its stages
5. **Cleanup** - Plugin releases resources

### Context Object

The `PluginContext` passed to `execute()` contains:
- `message`: The current message being processed
- `stage`: Current workflow stage
- `metadata`: Dictionary for passing data between plugins
- `resources`: Shared resources (LLM, memory, etc.)

### Supported Stages

Plugins can support these workflow stages:
- `INPUT` - Initial message processing
- `PARSE` - Message parsing and understanding
- `THINK` - Reasoning and planning
- `DO` - Action execution
- `REVIEW` - Result review and validation
- `OUTPUT` - Final output formatting

## 🤝 Contributing

To contribute a new template plugin:

1. Create your plugin in `src/entity_plugin_template/`
2. Add comprehensive tests in `tests/`
3. Update this README with documentation
4. Submit a pull request

## 📦 Publishing Your Plugin

When you're ready to publish your plugin:

1. Update `pyproject.toml` with your package details
2. Build the package: `python -m build`
3. Upload to PyPI: `twine upload dist/*`

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Resources

- [Entity Framework Documentation](https://github.com/Ladvien/entity)
- [Plugin Development Guide](https://github.com/Ladvien/entity/docs/plugins.md)
- [Entity Core API Reference](https://github.com/Ladvien/entity-core)
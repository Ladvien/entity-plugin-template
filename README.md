# Entity Plugin Template

Create Entity plugins fast. Four patterns included.

## Quick Start

```bash
git clone https://github.com/Ladvien/entity-plugin-template.git my-plugin
cd my-plugin
pip install -e ".[dev]"
pytest
```

## Template Patterns

### 1. SimplePlugin
Basic message processing
```python
plugin = SimplePlugin(resources, {"prefix": "[App]"})
```

### 2. AsyncPlugin  
External APIs, retries, batching
```python
plugin = AsyncPlugin(resources, {
    "timeout": 30,
    "max_retries": 3,
    "concurrent_limit": 5
})
```

### 3. ConfiguredPlugin
Pydantic config, caching, metrics
```python
plugin = ConfiguredPlugin(resources, {
    "mode": "balanced",  # fast|balanced|thorough
    "enable_cache": True
})
```

### 4. StatefulPlugin
History, persistence, patterns
```python
plugin = StatefulPlugin(resources, {
    "max_history": 100,
    "state_file": "state.json"
})
```

## Create Your Plugin

```python
from entity.plugins.base import Plugin

class MyPlugin(Plugin):
    supported_stages = ["think", "do"]
    
    async def _execute_impl(self, context):
        # Your logic
        return f"Processed: {context.message}"
```

## Test It

```python
import pytest

@pytest.mark.asyncio
async def test_my_plugin():
    plugin = MyPlugin({}, {})
    context = Mock(message="test")
    result = await plugin.execute(context)
    assert "Processed" in result.message
```

## Workflow Stages

- `INPUT` - Accept data
- `PARSE` - Extract meaning  
- `THINK` - Plan approach
- `DO` - Execute actions
- `REVIEW` - Validate results
- `OUTPUT` - Format response

## Best Practices

```python
# ✅ DO
- Validate config in __init__
- Use async for I/O
- Handle errors gracefully
- Add timeouts
- Test everything

# ❌ DON'T
- Let exceptions escape
- Block the event loop
- Store secrets in config
- Forget cleanup
```

## Publish

```bash
python -m build
twine upload dist/*
```

## Resources

- [Entity Docs](https://github.com/Ladvien/entity)
- [Plugin Guide](https://github.com/Ladvien/entity/docs/plugins.md)
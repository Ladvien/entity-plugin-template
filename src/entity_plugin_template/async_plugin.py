"""Async Plugin Template - Demonstrates async operations in plugins."""

from __future__ import annotations

import asyncio
from typing import Any

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext


class AsyncPlugin(Plugin):
    """Plugin template showing async operations and external API calls.
    
    This plugin demonstrates how to:
    - Make async API calls
    - Handle timeouts
    - Process results asynchronously
    - Manage concurrent operations
    """
    
    supported_stages = ["THINK", "DO"]
    
    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        """Initialize the async plugin."""
        super().__init__(resources, config)
        
        # Configuration for async operations
        self.timeout = self.config.get("timeout", 30.0)
        self.max_retries = self.config.get("max_retries", 3)
        self.concurrent_limit = self.config.get("concurrent_limit", 5)
    
    async def execute(self, context: PluginContext) -> PluginContext:
        """Execute async operations.
        
        This method demonstrates various async patterns commonly used in plugins.
        """
        # Example 1: Simple async operation with timeout
        try:
            result = await asyncio.wait_for(
                self._fetch_data(context.message),
                timeout=self.timeout
            )
            context.metadata["fetch_result"] = result
        except asyncio.TimeoutError:
            context.metadata["fetch_error"] = "Operation timed out"
        
        # Example 2: Concurrent operations with semaphore
        if self.config.get("enable_batch_processing", False):
            items = context.metadata.get("items", [])
            results = await self._process_batch(items)
            context.metadata["batch_results"] = results
        
        # Example 3: Retry logic for unreliable operations
        if self.config.get("enable_retry", False):
            success = await self._retry_operation(context)
            context.metadata["retry_success"] = success
        
        return context
    
    async def _fetch_data(self, query: str) -> dict:
        """Simulate an async API call.
        
        Args:
            query: The query string
            
        Returns:
            Simulated API response
        """
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Return mock data
        return {
            "query": query,
            "results": ["result1", "result2"],
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def _process_batch(self, items: list) -> list:
        """Process multiple items concurrently with rate limiting.
        
        Args:
            items: List of items to process
            
        Returns:
            List of processed results
        """
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def process_item(item):
            async with semaphore:
                # Simulate processing
                await asyncio.sleep(0.05)
                return f"processed_{item}"
        
        # Process all items concurrently
        tasks = [process_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _retry_operation(self, context: PluginContext) -> bool:
        """Demonstrate retry logic with exponential backoff.
        
        Args:
            context: Plugin context
            
        Returns:
            True if operation succeeded, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # Simulate an operation that might fail
                if attempt < 2:  # Fail first two attempts
                    await asyncio.sleep(0.1)
                    raise ConnectionError("Simulated failure")
                
                # Success on third attempt
                await asyncio.sleep(0.1)
                return True
                
            except ConnectionError as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt * 0.1
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    context.metadata["retry_error"] = str(e)
                    return False
        
        return False
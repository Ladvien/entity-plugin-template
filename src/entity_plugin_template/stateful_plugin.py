"""Stateful Plugin Template - Demonstrates state management in plugins."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext


class StatefulPlugin(Plugin):
    """Plugin demonstrating state management patterns.
    
    This plugin shows how to:
    - Maintain state across executions
    - Track conversation history
    - Implement memory patterns
    - Handle state persistence
    """
    
    supported_stages = ["THINK", "REVIEW"]
    
    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        """Initialize with state management."""
        super().__init__(resources, config)
        
        # Initialize state containers
        self.conversation_history: list[dict] = []
        self.context_memory: dict[str, Any] = {}
        self.execution_count = 0
        self.last_execution_time: Optional[datetime] = None
        
        # Configuration
        self.max_history_size = self.config.get("max_history_size", 100)
        self.enable_persistence = self.config.get("enable_persistence", False)
        self.state_file = self.config.get("state_file", "plugin_state.json")
        
        # Load persisted state if enabled
        if self.enable_persistence:
            self._load_state()
    
    async def execute(self, context: PluginContext) -> PluginContext:
        """Execute with state tracking."""
        
        # Update execution metrics
        self.execution_count += 1
        current_time = datetime.now()
        time_since_last = None
        
        if self.last_execution_time:
            time_since_last = (current_time - self.last_execution_time).total_seconds()
        
        self.last_execution_time = current_time
        
        # Add to conversation history
        history_entry = {
            "timestamp": current_time.isoformat(),
            "message": context.message,
            "stage": context.stage,
            "execution_number": self.execution_count,
            "metadata": dict(context.metadata)
        }
        
        self.conversation_history.append(history_entry)
        
        # Maintain history size limit
        if len(self.conversation_history) > self.max_history_size:
            self.conversation_history.pop(0)
        
        # Extract and store context information
        self._update_context_memory(context)
        
        # Add state information to context
        context.metadata["execution_count"] = self.execution_count
        context.metadata["history_size"] = len(self.conversation_history)
        context.metadata["time_since_last"] = time_since_last
        
        # Analyze patterns in history
        patterns = self._analyze_patterns()
        if patterns:
            context.metadata["detected_patterns"] = patterns
        
        # Check for context switches
        if self._detect_context_switch(context):
            context.metadata["context_switch_detected"] = True
            self._handle_context_switch(context)
        
        # Persist state if enabled
        if self.enable_persistence:
            self._save_state()
        
        return context
    
    def _update_context_memory(self, context: PluginContext):
        """Update context memory with relevant information."""
        
        # Extract entities, topics, or other relevant information
        # This is a simplified example - real implementation would use NLP
        
        # Track message length patterns
        if "message_lengths" not in self.context_memory:
            self.context_memory["message_lengths"] = []
        
        self.context_memory["message_lengths"].append(len(context.message))
        
        # Keep only recent lengths
        if len(self.context_memory["message_lengths"]) > 50:
            self.context_memory["message_lengths"].pop(0)
        
        # Track stage transitions
        if "stage_transitions" not in self.context_memory:
            self.context_memory["stage_transitions"] = []
        
        if self.context_memory["stage_transitions"]:
            last_stage = self.context_memory["stage_transitions"][-1]
            if last_stage != context.stage:
                self.context_memory["stage_transitions"].append(context.stage)
        else:
            self.context_memory["stage_transitions"].append(context.stage)
    
    def _analyze_patterns(self) -> dict:
        """Analyze patterns in conversation history."""
        patterns = {}
        
        if len(self.conversation_history) < 3:
            return patterns
        
        # Check for repetitive messages
        recent_messages = [h["message"] for h in self.conversation_history[-5:]]
        if len(recent_messages) == len(set(recent_messages)):
            patterns["unique_messages"] = True
        else:
            patterns["repetitive_messages"] = True
        
        # Check message length trends
        if "message_lengths" in self.context_memory:
            lengths = self.context_memory["message_lengths"]
            if len(lengths) >= 3:
                recent_avg = sum(lengths[-3:]) / 3
                overall_avg = sum(lengths) / len(lengths)
                
                if recent_avg > overall_avg * 1.5:
                    patterns["increasing_length"] = True
                elif recent_avg < overall_avg * 0.5:
                    patterns["decreasing_length"] = True
        
        # Check for rapid executions
        if len(self.conversation_history) >= 2:
            last_two = self.conversation_history[-2:]
            time1 = datetime.fromisoformat(last_two[0]["timestamp"])
            time2 = datetime.fromisoformat(last_two[1]["timestamp"])
            time_diff = (time2 - time1).total_seconds()
            
            if time_diff < 1.0:
                patterns["rapid_execution"] = True
        
        return patterns
    
    def _detect_context_switch(self, context: PluginContext) -> bool:
        """Detect if there's been a context switch."""
        
        if len(self.conversation_history) < 2:
            return False
        
        # Simple heuristic - check if message is very different from recent history
        current_msg = context.message.lower()
        recent_msgs = [h["message"].lower() for h in self.conversation_history[-3:]]
        
        # Check for topic change indicators
        switch_indicators = ["new topic", "different question", "change subject", "anyway", "by the way"]
        
        for indicator in switch_indicators:
            if indicator in current_msg:
                return True
        
        # Check for significant length difference
        if recent_msgs:
            avg_recent_length = sum(len(m) for m in recent_msgs) / len(recent_msgs)
            if abs(len(current_msg) - avg_recent_length) > avg_recent_length * 0.8:
                return True
        
        return False
    
    def _handle_context_switch(self, context: PluginContext):
        """Handle a detected context switch."""
        
        # Save current context to history
        if "context_switches" not in self.context_memory:
            self.context_memory["context_switches"] = []
        
        self.context_memory["context_switches"].append({
            "timestamp": datetime.now().isoformat(),
            "previous_context_size": len(self.conversation_history),
            "trigger_message": context.message[:100]
        })
        
        # Optionally clear some state
        if self.config.get("clear_on_context_switch", False):
            self.conversation_history = self.conversation_history[-10:]  # Keep only recent
    
    def _save_state(self):
        """Persist state to file."""
        try:
            state = {
                "execution_count": self.execution_count,
                "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
                "conversation_history": self.conversation_history[-20:],  # Save only recent
                "context_memory": self.context_memory
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            # Log error but don't fail execution
            print(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load persisted state from file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.execution_count = state.get("execution_count", 0)
            
            if state.get("last_execution_time"):
                self.last_execution_time = datetime.fromisoformat(state["last_execution_time"])
            
            self.conversation_history = state.get("conversation_history", [])
            self.context_memory = state.get("context_memory", {})
            
        except FileNotFoundError:
            # No state file yet, start fresh
            pass
        except Exception as e:
            # Log error but don't fail initialization
            print(f"Failed to load state: {e}")
    
    def get_state_summary(self) -> dict:
        """Get a summary of current state.
        
        Returns:
            Dictionary containing state summary
        """
        return {
            "execution_count": self.execution_count,
            "history_size": len(self.conversation_history),
            "context_switches": len(self.context_memory.get("context_switches", [])),
            "last_execution": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "memory_keys": list(self.context_memory.keys())
        }
    
    def clear_state(self):
        """Clear all state."""
        self.conversation_history = []
        self.context_memory = {}
        self.execution_count = 0
        self.last_execution_time = None
        
        if self.enable_persistence:
            self._save_state()
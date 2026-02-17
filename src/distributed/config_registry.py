"""
Global Config Registry

Unified configuration management across repositories.
Provides centralized config with validation and change tracking.
"""

import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from collections import defaultdict
import copy
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """Represents a configuration change."""
    key: str
    old_value: Any
    new_value: Any
    timestamp: float
    source: str


class GlobalConfigRegistry:
    """
    Unified configuration management across repositories.
    
    Features:
    - Hierarchical configuration with namespaces
    - Type validation
    - Change tracking and rollback
    - Config watchers/callbacks
    - Thread-safe access
    
    Example:
        registry = GlobalConfigRegistry()
        
        # Set configuration
        registry.set('ouroboros.thread.max_workers', 10, source='config_file')
        
        # Get configuration with default
        max_workers = registry.get('ouroboros.thread.max_workers', default=5)
        
        # Watch for changes
        registry.watch('ouroboros.thread.*', callback=on_config_change)
    """
    
    def __init__(self):
        """Initialize config registry."""
        self._config: Dict[str, Any] = {}
        self._validators: Dict[str, Callable] = {}
        self._watchers: Dict[str, List[Callable]] = defaultdict(list)
        self._changes: List[ConfigChange] = []
        
        self._lock = threading.Lock()
        
        # Statistics
        self._get_count = 0
        self._set_count = 0
        self._validation_failures = 0
    
    def set(
        self,
        key: str,
        value: Any,
        source: str = 'unknown',
    ) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (dot-separated path)
            value: Configuration value
            source: Source of the change
            
        Returns:
            True if set successfully
        """
        import time
        
        with self._lock:
            # Validate if validator exists
            if key in self._validators:
                try:
                    if not self._validators[key](value):
                        logger.error(f"Validation failed for {key} = {value}")
                        self._validation_failures += 1
                        return False
                except Exception as e:
                    logger.error(f"Validator error for {key}: {e}")
                    self._validation_failures += 1
                    return False
            
            # Store old value
            old_value = self._config.get(key)
            
            # Set new value
            self._config[key] = value
            
            # Record change
            change = ConfigChange(
                key=key,
                old_value=old_value,
                new_value=value,
                timestamp=time.time(),
                source=source,
            )
            self._changes.append(change)
            
            self._set_count += 1
        
        # Notify watchers (outside lock to avoid deadlock)
        self._notify_watchers(key, old_value, value)
        
        logger.debug(f"Set config {key} = {value} (source: {source})")
        return True
    
    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self._lock:
            self._get_count += 1
            return self._config.get(key, default)
    
    def get_all(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all configuration values, optionally filtered by prefix.
        
        Args:
            prefix: Key prefix filter
            
        Returns:
            Dictionary of configuration values
        """
        with self._lock:
            if prefix is None:
                return copy.deepcopy(self._config)
            
            return {
                key: copy.deepcopy(value)
                for key, value in self._config.items()
                if key.startswith(prefix)
            }
    
    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.
        
        Args:
            key: Configuration key
            
        Returns:
            True if deleted
        """
        with self._lock:
            if key not in self._config:
                return False
            
            old_value = self._config[key]
            del self._config[key]
            
            # Record change
            import time
            change = ConfigChange(
                key=key,
                old_value=old_value,
                new_value=None,
                timestamp=time.time(),
                source='delete',
            )
            self._changes.append(change)
        
        # Notify watchers
        self._notify_watchers(key, old_value, None)
        
        logger.debug(f"Deleted config key {key}")
        return True
    
    def register_validator(
        self,
        key: str,
        validator: Callable[[Any], bool],
    ) -> None:
        """
        Register a validator for a config key.
        
        Args:
            key: Configuration key
            validator: Validation function (returns True if valid)
        """
        with self._lock:
            self._validators[key] = validator
        
        logger.debug(f"Registered validator for {key}")
    
    def watch(
        self,
        pattern: str,
        callback: Callable[[str, Any, Any], None],
    ) -> None:
        """
        Watch for configuration changes.
        
        Args:
            pattern: Key pattern to watch (supports * wildcard)
            callback: Function called on change (key, old_value, new_value)
        """
        with self._lock:
            self._watchers[pattern].append(callback)
        
        logger.debug(f"Registered watcher for pattern {pattern}")
    
    def _notify_watchers(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """
        Notify watchers of a config change.
        
        Args:
            key: Changed key
            old_value: Old value
            new_value: New value
        """
        # Get matching watchers
        matching_watchers = []
        
        with self._lock:
            for pattern, callbacks in self._watchers.items():
                if self._match_pattern(key, pattern):
                    matching_watchers.extend(callbacks)
        
        # Call watchers
        for callback in matching_watchers:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Watcher error for {key}: {e}")
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """
        Check if a key matches a pattern.
        
        Args:
            key: Configuration key
            pattern: Pattern (supports * wildcard)
            
        Returns:
            True if matches
        """
        # Simple wildcard matching
        if '*' not in pattern:
            return key == pattern
        
        # Split on wildcard
        parts = pattern.split('*')
        
        # Check prefix and suffix
        if not key.startswith(parts[0]):
            return False
        
        if not key.endswith(parts[-1]):
            return False
        
        return True
    
    def get_changes(
        self,
        since_timestamp: Optional[float] = None,
        key_prefix: Optional[str] = None,
    ) -> List[ConfigChange]:
        """
        Get configuration change history.
        
        Args:
            since_timestamp: Only return changes after this time
            key_prefix: Only return changes for keys with this prefix
            
        Returns:
            List of ConfigChange objects
        """
        with self._lock:
            changes = self._changes.copy()
        
        # Filter by timestamp
        if since_timestamp is not None:
            changes = [
                c for c in changes
                if c.timestamp >= since_timestamp
            ]
        
        # Filter by key prefix
        if key_prefix is not None:
            changes = [
                c for c in changes
                if c.key.startswith(key_prefix)
            ]
        
        return changes
    
    def rollback(self, to_timestamp: float) -> int:
        """
        Rollback configuration to a previous state.
        
        Args:
            to_timestamp: Timestamp to rollback to
            
        Returns:
            Number of keys rolled back
        """
        rolled_back = 0
        
        with self._lock:
            # Find changes after timestamp
            changes_to_undo = [
                c for c in reversed(self._changes)
                if c.timestamp > to_timestamp
            ]
            
            # Undo changes
            for change in changes_to_undo:
                if change.key in self._config:
                    if change.old_value is None:
                        # Key was added, remove it
                        del self._config[change.key]
                    else:
                        # Key was changed, restore old value
                        self._config[change.key] = change.old_value
                    rolled_back += 1
        
        logger.info(f"Rolled back {rolled_back} configuration keys")
        return rolled_back
    
    def get_statistics(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                'total_keys': len(self._config),
                'total_validators': len(self._validators),
                'total_watchers': sum(len(w) for w in self._watchers.values()),
                'total_changes': len(self._changes),
                'get_count': self._get_count,
                'set_count': self._set_count,
                'validation_failures': self._validation_failures,
            }

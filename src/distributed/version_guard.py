"""
API Version Guard

Automatic message adaptation for API version compatibility.
Ensures cross-repo communication remains compatible across versions.
"""

import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """API version information."""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'VersionInfo') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    @classmethod
    def parse(cls, version_str: str) -> 'VersionInfo':
        """Parse version string like '1.2.3'."""
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]),
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
        )


class APIVersionGuard:
    """
    Automatic message adaptation for API compatibility.
    
    Features:
    - Version compatibility checking
    - Automatic message transformation
    - Backward and forward compatibility
    - Deprecation warnings
    - Migration helpers
    
    Example:
        guard = APIVersionGuard()
        
        # Register current API version
        guard.register_api('ouroboros', '2.0.0')
        
        # Register adapter for old version
        guard.register_adapter(
            'ouroboros',
            from_version='1.0.0',
            to_version='2.0.0',
            adapter=migrate_v1_to_v2
        )
        
        # Adapt message
        adapted = guard.adapt_message(
            message,
            from_api='ouroboros',
            from_version='1.0.0'
        )
    """
    
    def __init__(self):
        """Initialize version guard."""
        self._apis: Dict[str, VersionInfo] = {}
        self._adapters: Dict[tuple, Callable] = {}
        self._deprecations: Dict[tuple, str] = {}
        
        self._lock = threading.Lock()
        
        # Statistics
        self._adaptations = 0
        self._warnings_issued = 0
    
    def register_api(
        self,
        api_name: str,
        version: str,
    ) -> None:
        """
        Register an API version.
        
        Args:
            api_name: Name of the API
            version: Version string (e.g., '1.2.3')
        """
        version_info = VersionInfo.parse(version)
        
        with self._lock:
            self._apis[api_name] = version_info
        
        logger.info(f"Registered API {api_name} version {version_info}")
    
    def register_adapter(
        self,
        api_name: str,
        from_version: str,
        to_version: str,
        adapter: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Register a version adapter.
        
        Args:
            api_name: Name of the API
            from_version: Source version
            to_version: Target version
            adapter: Function to adapt messages
        """
        from_info = VersionInfo.parse(from_version)
        to_info = VersionInfo.parse(to_version)
        
        key = (api_name, str(from_info), str(to_info))
        
        with self._lock:
            self._adapters[key] = adapter
        
        logger.info(
            f"Registered adapter for {api_name}: "
            f"{from_info} -> {to_info}"
        )
    
    def mark_deprecated(
        self,
        api_name: str,
        version: str,
        message: str = "This API version is deprecated",
    ) -> None:
        """
        Mark an API version as deprecated.
        
        Args:
            api_name: Name of the API
            version: Deprecated version
            message: Deprecation message
        """
        version_info = VersionInfo.parse(version)
        key = (api_name, str(version_info))
        
        with self._lock:
            self._deprecations[key] = message
        
        logger.info(f"Marked {api_name} {version_info} as deprecated")
    
    def check_compatibility(
        self,
        api_name: str,
        requested_version: str,
    ) -> bool:
        """
        Check if a requested version is compatible.
        
        Args:
            api_name: Name of the API
            requested_version: Requested version
            
        Returns:
            True if compatible
        """
        if api_name not in self._apis:
            logger.warning(f"Unknown API: {api_name}")
            return False
        
        requested = VersionInfo.parse(requested_version)
        current = self._apis[api_name]
        
        # Compatible if major version matches and minor/patch <= current
        if requested.major != current.major:
            return False
        
        return requested <= current
    
    def adapt_message(
        self,
        message: Dict[str, Any],
        from_api: str,
        from_version: str,
        to_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adapt a message to a different API version.
        
        Args:
            message: Message to adapt
            from_api: Source API name
            from_version: Source version
            to_version: Target version (current if None)
            
        Returns:
            Adapted message
        """
        with self._lock:
            # Get target version
            if to_version is None:
                if from_api not in self._apis:
                    logger.warning(f"Unknown API {from_api}, returning original message")
                    return message
                to_version = str(self._apis[from_api])
            
            from_info = VersionInfo.parse(from_version)
            to_info = VersionInfo.parse(to_version)
            
            # Check for deprecation
            dep_key = (from_api, str(from_info))
            if dep_key in self._deprecations:
                logger.warning(
                    f"Using deprecated API: {from_api} {from_info}. "
                    f"{self._deprecations[dep_key]}"
                )
                self._warnings_issued += 1
            
            # If same version, no adaptation needed
            if from_info == to_info:
                return message
            
            # Try direct adapter
            adapter_key = (from_api, str(from_info), str(to_info))
            if adapter_key in self._adapters:
                adapted = self._adapters[adapter_key](message)
                self._adaptations += 1
                logger.debug(f"Adapted message from {from_info} to {to_info}")
                return adapted
            
            # Try multi-hop adaptation
            adapted = self._multi_hop_adapt(
                message, from_api, from_info, to_info
            )
            
            if adapted is not message:
                self._adaptations += 1
                return adapted
            
            logger.warning(
                f"No adapter found for {from_api}: {from_info} -> {to_info}"
            )
            return message
    
    def _multi_hop_adapt(
        self,
        message: Dict[str, Any],
        api_name: str,
        from_version: VersionInfo,
        to_version: VersionInfo,
    ) -> Dict[str, Any]:
        """
        Attempt multi-hop adaptation through intermediate versions.
        
        Args:
            message: Message to adapt
            api_name: API name
            from_version: Source version
            to_version: Target version
            
        Returns:
            Adapted message (or original if no path found)
        """
        # Try to find path through intermediate versions
        # This is a simplified version - a full implementation would use
        # graph search to find optimal adaptation path
        
        current = message
        current_version = from_version
        
        # Try incremental version upgrades
        while current_version < to_version:
            # Try next minor version
            next_version = VersionInfo(
                major=current_version.major,
                minor=current_version.minor + 1,
                patch=0,
            )
            
            if next_version > to_version:
                # Try to go directly to target
                next_version = to_version
            
            adapter_key = (
                api_name,
                str(current_version),
                str(next_version),
            )
            
            if adapter_key in self._adapters:
                current = self._adapters[adapter_key](current)
                current_version = next_version
                logger.debug(f"Multi-hop: adapted to {current_version}")
            else:
                # No path found
                return message
        
        return current
    
    def get_statistics(self) -> Dict:
        """
        Get version guard statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                'registered_apis': len(self._apis),
                'registered_adapters': len(self._adapters),
                'deprecations': len(self._deprecations),
                'total_adaptations': self._adaptations,
                'warnings_issued': self._warnings_issued,
            }

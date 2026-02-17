"""
UTe2 Hybrid System - Persistent Caching Module

Provides local caching for simulation results to accelerate repeated calculations.
Supports compression, TTL, and parameter-based hashing.
"""

import os
import json
import hashlib
import pickle
import gzip
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SimulationCache:
    """Persistent cache for UTe2 simulation results"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cache system
        
        Args:
            config: Cache configuration dictionary
        """
        self.config = config.get('cache', {})
        self.enabled = self.config.get('enabled', True)
        self.storage_path = Path(self.config.get('storage_path', './ute2_cache'))
        self.max_size_mb = self.config.get('max_size_mb', 500)
        self.ttl_days = self.config.get('ttl_days', 30)
        self.compression = self.config.get('compression', True)
        self.hash_params = self.config.get('strategy', {}).get('hash_parameters', [])
        
        # Create cache directory
        if self.enabled:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._cleanup_expired()
            logger.info(f"Cache initialized at {self.storage_path}")
    
    def _generate_key(self, parameters: Dict[str, Any]) -> str:
        """
        Generate cache key from simulation parameters
        
        Args:
            parameters: Simulation parameters dictionary
            
        Returns:
            Hash string for cache key
        """
        # Extract relevant parameters for hashing
        relevant_params = {
            k: v for k, v in parameters.items()
            if k in self.hash_params or not self.hash_params
        }
        
        # Sort keys for consistent hashing
        param_str = json.dumps(relevant_params, sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for given key"""
        return self.storage_path / f"{key}.cache"
    
    def _get_metadata_file(self, key: str) -> Path:
        """Get metadata file path for given key"""
        return self.storage_path / f"{key}.meta"
    
    def get(self, parameters: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve cached result if available
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            Cached result or None if not found/expired
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(parameters)
        cache_file = self._get_cache_file(key)
        meta_file = self._get_metadata_file(key)
        
        if not cache_file.exists() or not meta_file.exists():
            logger.debug(f"Cache miss for key {key[:8]}...")
            return None
        
        # Check metadata and TTL
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            
            created = datetime.fromisoformat(metadata['created'])
            expires = created + timedelta(days=self.ttl_days)
            
            if datetime.now() > expires:
                logger.debug(f"Cache expired for key {key[:8]}...")
                self._delete_entry(key)
                return None
            
            # Load cached data
            with open(cache_file, 'rb') as f:
                data = f.read()
            
            if self.compression:
                data = gzip.decompress(data)
            
            result = pickle.loads(data)
            logger.info(f"Cache hit for key {key[:8]}...")
            
            # Update access time
            metadata['last_accessed'] = datetime.now().isoformat()
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
            self._delete_entry(key)
            return None
    
    def put(self, parameters: Dict[str, Any], result: Any) -> bool:
        """
        Store result in cache
        
        Args:
            parameters: Simulation parameters
            result: Result to cache
            
        Returns:
            True if successfully cached
        """
        if not self.enabled:
            return False
        
        key = self._generate_key(parameters)
        cache_file = self._get_cache_file(key)
        meta_file = self._get_metadata_file(key)
        
        try:
            # Serialize result
            data = pickle.dumps(result)
            
            if self.compression:
                data = gzip.compress(data)
            
            # Check size limits
            data_size_mb = len(data) / (1024 * 1024)
            if data_size_mb > self.max_size_mb / 10:  # Single entry max 10% of total
                logger.warning(f"Result too large to cache: {data_size_mb:.2f} MB")
                return False
            
            # Ensure cache size limit
            self._ensure_size_limit(data_size_mb)
            
            # Write cache file
            with open(cache_file, 'wb') as f:
                f.write(data)
            
            # Write metadata
            metadata = {
                'key': key,
                'created': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'parameters': parameters,
                'size_mb': data_size_mb,
                'access_count': 0
            }
            
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Cached result for key {key[:8]}... ({data_size_mb:.2f} MB)")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")
            return False
    
    def _delete_entry(self, key: str):
        """Delete cache entry and its metadata"""
        cache_file = self._get_cache_file(key)
        meta_file = self._get_metadata_file(key)
        
        try:
            if cache_file.exists():
                cache_file.unlink()
            if meta_file.exists():
                meta_file.unlink()
        except Exception as e:
            logger.warning(f"Error deleting cache entry: {e}")
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        if not self.enabled:
            return
        
        count = 0
        for meta_file in self.storage_path.glob("*.meta"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                created = datetime.fromisoformat(metadata['created'])
                expires = created + timedelta(days=self.ttl_days)
                
                if datetime.now() > expires:
                    key = meta_file.stem
                    self._delete_entry(key)
                    count += 1
            except Exception as e:
                logger.warning(f"Error checking expiry: {e}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")
    
    def _ensure_size_limit(self, new_size_mb: float):
        """Ensure cache stays within size limit, evict oldest if needed"""
        current_size = self.get_cache_size_mb()
        
        if current_size + new_size_mb <= self.max_size_mb:
            return
        
        # Get all entries sorted by last access time
        entries = []
        for meta_file in self.storage_path.glob("*.meta"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                    entries.append((
                        meta_file.stem,
                        datetime.fromisoformat(metadata.get('last_accessed', metadata['created'])),
                        metadata.get('size_mb', 0)
                    ))
            except Exception:
                pass
        
        # Sort by access time (oldest first)
        entries.sort(key=lambda x: x[1])
        
        # Evict oldest until we have space
        freed_mb = 0
        for key, _, size_mb in entries:
            if current_size - freed_mb + new_size_mb <= self.max_size_mb:
                break
            
            self._delete_entry(key)
            freed_mb += size_mb
            logger.debug(f"Evicted cache entry {key[:8]}... ({size_mb:.2f} MB)")
    
    def get_cache_size_mb(self) -> float:
        """Get total cache size in MB"""
        total = 0
        for cache_file in self.storage_path.glob("*.cache"):
            total += cache_file.stat().st_size
        return total / (1024 * 1024)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        entries = list(self.storage_path.glob("*.meta"))
        
        total_accesses = 0
        for meta_file in entries:
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                    total_accesses += metadata.get('access_count', 0)
            except Exception:
                pass
        
        return {
            'enabled': self.enabled,
            'total_entries': len(entries),
            'total_size_mb': self.get_cache_size_mb(),
            'max_size_mb': self.max_size_mb,
            'total_accesses': total_accesses,
            'storage_path': str(self.storage_path)
        }
    
    def clear(self):
        """Clear all cache entries"""
        if not self.enabled:
            return
        
        count = 0
        for cache_file in self.storage_path.glob("*"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Error clearing cache: {e}")
        
        logger.info(f"Cleared {count} cache files")

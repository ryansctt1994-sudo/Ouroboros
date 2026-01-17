"""
L-Sharded Index for Fast Lookups

Implements sharded hash-based indexing for fast file lookups
with distributed hash table principles.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
import hashlib


@dataclass
class IndexEntry:
    """Entry in the sharded index."""
    key: str
    value: Any
    metadata: Dict[str, Any]


class LShardedIndex:
    """
    L-sharded index for fast lookups.
    
    Distributes keys across L shards using consistent hashing
    for balanced distribution and fast access.
    """
    
    def __init__(self, num_shards: int = 16, hash_algorithm: str = 'sha256'):
        """
        Initialize L-sharded index.
        
        Args:
            num_shards: Number of shards (L parameter)
            hash_algorithm: Hashing algorithm for shard selection
        """
        self.num_shards = num_shards
        self.hash_algorithm = hash_algorithm
        
        # Shard storage
        self.shards: List[Dict[str, IndexEntry]] = [
            {} for _ in range(num_shards)
        ]
        
        # Global key tracking
        self.all_keys: Set[str] = set()
        
        # Statistics
        self.total_entries = 0
        self.lookup_count = 0
        self.hit_count = 0
    
    def _compute_shard_id(self, key: str) -> int:
        """
        Compute shard ID for a key using consistent hashing.
        
        Args:
            key: Key to shard
            
        Returns:
            Shard ID (0 to num_shards-1)
        """
        # Compute hash
        if self.hash_algorithm == 'sha256':
            hash_bytes = hashlib.sha256(key.encode()).digest()
        elif self.hash_algorithm == 'sha1':
            hash_bytes = hashlib.sha1(key.encode()).digest()
        elif self.hash_algorithm == 'md5':
            hash_bytes = hashlib.md5(key.encode()).digest()
        else:
            hash_bytes = hashlib.sha256(key.encode()).digest()
        
        # Convert first 4 bytes to integer
        hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        
        # Modulo to get shard ID
        shard_id = hash_int % self.num_shards
        
        return shard_id
    
    def put(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Insert or update entry in index.
        
        Args:
            key: Lookup key
            value: Value to store
            metadata: Optional metadata
            
        Returns:
            True if new entry, False if update
        """
        shard_id = self._compute_shard_id(key)
        shard = self.shards[shard_id]
        
        is_new = key not in shard
        
        entry = IndexEntry(
            key=key,
            value=value,
            metadata=metadata or {}
        )
        
        shard[key] = entry
        
        if is_new:
            self.all_keys.add(key)
            self.total_entries += 1
        
        return is_new
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value for key.
        
        Args:
            key: Lookup key
            
        Returns:
            Value or None if not found
        """
        self.lookup_count += 1
        
        shard_id = self._compute_shard_id(key)
        shard = self.shards[shard_id]
        
        if key in shard:
            self.hit_count += 1
            return shard[key].value
        
        return None
    
    def get_entry(self, key: str) -> Optional[IndexEntry]:
        """
        Retrieve full index entry for key.
        
        Args:
            key: Lookup key
            
        Returns:
            IndexEntry or None if not found
        """
        shard_id = self._compute_shard_id(key)
        shard = self.shards[shard_id]
        
        return shard.get(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from index.
        
        Args:
            key: Key to delete
            
        Returns:
            True if deleted, False if not found
        """
        shard_id = self._compute_shard_id(key)
        shard = self.shards[shard_id]
        
        if key in shard:
            del shard[key]
            self.all_keys.discard(key)
            self.total_entries -= 1
            return True
        
        return False
    
    def contains(self, key: str) -> bool:
        """
        Check if key exists in index.
        
        Args:
            key: Key to check
            
        Returns:
            True if exists, False otherwise
        """
        return key in self.all_keys
    
    def get_shard_distribution(self) -> List[int]:
        """
        Get distribution of entries across shards.
        
        Returns:
            List of entry counts per shard
        """
        return [len(shard) for shard in self.shards]
    
    def find_by_prefix(self, prefix: str) -> List[str]:
        """
        Find all keys with given prefix.
        
        Args:
            prefix: Key prefix
            
        Returns:
            List of matching keys
        """
        matching_keys = []
        
        # Search all shards
        for shard in self.shards:
            for key in shard.keys():
                if key.startswith(prefix):
                    matching_keys.append(key)
        
        return matching_keys
    
    def range_query(self, start_key: str, end_key: str) -> List[str]:
        """
        Find all keys in lexicographic range.
        
        Args:
            start_key: Start of range (inclusive)
            end_key: End of range (inclusive)
            
        Returns:
            List of keys in range
        """
        matching_keys = []
        
        for shard in self.shards:
            for key in shard.keys():
                if start_key <= key <= end_key:
                    matching_keys.append(key)
        
        return sorted(matching_keys)
    
    def clear(self):
        """Clear all entries from index."""
        for shard in self.shards:
            shard.clear()
        
        self.all_keys.clear()
        self.total_entries = 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Statistics dictionary
        """
        distribution = self.get_shard_distribution()
        
        # Calculate load balance metrics
        if distribution:
            max_load = max(distribution)
            min_load = min(distribution)
            avg_load = sum(distribution) / len(distribution)
            load_imbalance = (max_load - min_load) / avg_load if avg_load > 0 else 0.0
        else:
            max_load = min_load = avg_load = load_imbalance = 0.0
        
        # Calculate hit rate
        hit_rate = self.hit_count / self.lookup_count if self.lookup_count > 0 else 0.0
        
        return {
            'total_entries': self.total_entries,
            'num_shards': self.num_shards,
            'shard_distribution': distribution,
            'max_shard_load': max_load,
            'min_shard_load': min_load,
            'avg_shard_load': avg_load,
            'load_imbalance': load_imbalance,
            'total_lookups': self.lookup_count,
            'total_hits': self.hit_count,
            'hit_rate': hit_rate
        }
    
    def rebalance(self, new_num_shards: int) -> 'LShardedIndex':
        """
        Create a rebalanced index with different number of shards.
        
        Args:
            new_num_shards: New number of shards
            
        Returns:
            New rebalanced index
        """
        new_index = LShardedIndex(
            num_shards=new_num_shards,
            hash_algorithm=self.hash_algorithm
        )
        
        # Migrate all entries
        for shard in self.shards:
            for entry in shard.values():
                new_index.put(entry.key, entry.value, entry.metadata)
        
        return new_index

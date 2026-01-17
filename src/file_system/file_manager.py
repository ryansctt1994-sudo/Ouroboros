"""
Enhanced File Manager

Integrates deduplication and sharded indexing for high-performance file management.
"""

from typing import Dict, Any, Optional, List
import time

from .deduplication import ContentDeduplicator
from .sharded_index import LShardedIndex


class EnhancedFileManager:
    """
    Enhanced file manager with deduplication and fast lookups.
    
    Combines content deduplication with L-sharded indexing for
    efficient storage and fast access.
    """
    
    def __init__(
        self,
        block_size: int = 4096,
        num_shards: int = 16,
        enable_deduplication: bool = True
    ):
        """
        Initialize enhanced file manager.
        
        Args:
            block_size: Deduplication block size
            num_shards: Number of index shards
            enable_deduplication: Enable content deduplication
        """
        self.enable_deduplication = enable_deduplication
        
        # Core components
        if enable_deduplication:
            self.deduplicator = ContentDeduplicator(block_size=block_size)
        else:
            self.deduplicator = None
        
        self.index = LShardedIndex(num_shards=num_shards)
        
        # File storage (if dedup disabled)
        self.file_store: Dict[str, bytes] = {}
        
        # File metadata
        self.file_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Access statistics
        self.access_counts: Dict[str, int] = {}
        self.last_access: Dict[str, float] = {}
    
    def store_file(
        self,
        file_id: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store file with optional deduplication.
        
        Args:
            file_id: Unique file identifier
            content: File content
            metadata: Optional file metadata
            
        Returns:
            Storage result with statistics
        """
        start_time = time.time()
        
        result = {
            'file_id': file_id,
            'success': False,
            'original_size': len(content),
            'stored_size': len(content)
        }
        
        try:
            if self.enable_deduplication and self.deduplicator is not None:
                # Store with deduplication
                dedup_metadata = self.deduplicator.store_file(file_id, content)
                result['stored_size'] = dedup_metadata.deduplicated_size
                result['compression_ratio'] = dedup_metadata.compression_ratio
                result['block_count'] = len(dedup_metadata.block_hashes)
            else:
                # Store without deduplication
                self.file_store[file_id] = content
            
            # Add to index
            self.index.put(file_id, {
                'size': len(content),
                'timestamp': start_time,
                'metadata': metadata or {}
            })
            
            # Update metadata
            self.file_metadata[file_id] = metadata or {}
            
            # Update access tracking
            self.access_counts[file_id] = 0
            self.last_access[file_id] = start_time
            
            result['success'] = True
            result['storage_time_ms'] = (time.time() - start_time) * 1000
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def retrieve_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve file content.
        
        Args:
            file_id: File identifier
            
        Returns:
            File content or None if not found
        """
        # Update access tracking
        if file_id in self.access_counts:
            self.access_counts[file_id] += 1
            self.last_access[file_id] = time.time()
        
        # Retrieve from deduplicator or store
        if self.enable_deduplication and self.deduplicator is not None:
            return self.deduplicator.retrieve_file(file_id)
        else:
            return self.file_store.get(file_id)
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file.
        
        Args:
            file_id: File identifier
            
        Returns:
            True if deleted, False if not found
        """
        # Delete from deduplicator or store
        if self.enable_deduplication and self.deduplicator is not None:
            success = self.deduplicator.delete_file(file_id)
        else:
            if file_id in self.file_store:
                del self.file_store[file_id]
                success = True
            else:
                success = False
        
        # Remove from index
        self.index.delete(file_id)
        
        # Remove metadata and tracking
        self.file_metadata.pop(file_id, None)
        self.access_counts.pop(file_id, None)
        self.last_access.pop(file_id, None)
        
        return success
    
    def file_exists(self, file_id: str) -> bool:
        """Check if file exists."""
        return self.index.contains(file_id)
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata."""
        return self.file_metadata.get(file_id)
    
    def find_similar_files(self, file_id: str) -> List[str]:
        """
        Find files with shared content blocks.
        
        Args:
            file_id: File identifier
            
        Returns:
            List of similar file IDs
        """
        if self.enable_deduplication and self.deduplicator is not None:
            return self.deduplicator.find_duplicates(file_id)
        return []
    
    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all files or files with given prefix.
        
        Args:
            prefix: Optional file ID prefix
            
        Returns:
            List of file IDs
        """
        if prefix:
            return self.index.find_by_prefix(prefix)
        else:
            return list(self.file_metadata.keys())
    
    def get_most_accessed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently accessed files.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of file access statistics
        """
        sorted_files = sorted(
            self.access_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = []
        for file_id, count in sorted_files[:limit]:
            results.append({
                'file_id': file_id,
                'access_count': count,
                'last_access': self.last_access.get(file_id, 0.0)
            })
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get file manager statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_files': len(self.file_metadata),
            'index_stats': self.index.get_statistics()
        }
        
        if self.enable_deduplication and self.deduplicator is not None:
            stats['deduplication_stats'] = self.deduplicator.get_statistics()
        else:
            total_size = sum(len(content) for content in self.file_store.values())
            stats['total_storage_bytes'] = total_size
            stats['total_storage_mb'] = total_size / (1024 * 1024)
        
        # Access statistics
        if self.access_counts:
            total_accesses = sum(self.access_counts.values())
            avg_accesses = total_accesses / len(self.access_counts)
        else:
            total_accesses = avg_accesses = 0
        
        stats['access_stats'] = {
            'total_accesses': total_accesses,
            'avg_accesses_per_file': avg_accesses,
            'unique_accessed_files': len(self.access_counts)
        }
        
        return stats

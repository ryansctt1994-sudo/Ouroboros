"""
Enhanced File System Layer with Deduplication and L-Sharded Lookups

Provides advanced file system capabilities including content-based deduplication,
hash-based indexing, and L-sharded lookup for fast access.
"""

from .deduplication import ContentDeduplicator
from .sharded_index import LShardedIndex
from .file_manager import EnhancedFileManager

__all__ = [
    'ContentDeduplicator',
    'LShardedIndex',
    'EnhancedFileManager'
]

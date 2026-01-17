"""
Content-Based Deduplication System

Implements content-based deduplication using cryptographic hashing
and reference counting for efficient storage.
"""

import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ContentBlock:
    """Represents a deduplicated content block."""
    hash: str
    size: int
    reference_count: int
    content: bytes
    
    def add_reference(self):
        """Increment reference count."""
        self.reference_count += 1
    
    def remove_reference(self):
        """Decrement reference count."""
        self.reference_count = max(0, self.reference_count - 1)


@dataclass
class FileMetadata:
    """Metadata for a deduplicated file."""
    file_id: str
    original_size: int
    deduplicated_size: int
    block_hashes: List[str]
    compression_ratio: float


class ContentDeduplicator:
    """
    Content-based deduplication engine.
    
    Splits content into blocks, computes hashes, and maintains
    reference counts for shared blocks.
    """
    
    def __init__(self, block_size: int = 4096, hash_algorithm: str = 'sha256'):
        """
        Initialize content deduplicator.
        
        Args:
            block_size: Size of content blocks in bytes
            hash_algorithm: Hashing algorithm to use
        """
        self.block_size = block_size
        self.hash_algorithm = hash_algorithm
        
        # Content block store
        self.blocks: Dict[str, ContentBlock] = {}
        
        # File metadata
        self.files: Dict[str, FileMetadata] = {}
        
        # Hash to file mappings
        self.hash_to_files: Dict[str, Set[str]] = defaultdict(set)
        
        # Statistics
        self.total_original_size = 0
        self.total_deduplicated_size = 0
        self.dedup_operations = 0
    
    def _compute_hash(self, data: bytes) -> str:
        """
        Compute cryptographic hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hexadecimal hash string
        """
        if self.hash_algorithm == 'sha256':
            return hashlib.sha256(data).hexdigest()
        elif self.hash_algorithm == 'sha1':
            return hashlib.sha1(data).hexdigest()
        elif self.hash_algorithm == 'md5':
            return hashlib.md5(data).hexdigest()
        else:
            return hashlib.sha256(data).hexdigest()
    
    def _split_into_blocks(self, content: bytes) -> List[bytes]:
        """
        Split content into fixed-size blocks.
        
        Args:
            content: Content to split
            
        Returns:
            List of content blocks
        """
        blocks = []
        offset = 0
        
        while offset < len(content):
            block = content[offset:offset + self.block_size]
            blocks.append(block)
            offset += self.block_size
        
        return blocks
    
    def store_file(self, file_id: str, content: bytes) -> FileMetadata:
        """
        Store file with deduplication.
        
        Args:
            file_id: Unique file identifier
            content: File content
            
        Returns:
            File metadata with deduplication info
        """
        # Split into blocks
        blocks = self._split_into_blocks(content)
        
        block_hashes = []
        deduplicated_size = 0
        
        for block in blocks:
            # Compute hash
            block_hash = self._compute_hash(block)
            block_hashes.append(block_hash)
            
            # Check if block exists
            if block_hash in self.blocks:
                # Block already exists, increment reference
                self.blocks[block_hash].add_reference()
            else:
                # New block, store it
                content_block = ContentBlock(
                    hash=block_hash,
                    size=len(block),
                    reference_count=1,
                    content=block
                )
                self.blocks[block_hash] = content_block
                deduplicated_size += len(block)
            
            # Track hash-to-file mapping
            self.hash_to_files[block_hash].add(file_id)
        
        # Create file metadata
        original_size = len(content)
        compression_ratio = (
            1.0 - (deduplicated_size / original_size)
            if original_size > 0 else 0.0
        )
        
        metadata = FileMetadata(
            file_id=file_id,
            original_size=original_size,
            deduplicated_size=deduplicated_size,
            block_hashes=block_hashes,
            compression_ratio=compression_ratio
        )
        
        self.files[file_id] = metadata
        
        # Update statistics
        self.total_original_size += original_size
        self.total_deduplicated_size += deduplicated_size
        self.dedup_operations += 1
        
        return metadata
    
    def retrieve_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve file content from deduplicated blocks.
        
        Args:
            file_id: File identifier
            
        Returns:
            Reconstructed file content or None if not found
        """
        if file_id not in self.files:
            return None
        
        metadata = self.files[file_id]
        content_parts = []
        
        for block_hash in metadata.block_hashes:
            if block_hash in self.blocks:
                content_parts.append(self.blocks[block_hash].content)
            else:
                # Block missing, cannot reconstruct
                return None
        
        return b''.join(content_parts)
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file and clean up unreferenced blocks.
        
        Args:
            file_id: File identifier
            
        Returns:
            True if deleted, False if not found
        """
        if file_id not in self.files:
            return False
        
        metadata = self.files[file_id]
        
        # Decrement reference counts
        blocks_to_delete = []
        for block_hash in metadata.block_hashes:
            if block_hash in self.blocks:
                self.blocks[block_hash].remove_reference()
                
                # Mark for deletion if no more references
                if self.blocks[block_hash].reference_count == 0:
                    blocks_to_delete.append(block_hash)
            
            # Remove from hash-to-file mapping
            self.hash_to_files[block_hash].discard(file_id)
        
        # Delete unreferenced blocks
        for block_hash in blocks_to_delete:
            del self.blocks[block_hash]
        
        # Delete file metadata
        del self.files[file_id]
        
        return True
    
    def find_duplicates(self, file_id: str) -> List[str]:
        """
        Find files that share blocks with given file.
        
        Args:
            file_id: File identifier
            
        Returns:
            List of file IDs sharing blocks
        """
        if file_id not in self.files:
            return []
        
        metadata = self.files[file_id]
        duplicate_files = set()
        
        for block_hash in metadata.block_hashes:
            if block_hash in self.hash_to_files:
                duplicate_files.update(self.hash_to_files[block_hash])
        
        # Remove the file itself
        duplicate_files.discard(file_id)
        
        return list(duplicate_files)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.
        
        Returns:
            Statistics dictionary
        """
        total_blocks = len(self.blocks)
        total_files = len(self.files)
        
        # Calculate space savings
        if self.total_original_size > 0:
            space_savings_ratio = (
                1.0 - (self.total_deduplicated_size / self.total_original_size)
            )
        else:
            space_savings_ratio = 0.0
        
        return {
            'total_files': total_files,
            'total_blocks': total_blocks,
            'total_original_size_bytes': self.total_original_size,
            'total_deduplicated_size_bytes': self.total_deduplicated_size,
            'space_savings_ratio': space_savings_ratio,
            'space_savings_mb': (self.total_original_size - self.total_deduplicated_size) / (1024 * 1024),
            'dedup_operations': self.dedup_operations,
            'avg_block_size': self.block_size
        }

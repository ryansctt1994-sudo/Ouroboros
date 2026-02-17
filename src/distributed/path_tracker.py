"""
Critical Path Tracker

End-to-end latency monitoring for distributed operations.
Tracks critical path through multi-repo workflows.
"""

import time
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """Represents a span in distributed tracing."""
    span_id: str
    parent_id: Optional[str]
    operation: str
    start_time: float
    end_time: Optional[float]
    tags: Dict[str, str]
    repo: str
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


@dataclass
class CriticalPath:
    """Critical path analysis result."""
    total_latency_ms: float
    path: List[Span]
    bottleneck_span: Span
    repos_involved: Set[str]
    
    
class CriticalPathTracker:
    """
    End-to-end latency monitoring for distributed operations.
    
    Tracks execution spans across multiple repositories and identifies
    critical paths and bottlenecks.
    
    Features:
    - Distributed tracing with parent-child relationships
    - Critical path identification
    - Bottleneck detection
    - Cross-repo latency tracking
    - Real-time monitoring
    
    Example:
        tracker = CriticalPathTracker()
        
        # Start operation
        span_id = tracker.start_span(
            'process_request',
            repo='ouroboros',
            tags={'request_id': 'req-123'}
        )
        
        # Do work...
        
        # End operation
        tracker.end_span(span_id)
        
        # Analyze critical path
        path = tracker.get_critical_path(span_id)
    """
    
    def __init__(
        self,
        max_spans: int = 10000,
        retention_seconds: float = 3600.0,
    ):
        """
        Initialize critical path tracker.
        
        Args:
            max_spans: Maximum number of spans to retain
            retention_seconds: How long to keep completed spans
        """
        self.max_spans = max_spans
        self.retention_seconds = retention_seconds
        
        self._spans: Dict[str, Span] = {}
        self._children: Dict[str, List[str]] = defaultdict(list)
        self._completed_spans: deque = deque(maxlen=max_spans)
        
        self._lock = threading.Lock()
        self._span_counter = 0
        
        # Statistics
        self._total_spans = 0
        self._active_spans = 0
        
    def start_span(
        self,
        operation: str,
        repo: str,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Start a new span.
        
        Args:
            operation: Operation name
            repo: Repository name
            parent_id: Parent span ID
            tags: Optional tags/metadata
            
        Returns:
            Span ID
        """
        if tags is None:
            tags = {}
        
        with self._lock:
            self._span_counter += 1
            span_id = f"span_{self._span_counter}"
            
            span = Span(
                span_id=span_id,
                parent_id=parent_id,
                operation=operation,
                start_time=time.time(),
                end_time=None,
                tags=tags,
                repo=repo,
            )
            
            self._spans[span_id] = span
            
            if parent_id:
                self._children[parent_id].append(span_id)
            
            self._total_spans += 1
            self._active_spans += 1
        
        logger.debug(f"Started span {span_id}: {operation} in {repo}")
        return span_id
    
    def end_span(self, span_id: str) -> None:
        """
        End a span.
        
        Args:
            span_id: Span identifier
        """
        with self._lock:
            if span_id not in self._spans:
                logger.warning(f"Span {span_id} not found")
                return
            
            span = self._spans[span_id]
            span.end_time = time.time()
            
            # Move to completed
            self._completed_spans.append(span)
            self._active_spans -= 1
        
        logger.debug(
            f"Ended span {span_id}: {span.operation} "
            f"({span.duration_ms:.2f} ms)"
        )
    
    def add_tag(self, span_id: str, key: str, value: str) -> None:
        """
        Add a tag to a span.
        
        Args:
            span_id: Span identifier
            key: Tag key
            value: Tag value
        """
        with self._lock:
            if span_id in self._spans:
                self._spans[span_id].tags[key] = value
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """
        Get a span by ID.
        
        Args:
            span_id: Span identifier
            
        Returns:
            Span if found, None otherwise
        """
        with self._lock:
            return self._spans.get(span_id)
    
    def get_critical_path(self, root_span_id: str) -> Optional[CriticalPath]:
        """
        Identify the critical path from a root span.
        
        The critical path is the longest sequential path through the
        span tree.
        
        Args:
            root_span_id: Root span identifier
            
        Returns:
            CriticalPath analysis or None if not found
        """
        with self._lock:
            if root_span_id not in self._spans:
                return None
            
            # Build path using DFS
            def find_longest_path(span_id: str) -> List[Span]:
                if span_id not in self._spans:
                    return []
                
                span = self._spans[span_id]
                children = self._children.get(span_id, [])
                
                if not children:
                    return [span]
                
                # Find longest child path
                longest_child_path = []
                max_duration = 0.0
                
                for child_id in children:
                    child_path = find_longest_path(child_id)
                    if child_path:
                        child_duration = sum(
                            s.duration_ms or 0 for s in child_path
                        )
                        if child_duration > max_duration:
                            max_duration = child_duration
                            longest_child_path = child_path
                
                return [span] + longest_child_path
            
            path = find_longest_path(root_span_id)
            
            if not path:
                return None
            
            # Calculate total latency
            total_latency = sum(s.duration_ms or 0 for s in path)
            
            # Find bottleneck (span with longest duration)
            bottleneck = max(
                path,
                key=lambda s: s.duration_ms or 0
            )
            
            # Collect repos involved
            repos = {s.repo for s in path}
        
        return CriticalPath(
            total_latency_ms=total_latency,
            path=path,
            bottleneck_span=bottleneck,
            repos_involved=repos,
        )
    
    def get_cross_repo_latency(self) -> Dict[Tuple[str, str], List[float]]:
        """
        Get latency statistics for cross-repo calls.
        
        Returns:
            Dictionary mapping (from_repo, to_repo) to list of latencies
        """
        cross_repo_latencies = defaultdict(list)
        
        with self._lock:
            for span in self._completed_spans:
                if span.parent_id and span.parent_id in self._spans:
                    parent = self._spans[span.parent_id]
                    
                    if parent.repo != span.repo and span.duration_ms:
                        key = (parent.repo, span.repo)
                        cross_repo_latencies[key].append(span.duration_ms)
        
        return dict(cross_repo_latencies)
    
    def cleanup_old_spans(self) -> int:
        """
        Clean up old completed spans.
        
        Returns:
            Number of spans cleaned up
        """
        current_time = time.time()
        cleaned = 0
        
        with self._lock:
            # Clean up completed spans
            to_remove = []
            for span in list(self._completed_spans):
                if span.end_time:
                    age = current_time - span.end_time
                    if age > self.retention_seconds:
                        to_remove.append(span)
            
            for span in to_remove:
                self._completed_spans.remove(span)
                if span.span_id in self._spans:
                    del self._spans[span.span_id]
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old spans")
        
        return cleaned
    
    def get_statistics(self) -> Dict:
        """
        Get tracker statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                'total_spans': self._total_spans,
                'active_spans': self._active_spans,
                'completed_spans': len(self._completed_spans),
            }

"""
Failure Correlator

Cross-repo error cascade detection and analysis.
Identifies and correlates failures across distributed systems.
"""

import time
import threading
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class FailureEvent:
    """Represents a failure event."""
    event_id: str
    repo: str
    component: str
    error_type: str
    message: str
    timestamp: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    tags: Dict[str, str]
    
    
@dataclass
class FailureCascade:
    """Represents a correlated failure cascade."""
    cascade_id: str
    root_cause: FailureEvent
    related_failures: List[FailureEvent]
    repos_affected: Set[str]
    total_failures: int
    duration_seconds: float
    severity: str


class FailureCorrelator:
    """
    Cross-repo error cascade detection and analysis.
    
    Features:
    - Temporal correlation of failures
    - Root cause identification
    - Cascade pattern detection
    - Cross-repo failure tracking
    - Impact analysis
    
    Example:
        correlator = FailureCorrelator()
        
        # Report failure
        correlator.report_failure(
            repo='ouroboros',
            component='thread_manager',
            error_type='ZombieThreadError',
            message='Thread cleanup failed',
            severity='high'
        )
        
        # Detect cascades
        cascades = correlator.detect_cascades()
        for cascade in cascades:
            print(f"Root cause: {cascade.root_cause.message}")
            print(f"Affected repos: {cascade.repos_affected}")
    """
    
    def __init__(
        self,
        correlation_window_seconds: float = 60.0,
        cascade_threshold: int = 3,
        retention_seconds: float = 3600.0,
    ):
        """
        Initialize failure correlator.
        
        Args:
            correlation_window_seconds: Time window for correlating failures
            cascade_threshold: Minimum failures to consider a cascade
            retention_seconds: How long to keep failure events
        """
        self.correlation_window = correlation_window_seconds
        self.cascade_threshold = cascade_threshold
        self.retention_seconds = retention_seconds
        
        self._events: deque = deque()
        self._cascades: List[FailureCascade] = []
        self._event_counter = 0
        
        self._lock = threading.Lock()
        
        # Statistics
        self._total_failures = 0
        self._total_cascades = 0
        
    def report_failure(
        self,
        repo: str,
        component: str,
        error_type: str,
        message: str,
        severity: str = 'medium',
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Report a failure event.
        
        Args:
            repo: Repository name
            component: Component name
            error_type: Type of error
            message: Error message
            severity: Severity level
            tags: Optional tags/metadata
            
        Returns:
            Event ID
        """
        if tags is None:
            tags = {}
        
        with self._lock:
            self._event_counter += 1
            event_id = f"failure_{self._event_counter}"
            
            event = FailureEvent(
                event_id=event_id,
                repo=repo,
                component=component,
                error_type=error_type,
                message=message,
                timestamp=time.time(),
                severity=severity,
                tags=tags,
            )
            
            self._events.append(event)
            self._total_failures += 1
        
        logger.warning(
            f"Failure reported in {repo}/{component}: "
            f"{error_type} - {message}"
        )
        
        return event_id
    
    def detect_cascades(self) -> List[FailureCascade]:
        """
        Detect failure cascades.
        
        Returns:
            List of detected cascades
        """
        current_time = time.time()
        cascades = []
        
        with self._lock:
            # Clean up old events
            self._cleanup_old_events(current_time)
            
            # Group events by time window
            time_groups = self._group_by_time_window()
            
            # Analyze each group for cascades
            for window_start, events in time_groups.items():
                if len(events) >= self.cascade_threshold:
                    cascade = self._analyze_cascade(events, window_start)
                    if cascade:
                        cascades.append(cascade)
                        if cascade not in self._cascades:
                            self._cascades.append(cascade)
                            self._total_cascades += 1
        
        return cascades
    
    def _group_by_time_window(self) -> Dict[float, List[FailureEvent]]:
        """
        Group events by time window.
        
        Returns:
            Dictionary mapping window start to events
        """
        groups = defaultdict(list)
        
        for event in self._events:
            # Round down to window boundary
            window_start = (
                int(event.timestamp / self.correlation_window) *
                self.correlation_window
            )
            groups[window_start].append(event)
        
        return groups
    
    def _analyze_cascade(
        self,
        events: List[FailureEvent],
        window_start: float,
    ) -> Optional[FailureCascade]:
        """
        Analyze a group of events for cascade patterns.
        
        Args:
            events: List of events in time window
            window_start: Start of time window
            
        Returns:
            FailureCascade if detected, None otherwise
        """
        if len(events) < self.cascade_threshold:
            return None
        
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # First event is potential root cause
        root_cause = sorted_events[0]
        
        # Check for temporal correlation
        related = []
        for event in sorted_events[1:]:
            time_diff = event.timestamp - root_cause.timestamp
            
            if time_diff <= self.correlation_window:
                # Check for related error types or components
                if self._are_related(root_cause, event):
                    related.append(event)
        
        if len(related) < self.cascade_threshold - 1:
            return None
        
        # Calculate cascade properties
        all_events = [root_cause] + related
        repos_affected = {e.repo for e in all_events}
        duration = sorted_events[-1].timestamp - root_cause.timestamp
        
        # Determine overall severity
        severity_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        max_severity_val = max(
            severity_levels.get(e.severity, 1) for e in all_events
        )
        severity = next(
            k for k, v in severity_levels.items()
            if v == max_severity_val
        )
        
        cascade_id = f"cascade_{int(window_start)}_{root_cause.event_id}"
        
        return FailureCascade(
            cascade_id=cascade_id,
            root_cause=root_cause,
            related_failures=related,
            repos_affected=repos_affected,
            total_failures=len(all_events),
            duration_seconds=duration,
            severity=severity,
        )
    
    def _are_related(
        self,
        event1: FailureEvent,
        event2: FailureEvent,
    ) -> bool:
        """
        Check if two failure events are related.
        
        Args:
            event1: First event
            event2: Second event
            
        Returns:
            True if events appear related
        """
        # Same error type is strongly related
        if event1.error_type == event2.error_type:
            return True
        
        # Same component across repos
        if event1.component == event2.component:
            return True
        
        # Check for common tags
        common_tags = set(event1.tags.keys()) & set(event2.tags.keys())
        if common_tags:
            for tag in common_tags:
                if event1.tags[tag] == event2.tags[tag]:
                    return True
        
        # Check message similarity (simple keyword matching)
        words1 = set(event1.message.lower().split())
        words2 = set(event2.message.lower().split())
        common_words = words1 & words2
        
        # If they share significant words, consider related
        if len(common_words) >= 2:
            return True
        
        return False
    
    def _cleanup_old_events(self, current_time: float) -> None:
        """
        Remove old failure events.
        
        Args:
            current_time: Current timestamp
        """
        cutoff = current_time - self.retention_seconds
        
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()
    
    def get_failure_rate(
        self,
        repo: Optional[str] = None,
        window_seconds: float = 300.0,
    ) -> float:
        """
        Calculate failure rate.
        
        Args:
            repo: Optional repo filter
            window_seconds: Time window in seconds
            
        Returns:
            Failures per second
        """
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        with self._lock:
            recent_failures = [
                e for e in self._events
                if e.timestamp >= cutoff and
                (repo is None or e.repo == repo)
            ]
            
            return len(recent_failures) / window_seconds
    
    def get_top_failures(
        self,
        limit: int = 10,
        window_seconds: float = 3600.0,
    ) -> List[Tuple[str, int]]:
        """
        Get top failure types.
        
        Args:
            limit: Maximum number to return
            window_seconds: Time window
            
        Returns:
            List of (error_type, count) tuples
        """
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        error_counts = defaultdict(int)
        
        with self._lock:
            for event in self._events:
                if event.timestamp >= cutoff:
                    error_counts[event.error_type] += 1
        
        # Sort by count
        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_errors[:limit]
    
    def get_statistics(self) -> Dict:
        """
        Get correlator statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            current_time = time.time()
            recent_count = sum(
                1 for e in self._events
                if current_time - e.timestamp <= 300
            )
            
            return {
                'total_failures': self._total_failures,
                'total_cascades': self._total_cascades,
                'recent_failures': recent_count,
                'active_events': len(self._events),
                'current_failure_rate': self.get_failure_rate(),
            }

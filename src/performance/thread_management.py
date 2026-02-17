"""
Resource-Aware Zombie Hunter V2

Advanced thread management with ancestry tracking and resource profiling.
Detects and manages zombie threads efficiently with comprehensive monitoring.
"""

import threading
import time
import psutil
from typing import Dict, Optional, Set, List, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThreadInfo:
    """Information about a tracked thread."""
    thread_id: int
    parent_id: Optional[int]
    creation_time: float
    last_activity: float
    activity_count: int
    cpu_time: float
    memory_usage: int
    activity_types: Set[str]
    
    
@dataclass
class ResourceProfile:
    """Resource usage profile for a thread."""
    cpu_percent: float
    memory_mb: float
    activity_rate: float  # activities per second
    is_zombie: bool
    inactivity_duration: float


class ResourceAwareZombieHunterV2:
    """
    Advanced thread management with ancestry tracking.
    
    Features:
    - Thread ancestry tracking for hierarchical cleanup
    - Resource profiling (CPU, memory, activity)
    - Configurable zombie detection thresholds
    - Activity type categorization
    - Automatic cleanup recommendations
    
    Example:
        hunter = ResourceAwareZombieHunterV2()
        hunter.register_thread(thread, parent_id=main_thread_id)
        hunter.report_activity(thread_id, activity_type='compute')
        zombies = hunter.detect_zombies()
    """
    
    def __init__(
        self,
        inactivity_threshold: float = 300.0,  # 5 minutes
        cpu_threshold: float = 0.1,  # 0.1% CPU usage
        check_interval: float = 60.0,  # 1 minute
    ):
        """
        Initialize zombie hunter.
        
        Args:
            inactivity_threshold: Seconds of inactivity before considering zombie
            cpu_threshold: Minimum CPU% to consider thread active
            check_interval: Seconds between automatic checks
        """
        self.inactivity_threshold = inactivity_threshold
        self.cpu_threshold = cpu_threshold
        self.check_interval = check_interval
        
        self._threads: Dict[int, ThreadInfo] = {}
        self._children: Dict[int, Set[int]] = defaultdict(set)
        self._lock = threading.Lock()
        self._last_check = time.time()
        
        # Track process for resource monitoring
        try:
            self._process = psutil.Process()
        except Exception as e:
            logger.warning(f"Could not initialize psutil: {e}")
            self._process = None
    
    def register_thread(
        self,
        thread: threading.Thread,
        parent_id: Optional[int] = None,
    ) -> int:
        """
        Register a new thread for tracking.
        
        Args:
            thread: Thread object to track
            parent_id: ID of parent thread (for ancestry tracking)
            
        Returns:
            Thread ID
        """
        thread_id = thread.ident if thread.ident else id(thread)
        current_time = time.time()
        
        with self._lock:
            self._threads[thread_id] = ThreadInfo(
                thread_id=thread_id,
                parent_id=parent_id,
                creation_time=current_time,
                last_activity=current_time,
                activity_count=0,
                cpu_time=0.0,
                memory_usage=0,
                activity_types=set(),
            )
            
            if parent_id is not None:
                self._children[parent_id].add(thread_id)
        
        logger.debug(f"Registered thread {thread_id} with parent {parent_id}")
        return thread_id
    
    def report_activity(
        self,
        thread_id: int,
        activity_type: str = 'generic',
    ) -> None:
        """
        Report activity for a thread.
        
        Args:
            thread_id: ID of the thread
            activity_type: Type of activity (e.g., 'compute', 'io', 'network')
        """
        with self._lock:
            if thread_id not in self._threads:
                logger.warning(f"Activity reported for unregistered thread {thread_id}")
                return
            
            thread_info = self._threads[thread_id]
            thread_info.last_activity = time.time()
            thread_info.activity_count += 1
            thread_info.activity_types.add(activity_type)
    
    def get_resource_profile(self, thread_id: int) -> Optional[ResourceProfile]:
        """
        Get resource usage profile for a thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            ResourceProfile if thread exists, None otherwise
        """
        with self._lock:
            if thread_id not in self._threads:
                return None
            
            thread_info = self._threads[thread_id]
            current_time = time.time()
            inactivity = current_time - thread_info.last_activity
            lifetime = current_time - thread_info.creation_time
            
            # Calculate activity rate
            activity_rate = (
                thread_info.activity_count / lifetime
                if lifetime > 0 else 0.0
            )
            
            # Estimate CPU and memory (simplified for now)
            cpu_percent = 0.0
            memory_mb = 0.0
            
            if self._process:
                try:
                    # Get overall process stats as approximation
                    cpu_percent = self._process.cpu_percent()
                    memory_mb = self._process.memory_info().rss / (1024 * 1024)
                except Exception:
                    pass
            
            # Determine if zombie
            is_zombie = (
                inactivity > self.inactivity_threshold and
                cpu_percent < self.cpu_threshold and
                activity_rate < 0.01  # Less than 1 activity per 100 seconds
            )
            
            return ResourceProfile(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                activity_rate=activity_rate,
                is_zombie=is_zombie,
                inactivity_duration=inactivity,
            )
    
    def detect_zombies(self) -> List[Tuple[int, ResourceProfile]]:
        """
        Detect zombie threads based on resource profiles.
        
        Returns:
            List of (thread_id, resource_profile) tuples for zombies
        """
        zombies = []
        
        with self._lock:
            for thread_id in list(self._threads.keys()):
                profile = self.get_resource_profile(thread_id)
                if profile and profile.is_zombie:
                    zombies.append((thread_id, profile))
        
        self._last_check = time.time()
        logger.info(f"Detected {len(zombies)} zombie threads")
        return zombies
    
    def get_thread_ancestry(self, thread_id: int) -> List[int]:
        """
        Get ancestry chain for a thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            List of thread IDs from root to current thread
        """
        ancestry = []
        current = thread_id
        
        with self._lock:
            while current is not None:
                if current not in self._threads:
                    break
                ancestry.insert(0, current)
                current = self._threads[current].parent_id
        
        return ancestry
    
    def get_descendants(self, thread_id: int) -> Set[int]:
        """
        Get all descendant threads of a thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            Set of descendant thread IDs
        """
        descendants = set()
        
        def collect_descendants(tid: int):
            for child_id in self._children.get(tid, set()):
                descendants.add(child_id)
                collect_descendants(child_id)
        
        with self._lock:
            collect_descendants(thread_id)
        
        return descendants
    
    def cleanup_zombie_tree(self, thread_id: int) -> Set[int]:
        """
        Clean up a zombie thread and all its descendants.
        
        Args:
            thread_id: ID of the zombie thread
            
        Returns:
            Set of cleaned up thread IDs
        """
        cleaned = set()
        
        with self._lock:
            # Get all descendants
            to_clean = {thread_id} | self.get_descendants(thread_id)
            
            for tid in to_clean:
                if tid in self._threads:
                    # Remove from parent's children
                    parent_id = self._threads[tid].parent_id
                    if parent_id and parent_id in self._children:
                        self._children[parent_id].discard(tid)
                    
                    # Remove thread info
                    del self._threads[tid]
                    
                    # Remove children mapping
                    if tid in self._children:
                        del self._children[tid]
                    
                    cleaned.add(tid)
        
        logger.info(f"Cleaned up {len(cleaned)} threads in zombie tree")
        return cleaned
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about tracked threads.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_threads = len(self._threads)
            zombies = self.detect_zombies()
            
            activity_types = set()
            total_activities = 0
            
            for thread_info in self._threads.values():
                activity_types.update(thread_info.activity_types)
                total_activities += thread_info.activity_count
            
            return {
                'total_threads': total_threads,
                'zombie_count': len(zombies),
                'activity_types': list(activity_types),
                'total_activities': total_activities,
                'last_check': self._last_check,
            }

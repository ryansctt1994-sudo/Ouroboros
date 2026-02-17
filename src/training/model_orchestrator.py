"""
Fair Model Orchestrator

Starvation-prevention scheduling with priority decay.
Ensures fair resource allocation across multiple models.
"""

import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import heapq
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelRequest:
    """Training request for a model."""
    model_id: str
    priority: float
    submit_time: float
    estimated_duration: float
    resource_requirements: Dict[str, float]
    
    def __lt__(self, other):
        """Compare by priority (higher priority first)."""
        return self.priority > other.priority


@dataclass
class ModelStats:
    """Statistics for a model."""
    model_id: str
    total_requests: int
    completed_requests: int
    total_wait_time: float
    total_execution_time: float
    avg_wait_time: float
    avg_execution_time: float
    current_priority: float
    starvation_score: float


class FairModelOrchestrator:
    """
    Fair scheduling with starvation prevention and priority decay.
    
    Features:
    - Priority-based scheduling with aging
    - Starvation prevention through wait-time boosting
    - Priority decay for frequently scheduled models
    - Resource-aware scheduling
    - Fairness metrics tracking
    
    Example:
        orchestrator = FairModelOrchestrator()
        orchestrator.register_model('model_a', base_priority=1.0)
        
        # Submit training request
        request_id = orchestrator.submit_request(
            'model_a',
            estimated_duration=60.0,
            resource_requirements={'gpu_memory': 8.0}
        )
        
        # Scheduler picks next model
        model_id, request = orchestrator.schedule_next()
        train_model(model_id)
        orchestrator.complete_request(request_id)
    """
    
    def __init__(
        self,
        aging_factor: float = 0.1,
        decay_factor: float = 0.95,
        starvation_threshold: float = 300.0,
        priority_boost: float = 0.5,
    ):
        """
        Initialize model orchestrator.
        
        Args:
            aging_factor: Factor for priority increase based on wait time
            decay_factor: Factor for priority decay after scheduling
            starvation_threshold: Wait time (seconds) before starvation boost
            priority_boost: Boost amount for starving models
        """
        self.aging_factor = aging_factor
        self.decay_factor = decay_factor
        self.starvation_threshold = starvation_threshold
        self.priority_boost = priority_boost
        
        self._models: Dict[str, Dict] = {}
        self._request_queue: List[ModelRequest] = []
        self._active_requests: Dict[str, ModelRequest] = {}
        self._completed_requests: Dict[str, List[Tuple[float, float]]] = {}
        
        self._lock = threading.Lock()
        self._request_counter = 0
        
    def register_model(
        self,
        model_id: str,
        base_priority: float = 1.0,
    ) -> None:
        """
        Register a model for orchestration.
        
        Args:
            model_id: Unique model identifier
            base_priority: Base priority level
        """
        with self._lock:
            if model_id in self._models:
                logger.warning(f"Model {model_id} already registered")
                return
            
            self._models[model_id] = {
                'base_priority': base_priority,
                'current_priority': base_priority,
                'last_scheduled': None,
                'total_scheduled': 0,
                'total_wait_time': 0.0,
                'total_execution_time': 0.0,
            }
            self._completed_requests[model_id] = []
        
        logger.info(f"Registered model {model_id} with priority {base_priority}")
    
    def submit_request(
        self,
        model_id: str,
        estimated_duration: float = 60.0,
        resource_requirements: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Submit a training request.
        
        Args:
            model_id: Model identifier
            estimated_duration: Estimated execution time in seconds
            resource_requirements: Required resources (e.g., {'gpu_memory': 8.0})
            
        Returns:
            Request ID
        """
        if model_id not in self._models:
            raise ValueError(f"Model {model_id} not registered")
        
        if resource_requirements is None:
            resource_requirements = {}
        
        current_time = time.time()
        
        with self._lock:
            self._request_counter += 1
            request_id = f"{model_id}_{self._request_counter}"
            
            # Get current priority
            priority = self._models[model_id]['current_priority']
            
            request = ModelRequest(
                model_id=model_id,
                priority=priority,
                submit_time=current_time,
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements,
            )
            
            # Add to priority queue
            heapq.heappush(self._request_queue, request)
            self._active_requests[request_id] = request
        
        logger.debug(f"Submitted request {request_id} for {model_id}")
        return request_id
    
    def schedule_next(self) -> Optional[Tuple[str, ModelRequest]]:
        """
        Schedule the next model for training.
        
        Returns:
            (request_id, request) tuple or None if queue empty
        """
        current_time = time.time()
        
        with self._lock:
            if not self._request_queue:
                return None
            
            # Update priorities based on aging
            self._age_priorities(current_time)
            
            # Check for starvation
            self._boost_starving_models(current_time)
            
            # Rebuild heap with updated priorities
            heapq.heapify(self._request_queue)
            
            # Pop highest priority request
            request = heapq.heappop(self._request_queue)
            model_id = request.model_id
            
            # Find request ID
            request_id = None
            for rid, req in self._active_requests.items():
                if req is request:
                    request_id = rid
                    break
            
            if request_id is None:
                logger.error("Could not find request ID")
                return None
            
            # Update model stats
            model_info = self._models[model_id]
            model_info['last_scheduled'] = current_time
            model_info['total_scheduled'] += 1
            
            # Calculate wait time
            wait_time = current_time - request.submit_time
            model_info['total_wait_time'] += wait_time
            
            # Apply priority decay
            model_info['current_priority'] *= self.decay_factor
        
        logger.debug(f"Scheduled request {request_id} for {model_id}")
        return request_id, request
    
    def complete_request(
        self,
        request_id: str,
        actual_duration: Optional[float] = None,
    ) -> None:
        """
        Mark a request as completed.
        
        Args:
            request_id: Request identifier
            actual_duration: Actual execution time (estimated if not provided)
        """
        current_time = time.time()
        
        with self._lock:
            if request_id not in self._active_requests:
                logger.warning(f"Request {request_id} not found")
                return
            
            request = self._active_requests[request_id]
            model_id = request.model_id
            
            # Calculate execution time
            if actual_duration is None:
                actual_duration = request.estimated_duration
            
            # Update stats
            model_info = self._models[model_id]
            model_info['total_execution_time'] += actual_duration
            
            # Record completion
            wait_time = (
                model_info['last_scheduled'] - request.submit_time
                if model_info['last_scheduled'] else 0.0
            )
            self._completed_requests[model_id].append((wait_time, actual_duration))
            
            # Remove from active requests
            del self._active_requests[request_id]
        
        logger.debug(f"Completed request {request_id} for {model_id}")
    
    def _age_priorities(self, current_time: float) -> None:
        """
        Increase priorities based on wait time (aging).
        
        Args:
            current_time: Current timestamp
        """
        for request in self._request_queue:
            wait_time = current_time - request.submit_time
            # Increase priority based on wait time
            age_boost = wait_time * self.aging_factor / 60.0  # Per minute
            request.priority += age_boost
    
    def _boost_starving_models(self, current_time: float) -> None:
        """
        Boost priorities for starving models.
        
        Args:
            current_time: Current timestamp
        """
        for request in self._request_queue:
            wait_time = current_time - request.submit_time
            
            if wait_time > self.starvation_threshold:
                # Apply starvation boost
                request.priority += self.priority_boost
                
                logger.info(
                    f"Starvation boost applied to {request.model_id} "
                    f"(waited {wait_time:.1f}s)"
                )
    
    def get_model_stats(self, model_id: str) -> ModelStats:
        """
        Get statistics for a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            ModelStats
        """
        if model_id not in self._models:
            raise ValueError(f"Model {model_id} not registered")
        
        with self._lock:
            model_info = self._models[model_id]
            completed = self._completed_requests[model_id]
            
            total_requests = model_info['total_scheduled'] + len(completed)
            completed_count = len(completed)
            
            # Calculate averages
            if completed:
                avg_wait = sum(w for w, _ in completed) / len(completed)
                avg_exec = sum(e for _, e in completed) / len(completed)
            else:
                avg_wait = 0.0
                avg_exec = 0.0
            
            # Calculate starvation score
            starvation_score = 0.0
            current_time = time.time()
            for request in self._request_queue:
                if request.model_id == model_id:
                    wait = current_time - request.submit_time
                    if wait > self.starvation_threshold:
                        starvation_score += (wait - self.starvation_threshold) / 60.0
        
        return ModelStats(
            model_id=model_id,
            total_requests=total_requests,
            completed_requests=completed_count,
            total_wait_time=model_info['total_wait_time'],
            total_execution_time=model_info['total_execution_time'],
            avg_wait_time=avg_wait,
            avg_execution_time=avg_exec,
            current_priority=model_info['current_priority'],
            starvation_score=starvation_score,
        )
    
    def get_queue_status(self) -> Dict:
        """
        Get overall queue status.
        
        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            queue_size = len(self._request_queue)
            active_size = len(self._active_requests)
            
            # Calculate per-model distribution
            model_distribution = {}
            for request in self._request_queue:
                model_id = request.model_id
                model_distribution[model_id] = model_distribution.get(model_id, 0) + 1
        
        return {
            'queue_size': queue_size,
            'active_requests': active_size,
            'model_distribution': model_distribution,
            'registered_models': len(self._models),
        }

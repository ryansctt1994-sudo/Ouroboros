#!/usr/bin/env python3
"""
gRPC Telemetry Service
======================

Asynchronous telemetry service for real-time metrics reporting.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from concurrent import futures
from typing import Dict, List, Optional, Deque
import threading

logger = logging.getLogger("eden_telemetry")

try:
    import grpc
    from grpc import aio as grpc_aio
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("grpcio not installed. Telemetry service will be unavailable.")


class MetricStore:
    """Thread-safe metric storage with time-series support."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, Deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = threading.Lock()
    
    def add_metric(self, name: str, value: float, timestamp: Optional[int] = None, labels: Optional[Dict] = None):
        """Add a metric data point."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        with self._lock:
            self._metrics[name].append({
                'value': value,
                'timestamp': timestamp,
                'labels': labels or {}
            })
    
    def get_metrics(self, name: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict]:
        """Get metrics for a given name and time range."""
        with self._lock:
            metrics = list(self._metrics.get(name, []))
        
        if start_time or end_time:
            metrics = [
                m for m in metrics
                if (start_time is None or m['timestamp'] >= start_time) and
                   (end_time is None or m['timestamp'] <= end_time)
            ]
        
        return metrics
    
    def get_summary(self, name: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> Dict:
        """Get summary statistics for a metric."""
        metrics = self.get_metrics(name, start_time, end_time)
        
        if not metrics:
            return {
                'count': 0,
                'min': 0.0,
                'max': 0.0,
                'avg': 0.0,
                'p50': 0.0,
                'p95': 0.0,
                'p99': 0.0
            }
        
        values = sorted([m['value'] for m in metrics])
        count = len(values)
        
        def percentile(p):
            k = (count - 1) * p / 100.0
            f = int(k)
            c = f + 1
            if c >= count:
                return values[-1]
            return values[f] + (k - f) * (values[c] - values[f])
        
        return {
            'count': count,
            'min': values[0],
            'max': values[-1],
            'avg': sum(values) / count,
            'p50': percentile(50),
            'p95': percentile(95),
            'p99': percentile(99)
        }


if GRPC_AVAILABLE:
    # Import generated protobuf code
    # Note: These will be generated from telemetry.proto
    # For now, we'll create a simplified implementation
    
    class TelemetryServicer:
        """gRPC servicer for telemetry."""
        
        def __init__(self):
            self.metric_store = MetricStore()
        
        async def StreamMetrics(self, request_iterator, context):
            """Handle streaming metrics."""
            count = 0
            async for metric_data in request_iterator:
                try:
                    # Store the metric
                    self.metric_store.add_metric(
                        name=metric_data.get('metric_name', 'unknown'),
                        value=metric_data.get('value', 0.0),
                        timestamp=metric_data.get('timestamp'),
                        labels=metric_data.get('labels', {})
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error processing metric: {e}")
            
            return {
                'success': True,
                'message': f'Processed {count} metrics',
                'server_timestamp': int(time.time() * 1000)
            }
        
        async def SendMetric(self, request, context):
            """Handle single metric submission."""
            try:
                self.metric_store.add_metric(
                    name=request.get('metric_name', 'unknown'),
                    value=request.get('value', 0.0),
                    timestamp=request.get('timestamp'),
                    labels=request.get('labels', {})
                )
                
                return {
                    'success': True,
                    'message': 'Metric received',
                    'server_timestamp': int(time.time() * 1000)
                }
            except Exception as e:
                logger.error(f"Error processing metric: {e}")
                return {
                    'success': False,
                    'message': str(e),
                    'server_timestamp': int(time.time() * 1000)
                }
        
        async def GetSummary(self, request, context):
            """Get metric summary."""
            try:
                summary = self.metric_store.get_summary(
                    name=request.get('metric_name', ''),
                    start_time=request.get('start_time'),
                    end_time=request.get('end_time')
                )
                
                return {
                    'metric_name': request.get('metric_name', ''),
                    **summary
                }
            except Exception as e:
                logger.error(f"Error getting summary: {e}")
                return {
                    'metric_name': request.get('metric_name', ''),
                    'count': 0,
                    'min': 0.0,
                    'max': 0.0,
                    'avg': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0
                }


class TelemetryClient:
    """Async telemetry client for sending metrics."""
    
    def __init__(self, endpoint: str = "localhost:50051"):
        self.endpoint = endpoint
        self._channel = None
        self._stub = None
        self._enabled = GRPC_AVAILABLE
        self._queue = None  # Created lazily in connect()
        self._background_task = None
    
    async def connect(self):
        """Connect to telemetry server."""
        if not self._enabled:
            logger.warning("gRPC not available, telemetry disabled")
            return False
        
        try:
            # Create async channel
            self._channel = grpc_aio.insecure_channel(self.endpoint)
            
            # Create queue in async context
            self._queue = asyncio.Queue(maxsize=1000)
            
            # Note: In production, use generated stub from protobuf
            logger.info(f"Connected to telemetry server at {self.endpoint}")
            
            # Start background worker
            self._background_task = asyncio.create_task(self._process_queue())
            return True
        except Exception as e:
            logger.error(f"Failed to connect to telemetry server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from telemetry server."""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        if self._channel:
            await self._channel.close()
    
    async def send_metric(self, name: str, value: float, labels: Optional[Dict] = None):
        """Send a metric asynchronously."""
        if not self._enabled or self._queue is None:
            return
        
        metric_data = {
            'metric_name': name,
            'value': value,
            'timestamp': int(time.time() * 1000),
            'labels': labels or {}
        }
        
        try:
            # Non-blocking put with timeout
            await asyncio.wait_for(self._queue.put(metric_data), timeout=0.01)
        except asyncio.TimeoutError:
            logger.warning(f"Telemetry queue full, dropping metric: {name}")
    
    async def _process_queue(self):
        """Background task to process metric queue."""
        while True:
            try:
                # Batch metrics for efficiency
                batch = []
                timeout = 0.1  # 100ms batch window
                
                try:
                    # Get first metric with timeout
                    metric = await asyncio.wait_for(self._queue.get(), timeout=timeout)
                    batch.append(metric)
                    
                    # Get additional metrics without blocking
                    while len(batch) < 100:  # Max batch size
                        try:
                            metric = self._queue.get_nowait()
                            batch.append(metric)
                        except asyncio.QueueEmpty:
                            break
                except asyncio.TimeoutError:
                    # No metrics available, continue
                    continue
                
                if batch:
                    await self._send_batch(batch)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing telemetry queue: {e}")
                await asyncio.sleep(1)  # Back off on error
    
    async def _send_batch(self, batch: List[Dict]):
        """Send a batch of metrics."""
        try:
            # In production, use the generated gRPC stub
            # For now, just log
            logger.debug(f"Sending batch of {len(batch)} metrics")
            # await self._stub.StreamMetrics(iter(batch))
        except Exception as e:
            logger.error(f"Error sending metrics batch: {e}")


# Singleton client instance
_telemetry_client: Optional[TelemetryClient] = None


def get_telemetry_client(endpoint: Optional[str] = None) -> TelemetryClient:
    """Get or create telemetry client singleton."""
    global _telemetry_client
    
    if _telemetry_client is None:
        endpoint = endpoint or "localhost:50051"
        _telemetry_client = TelemetryClient(endpoint)
    
    return _telemetry_client


async def send_metric_async(name: str, value: float, labels: Optional[Dict] = None):
    """Helper function to send a metric asynchronously."""
    client = get_telemetry_client()
    await client.send_metric(name, value, labels)

"""Metrics collection and aggregation for Resume Customizer.

This module handles collecting and aggregating metrics from various parts of
the application, including agent performance, API usage, and system metrics.
"""

import time
from collections import defaultdict
from datetime import datetime, timezone
import threading
from typing import Dict, List, Any, Optional

from loguru import logger
import psutil

from resume_customizer.core.config import settings


# Thread-safe storage for metrics
_metrics_lock = threading.RLock()
_agent_metrics = defaultdict(lambda: defaultdict(list))
_api_metrics = defaultdict(lambda: defaultdict(list))
_system_metrics_history = []
_system_metrics_snapshot_interval = 300  # seconds


class MetricsAggregator:
    """Utility class for aggregating metrics."""
    
    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, float]:
        """Calculate standard statistics for a set of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dictionary with count, min, max, avg, p50, p90, p99 statistics
        """
        if not values:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            }
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[count // 2],
            "p90": sorted_values[int(count * 0.9)],
            "p99": sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1],
        }
    
    @staticmethod
    def aggregate_metrics(raw_metrics: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Aggregate raw metrics into statistical summaries.
        
        Args:
            raw_metrics: Dictionary mapping metric names to lists of values
            
        Returns:
            Dictionary mapping metric names to statistical summaries
        """
        aggregated = {}
        
        for metric_name, values in raw_metrics.items():
            # Skip non-numeric metrics
            if not values or not all(isinstance(v, (int, float)) for v in values):
                continue
                
            aggregated[metric_name] = MetricsAggregator.calculate_statistics(values)
        
        return aggregated


def track_agent_metrics(agent_name: str, metrics: Dict[str, Any]) -> None:
    """Track metrics for an agent operation.
    
    Args:
        agent_name: Name of the agent (profiler, researcher, strategist)
        metrics: Dictionary of metrics to record
    """
    if not settings.ENABLE_PERFORMANCE_LOGGING:
        return
    
    with _metrics_lock:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Add timestamp for this metrics entry
        metrics_with_timestamp = {**metrics, "timestamp": timestamp}
        
        # Store in time-series format for each agent
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                _agent_metrics[agent_name][metric_name].append(value)
        
        logger.debug(f"Tracked metrics for {agent_name}: {metrics}")


def track_api_metrics(endpoint: str, metrics: Dict[str, Any]) -> None:
    """Track metrics for an API endpoint.
    
    Args:
        endpoint: Name of the API endpoint
        metrics: Dictionary of metrics to record
    """
    if not settings.ENABLE_PERFORMANCE_LOGGING:
        return
    
    with _metrics_lock:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Add timestamp for this metrics entry
        metrics_with_timestamp = {**metrics, "timestamp": timestamp}
        
        # Store in time-series format for each endpoint
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                _api_metrics[endpoint][metric_name].append(value)
        
        logger.debug(f"Tracked metrics for endpoint {endpoint}: {metrics}")


def track_system_metrics() -> None:
    """Capture and store system-level metrics."""
    if not settings.ENABLE_PERFORMANCE_LOGGING:
        return
    
    try:
        with _metrics_lock:
            # Capture current system metrics
            metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
            }
            
            _system_metrics_history.append(metrics)
            
            # Keep only the last 24 hours of metrics (at 5-minute intervals)
            max_history = 24 * 60 // 5  # 24 hours at 5-minute intervals
            if len(_system_metrics_history) > max_history:
                _system_metrics_history.pop(0)
    except Exception as e:
        logger.warning(f"Failed to capture system metrics: {str(e)}")


def get_agent_metrics(agent_name: Optional[str] = None, aggregated: bool = True) -> Dict:
    """Get metrics for one or all agents.
    
    Args:
        agent_name: Specific agent to get metrics for, or None for all agents
        aggregated: Whether to return aggregated statistics or raw values
        
    Returns:
        Dictionary of agent metrics
    """
    with _metrics_lock:
        if agent_name:
            # Return metrics for a specific agent
            if agent_name not in _agent_metrics:
                return {}
            
            agent_data = _agent_metrics[agent_name]
            if aggregated:
                return MetricsAggregator.aggregate_metrics(agent_data)
            else:
                return dict(agent_data)
        else:
            # Return metrics for all agents
            result = {}
            for name, metrics in _agent_metrics.items():
                if aggregated:
                    result[name] = MetricsAggregator.aggregate_metrics(metrics)
                else:
                    result[name] = dict(metrics)
            
            return result


def get_api_metrics(endpoint: Optional[str] = None, aggregated: bool = True) -> Dict:
    """Get metrics for one or all API endpoints.
    
    Args:
        endpoint: Specific endpoint to get metrics for, or None for all endpoints
        aggregated: Whether to return aggregated statistics or raw values
        
    Returns:
        Dictionary of API metrics
    """
    with _metrics_lock:
        if endpoint:
            # Return metrics for a specific endpoint
            if endpoint not in _api_metrics:
                return {}
            
            endpoint_data = _api_metrics[endpoint]
            if aggregated:
                return MetricsAggregator.aggregate_metrics(endpoint_data)
            else:
                return dict(endpoint_data)
        else:
            # Return metrics for all endpoints
            result = {}
            for name, metrics in _api_metrics.items():
                if aggregated:
                    result[name] = MetricsAggregator.aggregate_metrics(metrics)
                else:
                    result[name] = dict(metrics)
            
            return result


def get_system_metrics(aggregated: bool = True) -> Dict:
    """Get system-level metrics.
    
    Args:
        aggregated: Whether to return aggregated statistics or all data points
        
    Returns:
        Dictionary of system metrics
    """
    with _metrics_lock:
        if not _system_metrics_history:
            return {}
        
        if not aggregated:
            # Return all data points
            return {"history": _system_metrics_history}
        else:
            # Return aggregated statistics
            metrics = {}
            for metric_name in ["cpu_percent", "memory_percent", "disk_percent"]:
                values = [m[metric_name] for m in _system_metrics_history if metric_name in m]
                metrics[metric_name] = MetricsAggregator.calculate_statistics(values)
            
            # Add latest values
            latest = _system_metrics_history[-1]
            metrics["latest"] = {
                k: v for k, v in latest.items() if k != "timestamp"
            }
            
            return metrics


def reset_metrics() -> None:
    """Reset all collected metrics."""
    with _metrics_lock:
        _agent_metrics.clear()
        _api_metrics.clear()
        _system_metrics_history.clear()
        
        logger.info("All metrics have been reset")


# Initialize system metrics collection
if settings.ENABLE_PERFORMANCE_LOGGING:
    import threading
    
    def _system_metrics_collector():
        while True:
            track_system_metrics()
            time.sleep(_system_metrics_snapshot_interval)
    
    # Start system metrics collection in a daemon thread
    system_metrics_thread = threading.Thread(
        target=_system_metrics_collector,
        daemon=True,
        name="SystemMetricsCollector"
    )
    system_metrics_thread.start()
    
    logger.info("System metrics collection started")

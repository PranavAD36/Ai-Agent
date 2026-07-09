import threading
from typing import Dict, List, Any

class MetricsCollector:
    """Thread-safe collector for LLM failover and performance metrics."""
    def __init__(self):
        self._lock = threading.Lock()
        self.success_counts: Dict[str, int] = {}
        self.failure_counts: Dict[str, int] = {}
        self.retry_counts: Dict[str, int] = {}
        self.latencies: Dict[str, List[float]] = {}
        self.switch_count: int = 0
        self.active_provider: str = "None"
        self.all_failed_count: int = 0

    def record_success(self, provider_id: str, latency: float, response: Any = None):
        with self._lock:
            self.success_counts[provider_id] = self.success_counts.get(provider_id, 0) + 1
            if provider_id not in self.latencies:
                self.latencies[provider_id] = []
            self.latencies[provider_id].append(latency)
            self.active_provider = provider_id

    def record_failure(self, provider_id: str, error: Exception, is_retryable: bool):
        with self._lock:
            self.failure_counts[provider_id] = self.failure_counts.get(provider_id, 0) + 1

    def record_retry(self, provider_id: str):
        with self._lock:
            self.retry_counts[provider_id] = self.retry_counts.get(provider_id, 0) + 1

    def record_switch(self, from_provider: str, to_provider: str):
        with self._lock:
            self.switch_count += 1
            self.active_provider = to_provider

    def record_all_failed(self):
        with self._lock:
            self.all_failed_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            avg_latencies = {}
            for pid, lats in self.latencies.items():
                if lats:
                    avg_latencies[pid] = sum(lats) / len(lats)
                else:
                    avg_latencies[pid] = 0.0

            # Calculate success rate
            success_rates = {}
            for pid in set(list(self.success_counts.keys()) + list(self.failure_counts.keys())):
                succs = self.success_counts.get(pid, 0)
                fails = self.failure_counts.get(pid, 0)
                total = succs + fails
                success_rates[pid] = (succs / total) if total > 0 else 0.0

            return {
                "active_provider": self.active_provider,
                "provider_switch_count": self.switch_count,
                "all_failed_count": self.all_failed_count,
                "success_counts": dict(self.success_counts),
                "failure_counts": dict(self.failure_counts),
                "retry_counts": dict(self.retry_counts),
                "average_latency": avg_latencies,
                "success_rate": success_rates
            }

# Global metrics tracker
metrics = MetricsCollector()

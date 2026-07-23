import time
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("resilience")

class CircuitBreakerOpenException(Exception):
    """Exception raised when the circuit breaker is open and blocking calls."""
    pass


class CircuitBreaker:
    """Implements Circuit Breaker Pattern tracking failure rates of external API providers."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_success(self) -> None:
        """Resets failures on successful operation."""
        self.failure_count = 0
        if self.state != "CLOSED":
            logger.info("Circuit breaker transitioned from OPEN/HALF-OPEN to CLOSED state.")
            self.state = "CLOSED"
            self.last_state_change = time.time()

    def record_failure(self) -> None:
        """Increments failure count and trips circuit if threshold is reached."""
        self.failure_count += 1
        logger.warning(f"Recorded failure. Failure count: {self.failure_count}/{self.failure_threshold}")
        
        if self.failure_count >= self.failure_threshold and self.state != "OPEN":
            logger.error(f"Tripping circuit breaker! Entering OPEN state for {self.recovery_timeout} seconds.")
            self.state = "OPEN"
            self.last_state_change = time.time()

    def allow_request(self) -> bool:
        """Evaluates whether to block or allow the next API call."""
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            # Check if timeout has expired
            if time.time() - self.last_state_change >= self.recovery_timeout:
                logger.info("Recovery timeout expired. Transitioning circuit to HALF-OPEN state.")
                self.state = "HALF-OPEN"
                self.last_state_change = time.time()
                return True
            return False
            
        # HALF-OPEN allows requests to test health
        return True


# Global mapping of provider_name -> CircuitBreaker instance
_CIRCUITS: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(provider_name: str) -> CircuitBreaker:
    """Returns or creates a circuit breaker for a provider."""
    if provider_name not in _CIRCUITS:
        _CIRCUITS[provider_name] = CircuitBreaker()
    return _CIRCUITS[provider_name]


async def execute_resilient_call(provider_name: str, func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Executes a callable with circuit breaking and fast-failing support."""
    breaker = get_circuit_breaker(provider_name)
    
    if not breaker.allow_request():
        raise CircuitBreakerOpenException(
            f"Circuit breaker for provider '{provider_name}' is currently OPEN. Request blocked to prevent cascading failures."
        )
        
    try:
        res = await func(*args, **kwargs)
        breaker.record_success()
        return res
    except Exception as e:
        breaker.record_failure()
        raise e

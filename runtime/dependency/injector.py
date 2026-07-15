from typing import Any, Type, TypeVar
from providers.storage.local_storage import LocalStorage
from providers.eventbus.memory_event_bus import pre_configured_bus
from providers.scheduler.apscheduler_provider import APSchedulerProvider

T = TypeVar("T")

class RuntimeDependencyResolver:
    """Core Dependency Injection resolver managed by the AATES Runtime Layer."""
    
    def __init__(self) -> None:
        self._registry: dict[Type, Any] = {}
        # Pre-register foundation provider skeletons
        self.register(LocalStorage, LocalStorage())
        self.register(type(pre_configured_bus), pre_configured_bus)
        self.register(APSchedulerProvider, APSchedulerProvider())

    def register(self, interface: Type[T], implementation: Any) -> None:
        """Binds a dependency contract/class type to its concrete implementation instance."""
        self._registry[interface] = implementation

    def resolve(self, interface: Type[T]) -> T:
        """Resolves and retrieves a registered dependency component instance."""
        if interface not in self._registry:
            raise ValueError(f"Runtime DI: Dependency interface '{interface.__name__}' is unregistered.")
        return self._registry[interface]

dependency_resolver = RuntimeDependencyResolver()

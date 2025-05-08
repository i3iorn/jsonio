import logging
from typing import Tuple, Type, Union, LiteralString

from jsonio._config import ReaderConfig
from jsonio._utils import Backend
from jsonio.backend import JsonBackendProtocol, load_backend
from jsonio.backend.json_backend import JsonBackend


class BackendResolver:
    @classmethod
    def resolve_backend(cls, config: ReaderConfig) -> Tuple[Type[JsonBackendProtocol], Union[str, None, LiteralString]]:
        """
        Resolve the JSON backend, either by class or by name (lazy‐loaded).
        Falls back to built-in JsonBackend if the requested backend isn't installed and Flags.SAFE not set.
        """
        _logger = logging.getLogger(__name__)
        backend_name = config.backend_name
        backend_class = config.backend_class
        # 1) Must supply at least one
        if backend_name is None and backend_class is None:
            raise ValueError("Either 'backend_name' or 'backend_class' must be provided")

        # 2) If a class is provided, ensure it implements the protocol
        if backend_class is not None:
            if not issubclass(backend_class, JsonBackendProtocol):
                raise TypeError(f"backend_class must implement JsonBackendProtocol, got {backend_class}")
            # Derive a name if none given
            name = backend_name or getattr(backend_class, "__name__", "unknown").lower()
            return backend_class, name

        # 3) At this point we have a backend_name (string). Validate it.
        if not isinstance(backend_name, str):
            raise TypeError(f"backend_name must be a str, not {type(backend_name)}")
        try:
            backend_enum = Backend(backend_name)
        except ValueError:
            valid = ", ".join(b.value for b in Backend)
            raise ValueError(f"Invalid backend '{backend_name}'. Must be one of: {valid}")

        # 4) Attempt lazy import
        try:
            instance = load_backend(backend_enum, config.resolver_flags)
            return instance.__class__, backend_name
        except ImportError as e:
            _logger.warning(f"Could not lazy‐load backend '{backend_name}': {e}")

            if config.safe_mode:
                raise

            _logger.info("Falling back to built-in JsonBackend")
            return JsonBackend, Backend.JSON.value

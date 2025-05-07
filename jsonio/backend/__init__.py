import importlib
import logging
from typing import Type

from jsonio._utils import Backend
from jsonio.backend.protocol import JsonBackendProtocol

_logger = logging.getLogger(__name__)

_BACKEND_CLASSES = {
    Backend.JSON: "json_backend.JsonBackend",
    Backend.ORJSON: "orjson_backend.OrjsonBackend",
    Backend.UJSON: "ujson_backend.UjsonBackend",
    Backend.RAPIDJSON: "rapidjson_backend.RapidjsonBackend",
    Backend.SIMPLEJSON: "simplejson_backend.SimplejsonBackend",
}


def load_backend(backend: Backend) -> JsonBackendProtocol:
    """
    Lazily import and return a backend class instance.
    """
    if backend not in _BACKEND_CLASSES:
        raise ValueError(f"Unsupported backend: {backend}")

    module_path, class_name = _BACKEND_CLASSES[backend].rsplit(".", 1)

    try:
        module = importlib.import_module(f"jsonio.backends.{module_path}")
        backend_cls: Type[JsonBackendProtocol] = getattr(module, class_name)
        return backend_cls()
    except ImportError as e:
        _logger.error(f"Backend '{backend.value}' is not installed: {e}")
        raise ImportError(
            f"Backend '{backend.value}' is not available. Please install it manually or use InstallerFactory."
        ) from e

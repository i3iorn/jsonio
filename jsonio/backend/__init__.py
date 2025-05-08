import importlib
import logging
from typing import Type

from jsonio._utils import Backend, Flags
from jsonio.backend.protocol import JsonBackendProtocol

_logger = logging.getLogger(__name__)

_BACKEND_CLASSES = {
    Backend.JSON: "json_backend.JsonBackend",
    Backend.ORJSON: "orjson_backend.OrjsonBackend",
    Backend.UJSON: "ujson_backend.UjsonBackend",
    Backend.RAPIDJSON: "rapidjson_backend.RapidjsonBackend",
    Backend.SIMPLEJSON: "simplejson_backend.SimplejsonBackend",
}


def load_backend(backend: Backend, flags: Flags) -> JsonBackendProtocol:
    """
    Lazily import and return a backend class instance.
    """
    if backend not in _BACKEND_CLASSES:
        raise ValueError(f"Unsupported backend: {backend}")

    module_path, class_name = _BACKEND_CLASSES[backend].rsplit(".", 1)

    try:
        module = importlib.import_module(f"jsonio.backend.{module_path}")
        backend_cls: Type[JsonBackendProtocol] = getattr(module, class_name)
        return backend_cls()
    except ImportError as e:
        msg = f"Backend '{backend.value}' is not installed: {e}"
        if Flags.RUNTIME_INSTALL in flags:
            _logger.info(msg)
            try:
                from jsonio.backend._installer import InstallerFactory
                installer = InstallerFactory.get_installer(backend)
                installer.install()
                module = importlib.import_module(f"jsonio.backend.{module_path}")
                backend_cls: Type[JsonBackendProtocol] = getattr(module, class_name)
                return backend_cls()
            except Exception as install_error:
                _logger.error(f"Failed to install backend '{backend.value}': {install_error}")
                raise ImportError(msg) from install_error
        else:
            _logger.error(msg)
            raise ImportError(
                f"Backend '{backend.value}' is not available. Please install it manually or use InstallerFactory."
            ) from e

# -*- coding: utf-8 -*-
import importlib
import json
import logging
import re
import urllib.request
from io import StringIO, TextIOBase
from json import JSONDecoder
from pathlib import Path
from typing import Optional, Type, Callable, Any, IO, BinaryIO, Tuple, LiteralString, Union

from jsonio._exception import JsonParsingError
from jsonio._utils import (Flags, InputType, ReadFlags, JsonRoot, SUPPORTED_NETWORK_PROTOCOLS, Backend, FileSize,
                           BackendLimit, DecoderClass, SourceType)
from jsonio.backend import JsonBackendProtocol, load_backend
from jsonio.backend.json_backend import JsonBackend
from jsonio.backend.protocol import PluggableJsonLoaderProtocol


_DEFAULT_NETWORK_TIMEOUT = 5.0
_DEFAULT_JSON_BACKEND = JsonBackend


class JsonIOReader:
    """
    Reads JSON from a file‐path, file‐like, bytes or raw string.
    This class is a mixin that provides the read method for JSON data.
    It is designed to be used with classes that handle file I/O operations.
    The class supports reading JSON data from various sources, including:
    - File paths (local or network)
    - File-like objects (e.g., StringIO, BytesIO)
    - Raw JSON strings
    - Bytes or bytearray

    The class also provides options for encoding, decoding, and validation of the JSON data.
    """
    def __init__(
            self,
            *,
            flags: Flags = Flags.NONE,
            backend_name: Optional[str] = None,
            backend_class: Optional[Type[JsonBackendProtocol]] = _DEFAULT_JSON_BACKEND,
            logger: logging.Logger = None
    ) -> None:
        """
        Initialize the JsonIO mixin.

        :param flags: Flags to control the behavior of the reader.
        """
        self._backend_instance = None
        self._network_timeout = _DEFAULT_NETWORK_TIMEOUT
        if logger is not None and not isinstance(logger, logging.Logger):
            raise TypeError(f"logger must be an instance of logging.Logger")
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        if not isinstance(flags, Flags):
            raise TypeError(f"flags must be a Flags instance, not {type(flags)}")
        self.flags = flags

        self._backend, self._backend_name = self._load_backend(backend_name=backend_name, backend_class=backend_class)

    @property
    def backend(self) -> JsonBackendProtocol:
        """
        Get the backend instance.
        """
        if not hasattr(self, "_backend_instance"):
            self._backend_instance = self._backend()
        return self._backend_instance

    @property
    def network_timeout(self) -> Optional[float]:
        """
        Get the network timeout value.
        """
        return float(self._network_timeout)

    @network_timeout.setter
    def network_timeout(self, value: Optional[float]) -> None:
        """
        Set the network timeout value.
        """
        if value is None:
            self._network_timeout = None
        elif isinstance(value, (int, float)):
            self._network_timeout = float(value)
        else:
            raise TypeError(f"network_timeout must be a number, not {type(value)}")

    def _load_backend(
            self,
            *,
            backend_name: Optional[str] = None,
            backend_class: Optional[Type[JsonBackendProtocol]] = None
    ) -> Tuple[Type[JsonBackendProtocol], Union[str, None, LiteralString]]:
        """
        Resolve the JSON backend, either by class or by name (lazy‐loaded).
        Falls back to built-in JsonBackend if the requested backend isn't installed and Flags.SAFE not set.
        """
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
            instance = load_backend(backend_enum)
            return instance.__class__, backend_name
        except ImportError as e:
            self.logger.warning(f"Could not lazy‐load backend '{backend_name}': {e}")

            if Flags.SAFE in getattr(self, "flags", Flags.NONE):
                raise

            self.logger.info("Falling back to built-in JsonBackend")
            return JsonBackend, Backend.JSON.value

    def read(
            self,
            source: InputType,
            *,
            flags: ReadFlags = ReadFlags.NONE,
            encoding: str = "utf-8",
            decoder_cls: DecoderClass = JSONDecoder,
            validate: Optional[Callable[[JsonRoot], None]] = None,
            **parse_kwargs: Any
    ) -> Optional[JsonRoot]:
        """
        Read JSON from a file‐path, file‐like, bytes or raw string.

        :param source: file path, file‐like, bytes, or JSON string
        :param encoding: encoding to use for reading the file
        :param flags: flags to control the behavior of the read method
        :param decoder_cls: JSONDecoder class to use for deserialization
        :param validate: optional validation function to call on the parsed JSON data
        :param parse_kwargs: extra kwargs to pass to json.load/json.loads
        :return: deserialized JSON data
        """
        # if source is None, return None
        if source is None:
            raise ValueError("NoneType is not a valid source for JSON reading")

        if (ReadFlags.IS_JSON in flags) and (ReadFlags.IS_PATH in flags):
            raise ValueError("IS_JSON and IS_PATH cannot be used together")

        if not issubclass(decoder_cls, JSONDecoder):
            raise TypeError(f"cls must be a JSONDecoder class, not {type(decoder_cls)}")

        try:
            src_type, norm = self._classify_source(source, flags)
            with self._open(norm, src_type, encoding) as fp:
                # choose json.load for file‐like, loads for string
                if hasattr(fp, "read"):
                    if decoder_cls is not None:
                        if not isinstance(self.backend, PluggableJsonLoaderProtocol):
                            raise TypeError("decoder_cls is not supported by this backend")
                        else:
                            parse_kwargs["cls"] = decoder_cls
                    result = self.backend.load(fp, **parse_kwargs)
                    if validate:
                        validate(result)
                    return result
                # fallback shouldn't happen
                raise RuntimeError("Unexpected source type")
        except Exception as e:
            raise JsonParsingError(e) from e

    def _open(self, norm_source, src_type: SourceType, encoding: str) -> IO[str]:
        if src_type is SourceType.URL:
            resp = urllib.request.urlopen(norm_source, timeout=self.network_timeout)
            return StringIO(resp.read().decode(encoding))
        if src_type is SourceType.PATH:
            path: Path = norm_source
            if not path.exists(): raise FileNotFoundError(path)
            if path.is_dir():  raise IsADirectoryError(path)
            size = path.stat().st_size
            if size > BackendLimit[self._backend_name.upper()].value:
                self.logger.info("…large file warning…")
            return path.open("r", encoding=encoding)
        if src_type is SourceType.BYTES:
            return StringIO(norm_source.decode(encoding))
        if src_type is SourceType.JSON_STR:
            return StringIO(norm_source)
        # STREAM
        stream = norm_source
        data = stream.read()
        # if binary
        if isinstance(data, (bytes, bytearray)):
            return StringIO(data.decode(encoding))
        # text
        return StringIO(data) if not hasattr(data, "read") else data

    def _is_path(self, path: Path) -> bool:
        """
        Verify the path does look like a path, so that we don't try to load it as a json value
        """
        if Flags.SAFE in self.flags:
            return self._safe_is_path(path)
        else:
            return self._unsafe_is_path(path)

    @staticmethod
    def _safe_is_path(path: Path) -> bool:
        """
        We use soft heuristics to determine if the path is valid.
        """
        cant_contain = ("{", "[", '"', "'", "b'", "b\"")
        path_regex = r"^[a-zA-Z0-9_\-\/\\\.]+$"
        string = str(path)
        if string.endswith(".json"):
            return True
        if any(c in string for c in cant_contain):
            return False
        if not re.match(path_regex, string):
            return False
        return True

    def _unsafe_is_path(self, path: Path) -> bool:
        """
        We brute force the path to see if it is a path or a json string.
        """
        if Flags.FS_PROBE in self.flags:
            try:
                path.touch()
                path.unlink()
                return True
            except Exception as e:
                # if we can't create the file it is probably a json string and not a path
                return False
        else:
            return self._safe_is_path(path)

    def _classify_source(self, source: InputType, flags: ReadFlags) -> Tuple[SourceType, Any]:
        # handle None
        if source is None:
            raise ValueError("Cannot read from None")
        # explicit flags
        if ReadFlags.IS_JSON in flags:
            if not isinstance(source, str):
                raise ValueError("IS_JSON flag but not a string")
            return SourceType.JSON_STR, source
        if ReadFlags.IS_PATH in flags:
            p = Path(source)
            return SourceType.PATH, p
        # detect URL
        if isinstance(source, str) and source.startswith(SUPPORTED_NETWORK_PROTOCOLS):
            return SourceType.URL, source
        # path heuristic
        if isinstance(source, (str, Path)) and self._is_path(Path(source)):
            return SourceType.PATH, Path(source)
        # bytes
        if isinstance(source, (bytes, bytearray)):
            return SourceType.BYTES, source
        # file‐like
        if hasattr(source, "read"):
            return SourceType.STREAM, source
        # fallback: treat as JSON
        return SourceType.JSON_STR, str(source)

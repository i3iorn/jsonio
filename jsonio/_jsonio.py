import logging
from json import JSONDecoder, JSONDecodeError
from typing import Optional, Callable, Any

from jsonio._classifier import SourceClassifier
from jsonio._config import ReaderConfig
from jsonio._exception import JsonParsingError
from jsonio._loader import AbstractLoader, Loader
from jsonio._resolver import BackendResolver
from jsonio._utils import (Flags, InputType, JsonRoot, BackendLimit, DecoderClass)
from jsonio.backend import JsonBackendProtocol
from jsonio.backend.protocol import PluggableJsonLoaderProtocol


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
            config: ReaderConfig,
            loader: Optional[Loader] = None,
            logger: logging.Logger = None
    ) -> None:
        """
        Initialize the JsonIO mixin.

        :param flags: Flags to control the behavior of the reader.
        """
        if not isinstance(config, ReaderConfig):
            raise TypeError(f"config must be a ReaderConfig instance, not {type(config)}")
        self.config = config

        if logger is not None and not isinstance(logger, logging.Logger):
            raise TypeError(f"logger must be an instance of logging.Logger")

        self.logger = logger or logging.getLogger(self.__class__.__name__)

        if not isinstance(loader, AbstractLoader):
            raise TypeError(f"loader must be a Loader instance, not {type(loader)}")

        self.loader = loader or Loader()

        self._backend, self._backend_name = BackendResolver.resolve_backend(self.config)
        self._backend_instance = self._backend()

    @property
    def backend(self) -> JsonBackendProtocol:
        """
        Get the backend instance.
        """
        return self._backend_instance

    def read(
            self,
            source: InputType,
            *,
            flags: Flags = Flags.NONE,
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
        :param loader: optional loader to use for reading the JSON data
        :param parse_kwargs: extra kwargs to pass to json.load/json.loads
        :return: deserialized JSON data
        """
        # if source is None, return None
        if source is None:
            raise ValueError("NoneType is not a valid source for JSON reading")

        if (Flags.IS_JSON in flags) and (Flags.IS_PATH in flags):
            raise ValueError("IS_JSON and IS_PATH cannot be used together")

        if not issubclass(decoder_cls, JSONDecoder):
            raise TypeError(f"cls must be a JSONDecoder class, not {type(decoder_cls)}")

        if not isinstance(encoding, str):
            raise TypeError(f"encoding must be a str, not {type(encoding)}")

        if not isinstance(parse_kwargs, dict):
            raise TypeError(f"parse_kwargs must be a dict, not {type(parse_kwargs)}")

        if validate is not None and not callable(validate):
            raise TypeError(f"validate must be a callable, not {type(validate)}")

        try:
            src_type, norm = SourceClassifier.classify_source(source, self.config.classification_flags)
            size_hint = BackendLimit[self._backend_name.upper()].value
            with self.loader.open(norm, src_type, encoding, size_hint) as fp:
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
        except (ValueError, JSONDecodeError, OSError) as e:
            raise JsonParsingError(e) from e

from typing import runtime_checkable, Protocol, Optional, Any

from jsonio._utils import DecoderClass
from jsonio.backend import OpenFilePointer


@runtime_checkable
class JsonBackendProtocol(Protocol):
    """Marker protocol for JSON backend implementations."""
    ...


@runtime_checkable
class JsonReaderBackendProtocol(JsonBackendProtocol, Protocol):
    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None) -> Any:
        ...

    def loads(self, s: str, encoding: Optional[str] = None) -> Any:
        ...


@runtime_checkable
class JsonWriterBackendProtocol(JsonBackendProtocol, Protocol):
    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        ...

    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        ...


@runtime_checkable
class PluggableJsonLoaderProtocol(JsonBackendProtocol, Protocol):
    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None, decoder_class: DecoderClass = None) -> Any:
        ...

    def loads(self, s: str, encoding: Optional[str] = None, decoder_class: DecoderClass = None) -> Any:
        ...

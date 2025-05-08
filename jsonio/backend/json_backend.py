import json
from typing import Any, Optional

from jsonio._utils import DecoderClass, OpenFilePointer
from jsonio.backend.protocol import JsonReaderBackendProtocol, JsonWriterBackendProtocol, PluggableJsonLoaderProtocol


class JsonBackend(JsonReaderBackendProtocol, JsonWriterBackendProtocol, PluggableJsonLoaderProtocol):
    """Standard library JSON backend, supports pluggable decoder."""
    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        return json.dumps(obj)

    def loads(self, s: str, encoding: Optional[str] = None, decoder_class: DecoderClass = None) -> Any:
        return self._load(s, json.loads, cls=decoder_class, encoding=encoding)

    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        json.dump(obj, fp)

    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None, decoder_class: DecoderClass = None) -> Any:
        return self._load(fp, json.load, cls=decoder_class, encoding=encoding)

    def _load(self, fp, func, **parameters) -> Any:
        """Load JSON data from a file-like object."""
        parameters = {k: v for k, v in parameters.items() if v is not None}
        return func(fp, **parameters)

import json
from typing import Any, Optional

import ijson

from jsonio._utils import DecoderClass, OpenFilePointer
from jsonio.backend.protocol import JsonReaderBackendProtocol, JsonWriterBackendProtocol, PluggableJsonLoaderProtocol


class JsonBackend(JsonReaderBackendProtocol, JsonWriterBackendProtocol, PluggableJsonLoaderProtocol):
    """Standard library JSON backend, supports pluggable decoder."""
    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        return json.dumps(obj)

    def loads(self, s: str, encoding: Optional[str] = None) -> Any:
        return json.loads(s)

    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        json.dump(obj, fp)

    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None, decoder_class: DecoderClass = None) -> Any:
        if decoder_class:
            return ijson.load(fp, decoder_class=decoder_class)
        return json.load(fp)

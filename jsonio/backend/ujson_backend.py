from typing import Any, Optional

import ujson

from jsonio._utils import OpenFilePointer
from jsonio.backend.protocol import JsonReaderBackendProtocol, JsonWriterBackendProtocol


class UjsonBackend(JsonReaderBackendProtocol, JsonWriterBackendProtocol):
    """ujson backend."""
    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        return ujson.dumps(obj)

    def loads(self, s: str, encoding: Optional[str] = None) -> Any:
        return ujson.loads(s)

    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        ujson.dump(obj, fp)

    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None) -> Any:
        return ujson.load(fp)

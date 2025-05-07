from typing import Any, Optional

import simplejson

from jsonio.backend import JsonReaderBackendProtocol, JsonWriterBackendProtocol, OpenFilePointer


class SimplejsonBackend(JsonReaderBackendProtocol, JsonWriterBackendProtocol):
    """simplejson backend."""
    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        return simplejson.dumps(obj)

    def loads(self, s: str, encoding: Optional[str] = None) -> Any:
        return simplejson.loads(s)

    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        simplejson.dump(obj, fp)

    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None) -> Any:
        return simplejson.load(fp)

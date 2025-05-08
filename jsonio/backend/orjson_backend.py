from typing import Any, Optional, IO

import orjson

from jsonio._utils import OpenFilePointer
from jsonio.backend.protocol import JsonReaderBackendProtocol, JsonWriterBackendProtocol


class OrjsonBackend(JsonReaderBackendProtocol, JsonWriterBackendProtocol):
    """High-performance orjson backend."""
    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        return orjson.dumps(obj).decode("utf-8")

    def loads(self, s: str, encoding: Optional[str] = None) -> Any:
        return orjson.loads(s)

    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        # Expect fp to be opened in binary mode
        data = orjson.dumps(obj)
        if isinstance(fp, IO):
            fp.write(data)
        else:
            # Fallback: assume text mode
            fp.write(data.decode("utf-8"))

    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None) -> Any:
        data = fp.read()
        if isinstance(data, str):
            data = data.encode(encoding or "utf-8")
        return orjson.loads(data)

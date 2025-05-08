from typing import Any, Optional

import rapidjson

from jsonio._utils import OpenFilePointer
from jsonio.backend.protocol import JsonReaderBackendProtocol, JsonWriterBackendProtocol


class RapidjsonBackend(JsonReaderBackendProtocol, JsonWriterBackendProtocol):
    """rapidjson backend."""
    def dumps(self, obj: Any, encoding: Optional[str] = None) -> str:
        return rapidjson.dumps(obj)

    def loads(self, s: str, encoding: Optional[str] = None) -> Any:
        return rapidjson.loads(s)

    def dump(self, obj: Any, fp: OpenFilePointer, encoding: Optional[str] = None) -> None:
        data = rapidjson.dumps(obj)
        # Write as text
        fp.write(data)

    def load(self, fp: OpenFilePointer, encoding: Optional[str] = None) -> Any:
        return rapidjson.loads(fp.read())

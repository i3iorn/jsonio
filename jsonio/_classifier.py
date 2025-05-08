import re
from pathlib import Path
from typing import Tuple, Any

from jsonio._utils import InputType, Flags, SourceType, SUPPORTED_NETWORK_PROTOCOLS


class SourceClassifier:
    """
    Classifies the source of JSON data into different types.
    This class is used to determine the type of input source for JSON data.
    It provides methods to classify the source based on its type and content.
    The supported source types include:
    - File paths (local or network)
    - File-like objects (e.g., StringIO, BytesIO)
    - Raw JSON strings
    - Bytes or bytearray
    """
    @classmethod
    def classify_source(cls, source: InputType, flags: Flags) -> Tuple[SourceType, Any]:
        # handle None
        if source is None:
            raise ValueError("Cannot read from None")
        # explicit flags
        if Flags.IS_JSON in flags:
            if not isinstance(source, str):
                raise ValueError("IS_JSON flag is set but not a string")
            return SourceType.JSON_STR, source
        if Flags.IS_PATH in flags:
            p = Path(source)
            return SourceType.PATH, p
        # detect URL
        if isinstance(source, str) and source.startswith(SUPPORTED_NETWORK_PROTOCOLS):
            return SourceType.URL, source
        # path heuristic
        if isinstance(source, (str, Path)) and cls._is_path(Path(source), flags):
            return SourceType.PATH, Path(source)
        # bytes
        if isinstance(source, (bytes, bytearray)):
            return SourceType.BYTES, source
        # file‐like
        if hasattr(source, "read"):
            return SourceType.STREAM, source
        # fallback: treat as JSON
        return SourceType.JSON_STR, str(source)

    @classmethod
    def _is_path(cls, path: Path, flags) -> bool:
        """
        Verify the path does look like a path, so that we don't try to load it as a json value
        """
        if Flags.SAFE in flags:
            return cls._safe_is_path(path)
        else:
            return cls._unsafe_is_path(path, flags)

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

    @classmethod
    def _unsafe_is_path(self, path: Path, flags) -> bool:
        """
        We brute force the path to see if it is a path or a json string.
        """
        if Flags.FS_PROBE in flags:
            try:
                path.touch()
                path.unlink()
                return True
            except Exception as e:
                # if we can't create the file it is probably a json string and not a path
                return False
        else:
            return self._safe_is_path(path)

import logging
import urllib.request
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from typing import TextIO, Optional

from jsonio._utils import SourceType

_DEFAULT_NETWORK_TIMEOUT = 5.0


class AbstractLoader(ABC):
    """
    Abstract base class for loaders.
    This class defines the interface for loading JSON data from various sources.
    It provides methods to open and read JSON data from different input types.
    """
    @abstractmethod
    def open(self, norm_source, src_type: SourceType, encoding: str, backend_size_hint: int) -> TextIO:
        raise NotImplementedError("Subclasses must implement this method")


class Loader(AbstractLoader):
    def __init__(self):
        self._network_timeout = _DEFAULT_NETWORK_TIMEOUT
        self.logger = logging.getLogger(self.__class__.__name__)

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

    def open(self, norm_source, src_type: SourceType, encoding: str, backend_size_hint: int) -> TextIO:
        if src_type is SourceType.URL:
            resp = urllib.request.urlopen(norm_source, timeout=self.network_timeout)
            return StringIO(resp.read().decode(encoding))
        if src_type is SourceType.PATH:
            path: Path = norm_source
            if not path.exists(): raise FileNotFoundError(path)
            if path.is_dir():  raise IsADirectoryError(path)
            size = path.stat().st_size
            if size > backend_size_hint:
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

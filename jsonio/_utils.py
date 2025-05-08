from enum import IntFlag, auto, Enum, IntEnum
from json import JSONDecoder
from pathlib import Path
from typing import Union, BinaryIO, TextIO, Type, Optional, IO


class Flags(IntFlag):
    """
    Enum for flags used in the JsonIO mixin.

    This enum is used to define flags that can be passed to the read and write methods of the JsonIO mixin.
    The flags are used to control the behavior of the methods, such as whether to overwrite existing files,
    whether to allow network sources, etc.
    """
    NONE = 0                    # default
    SAFE = auto()               # safe mode
    NETWORK_SOURCES = auto()    # allow network sources
    DYNAMIC_BACKEND = auto()    # allow switching backend at runtime
    RUNTIME_INSTALL = auto()    # allow runtime installation of backend modules
    IS_PATH         = auto()    # is path
    IS_JSON         = auto()    # is json
    FS_PROBE        = auto()    # file system probe


class Backend(Enum):
    """
    Enum for backend types used in the JsonIO mixin.

    This enum is used to define the backend module/modules that will be used for reading and writing JSON files.
    """
    JSON = "json"
    ORJSON = "orjson"
    UJSON = "ujson"
    IJSON = "ijson"
    RAPIDJSON = "rapidjson"
    SIMPLEJSON = "simplejson"
    CUSTOM = "custom"


class BackendLimit(IntEnum):
    """
    Enum for backend limits used in the JsonIO mixin.

    This enum is used to define the recommended maximum size of the JSON file that can be processed by each backend.
    """
    JSON = 150 * 1024**2
    ORJSON = 250 * 1024**2
    UJSON = 200 * 1024**2
    IJSON = 2**31 - 1
    RAPIDJSON = 50 * 1024**2
    SIMPLEJSON = 50 * 1024**2
    CUSTOM = 2**31 - 1


class HookPoint(Enum):
    """
    Enum for hook points used in the JsonIO mixin.

    This enum is used to define the hook points where custom behavior can be injected into the read and write methods.
    """
    BEFORE_INSTALL = "before_install"
    AFTER_INSTALL = "after_install"
    BEFORE_VALIDATION = "before_validation"
    AFTER_VALIDATION = "after_validation"
    BEFORE_READ = "before_read"
    AFTER_READ = "after_read"
    BEFORE_WRITE = "before_write"
    AFTER_WRITE = "after_write"


class FileSize(IntEnum):
    """
    Enum for file size, used to help the user understand the size of the file being processed and give them
    an idea of how long it might take to process and what backend to use.
    """
    TINY = 0
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    HUGE = 4

    @classmethod
    def from_size(cls, size: int) -> "FileSize":
        """
        Returns the FileSize enum value based on the given size in bytes.
        """
        for size_enum in FileSizeLimits:
            if size < size_enum.value:
                return FileSize(size_enum.value)
        return FileSize.HUGE


class FileSizeLimits(Enum):
    """
    Enum for file size, used to help the user understand the size of the file being processed and give them
    an idea of how long it might take to process and what backend to use.
    """
    TINY = 1024
    SMALL = 10 * 1024**2
    MEDIUM = 100 * 1024**2
    LARGE = 1024**3
    HUGE = 1024**5


class SourceType(Enum):
    URL = auto()
    PATH = auto()
    JSON_STR = auto()
    BYTES = auto()
    STREAM = auto()


JsonRoot = Union[dict, list]
InputType = Union[str, bytes, bytearray, Path, BinaryIO, TextIO]
DecoderClass = Optional[Type[JSONDecoder]]
OpenFilePointer = Union[IO[str], IO[bytes]]
SUPPORTED_NETWORK_PROTOCOLS = ("http://", "https://")

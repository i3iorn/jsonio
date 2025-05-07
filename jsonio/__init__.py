from typing import overload, BinaryIO, Union, TextIO

JsonRoot = Union[dict, list]


class JsonIO:
    """
    Mixin for reading and writing JSON files.

    This mixin provides methods to read JSON data from a file and write JSON data to a file. It uses the `json` module
    and extends the functionality with settings and helpers. It is designed to be used with classes
    that require JSON file operations. As such it does not define any custom exceptions, that is left to the
    inheriting class.
    """
    @overload
    def read(self, file_path: str) -> JsonRoot: ...
    @overload
    def read(self, binary_io: BinaryIO) -> JsonRoot: ...
    @overload
    def read(self, text_io: TextIO) -> JsonRoot: ...
    @overload
    def read(self, str_value: str) -> JsonRoot: ...
    @overload
    def read(self, binary_value: bytes) -> JsonRoot: ...
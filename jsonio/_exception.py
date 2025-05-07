class JsonIOException(Exception):
    """
    Base class for all exceptions in the JsonIO mixin.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class JsonParsingError(JsonIOException):
    def __init__(self, exception: Exception, msg: str = "Failed to parse JSON: ") -> None:
        super().__init__(f"{msg}{exception}")
        self.exception = exception
        self.msg = msg

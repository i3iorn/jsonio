class JsonParsingWarning(Warning):
    def __init__(self, exception: Exception, msg: str = "Failed to parse JSON: ") -> None:
        super().__init__(f"{msg}{exception}")
        self.exception = exception
        self.msg = msg

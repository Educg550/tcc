from typing import TypeVar, Generic

Type = TypeVar('Type')

class Result(Generic[Type]):
    def __init__(self, data: Type = None, message: str = "") -> None:
        if data is None:
            self.succeeded = False
            self.message = message
        else:
            self.succeeded = True
            self.data = data
            self.message = message

    def handler_error(self, message):
        self.succeeded = False
        self.message = message

        raise Exception(message)
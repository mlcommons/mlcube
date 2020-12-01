from typing import Optional


class Operation(object):
    def __int__(self, operation: dict) -> None:
        self.operation: dict = operation

    @property
    def id(self) -> Optional[str]:
        return self.operation.get('id', None)

    @property
    def name(self) -> Optional[str]:
        return self.operation.get('name', None)

    @property
    def type(self) -> Optional[str]:
        return self.operation.get('operationType', None)

    @property
    def progress(self) -> Optional[float]:
        return self.operation.get('progress', None)

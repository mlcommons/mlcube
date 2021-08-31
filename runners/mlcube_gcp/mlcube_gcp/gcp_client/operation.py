import typing as t


class Operation(object):
    def __int__(self, operation: t.Dict) -> None:
        self.operation: t.Dict = operation

    @property
    def id(self) -> t.Optional[t.Text]:
        return self.operation.get('id', None)

    @property
    def name(self) -> t.Optional[t.Text]:
        return self.operation.get('name', None)

    @property
    def type(self) -> t.Optional[t.Text]:
        return self.operation.get('operationType', None)

    @property
    def progress(self) -> t.Optional[t.Text]:
        return self.operation.get('progress', None)

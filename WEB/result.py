from enum import Enum


class Status(Enum):
    FAILURE = 0
    SUCCESS = 1


class ImmutableObject:
    _lock_name = "_locked"

    def lock(self):
        if not self.locked():
            self.__setattr__(self._lock_name, True)

    def locked(self):
        return getattr(self, self._lock_name, False)

    def __setattr__(self, key, value):
        if self.locked():
            raise AttributeError("This object cannot be modified!")
        else:
            super().__setattr__(key, value)


class Result(ImmutableObject):
    def __init__(self, status: Status, data=None, message: str = ""):
        self.status = status
        self.data = data
        self.message = message

        self.lock()

    def __str__(self):
        output = "Status: {status}\n".format(status=str(self.status).rsplit(".", maxsplit=1)[-1])
        output += "Data: {type}\n".format(type=type(self.data) if self.data is not None else "None")
        output += "Message: {message}".format(message=self.message)

        return output


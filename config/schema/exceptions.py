class GalaxyExceptions(Exception):

    def __init__(self, message, status, root_exception=None):
        self.message = message
        self.status = status
        self.root_exception = root_exception

    def __str__(self):
        if self.root_exception is not None:
            return f"{self}. Root exception: {self.root_exception}."
        else:
            return f"{self}."


class ProcessingError(GalaxyExceptions):
    pass


class ESError(GalaxyExceptions):
    pass
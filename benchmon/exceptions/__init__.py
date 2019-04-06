# coding: UTF-8


class BenchNotFoundError(Exception):
    pass


class StateError(Exception):
    pass


class AlreadyFinalizedError(StateError):
    pass


class InitRequiredError(StateError):
    pass


class AlreadyInitedError(StateError):
    pass

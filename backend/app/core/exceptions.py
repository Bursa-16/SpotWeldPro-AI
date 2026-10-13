from __future__ import annotations


class SpotWeldBaseError(Exception):
    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(SpotWeldBaseError): ...


class InvalidRequestError(SpotWeldBaseError): ...


class IdempotencyConflictError(SpotWeldBaseError): ...


class IdempotencyInProgressError(SpotWeldBaseError): ...


class InternalError(SpotWeldBaseError): ...

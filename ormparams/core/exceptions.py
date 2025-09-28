from logging import Logger
from typing import Callable

from ormparams.core.types import PolicyReaction


class ExceptionWrapper:
    def missing_logger(self):
        raise LoggerMissingError("Logger is missing")

    def field_not_found(self, field: str):
        raise FieldNotFoundError(f"The field '{field}' does not exist.")

    def operation_undefined(self, operation: str):
        raise UndefinedOperationError(f"The operation '{operation}' is not defined.")

    def excluded_operation(self, operation: str):
        raise ExcludedOperationError(
            f"The operation '{operation}' is not allowed to be usedhere."
        )

    def excluded_field(self, field: str):
        raise ExcludedFieldError(f"The field '{field}' is not allowed to be used here.")

    def reactor(
        self, rule: PolicyReaction, logger: Callable[[], Logger], func, *args, **kwargs
    ):
        """
        Executes `func` according to the policy rule:
            - "ignore": do nothing
            - "warn": log a warning if exception occurs
            - "error": raise the exception normally
        """
        if rule == "ignore":
            return
        elif rule == "warn":
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"{e}")
        elif rule == "error":
            func(*args, **kwargs)


class LoggerMissingError(Exception):
    """Raised when a required logger is not provided or initialized."""


class FieldNotFoundError(Exception):
    """Raised when a field specified in parameters does not exist in the model."""


class UndefinedOperationError(Exception):
    """Raised when a requested operation/suffix is not defined in the suffix set."""


class ExcludedOperationError(Exception):
    """When operation is not allowed to be operated"""


class ExcludedFieldError(Exception):
    """When field is not alllowed to be operated"""

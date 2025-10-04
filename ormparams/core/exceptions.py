from logging import Logger
from typing import Callable

from ormparams.core.types import PolicyReaction


class ExceptionWrapper:
    def missing_logger(self) -> None:
        raise LoggerMissingError("Logger is missing")

    def field_not_found(self, field: str) -> None:
        raise FieldNotFoundError(f"The field '{field}' does not exist.")

    def operation_undefined(self, operation: str) -> None:
        raise UndefinedOperationError(f"The operation '{operation}' is not defined.")

    def excluded_operator(self, operation: str) -> None:
        raise ExcludedOperatorError(
            f"The operation '{operation}' is not allowed to be used here."
        )

    def excluded_field(self, field: str) -> None:
        raise ExcludedFieldError(f"The field '{field}' is not allowed to be used here.")

    def not_allowed_relationship(self, relationship: str) -> None:
        raise NotAllowedRelationshioError(
            f"Relationships are nesseccary to be providen in allowed_relationships. \n Please, provide {relationship} in allowed_relationships"
        )

    def reactor(
        self,
        rule: PolicyReaction,
        logger: Callable[[], Logger],
        func: Callable,
        *args,
        **kwargs,
    ) -> None:
        """
        Executes `func` according to the policy rule:
            - "ignore": do nothing
            - "warn": log a warning if exception occurs
            - "error": raise the exception normally
        """
        if rule == "ignore":
            return
        elif rule == "warn":
            logger = logger()
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


class ExcludedOperatorError(Exception):
    """When operation is not allowed to be operated"""


class ExcludedFieldError(Exception):
    """When field is not alllowed to be operated"""


class NotAllowedRelationshioError(Exception):
    """When field is not alllowed to be operated"""

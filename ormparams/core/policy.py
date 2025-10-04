from dataclasses import dataclass, field
from logging import Logger
from typing import Annotated, Optional

from ormparams.core.exceptions import ExceptionWrapper
from ormparams.core.suffixes import DefaultSuffixSet, SuffixSet
from ormparams.core.types import PolicyReaction


@dataclass
class OrmParamsPolicy:
    RELATIONSHIPS_DELIMITER: Annotated[str, "Delimiter for relationships"] = "."
    SUFFIX_DELIMITER: Annotated[str, "Delimiter for operators"] = "__"
    SUFFIX_SET: SuffixSet = field(default_factory=DefaultSuffixSet)

    LOGGER: Optional[Logger] = None
    EXCEPTION_WRAPPER: Annotated[
        ExceptionWrapper, """A wrapper for different situations"""
    ] = ExceptionWrapper()

    EXCLUDED_FIELD: PolicyReaction = "error"
    EXCLUDED_OPERATOR: PolicyReaction = "error"
    NOT_ALLOWED_RELATIONSHIP: PolicyReaction = "error"

    def get_logger(self) -> Logger:
        """Returns a logger, otherwise throws an error"""
        if self.LOGGER is None:
            self.EXCEPTION_WRAPPER.missing_logger()

        return self.LOGGER

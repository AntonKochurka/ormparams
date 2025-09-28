from dataclasses import dataclass, field
from logging import Logger
from typing import Annotated, Optional

from ormparams.core.exceptions import MissingLoggerException
from ormparams.core.suffixes import DefaultSuffixSet, SuffixSet


@dataclass
class OrmParamsPolicy:
    RELATIONSHIPS_DELIMITER: Annotated[str, "Delimiter for relationships"] = "."
    SUFFIX_DELIMITER: Annotated[str, "Delimiter for operators"] = "__"
    SUFFIX_SET: SuffixSet = field(default_factory=DefaultSuffixSet)

    LOGGER: Optional[Logger] = None

    def get_logger(self) -> Logger:
        """Returns a logger, otherwise throws an error"""
        if self.LOGGER is None:
            raise MissingLoggerException("Logger is not set for OrmParamsPolicy")

        return self.LOGGER

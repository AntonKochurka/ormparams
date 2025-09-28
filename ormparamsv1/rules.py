import logging
from typing import Literal, Optional

from ormparams.suffixes import DEFAULT_SUFFIXES, SuffixSet

RuleReaction = Literal["error", "ignore", "warn"]


class ParserRules:
    """
    Semantic and processing rules for parsing filter expressions.

    [ GENERAL FORMAT ]
        relationship@field__suffix=value

    [ COMPONENTS ]
        relationship       (optional): name of relationship (ORM relation)
        @ (RELATIONSHIP_LOADER): separates relationship from field
        field              (required): ORM column name
        __ (SUFFIX_DELIMITER): separates field from suffix
        suffix             (optional): operation modifier (from SUFFIX_SET)
        value              (required): user-provided value

    [ EXAMPLES ]
        "age__gt=30"
            - relationship=None, field="age", suffix="gt", value=30

        "profile@username__contains=foo"
            - relationship="profile", field="username", suffix="contains", value="foo"

        "created_at=2024-01-01"
            - field="created_at", suffix="exact", value=2024-01-01
    """

    def __init__(
        self,
        suffix_set: Optional[SuffixSet] = None,
        unknown_suffix_reaction: RuleReaction = "error",
        suffix_delimiter: str = "__",
        relationships_delimiter: str = "@",
        unknown_filtrated_field: RuleReaction = "error",
        logger: Optional[logging.Logger] = None,
        not_allowed_operation: RuleReaction = "error",
    ):
        self.LOGGER = logger
        self.SUFFIX_SET = suffix_set or DEFAULT_SUFFIXES
        self.SUFFIX_DELIMITER = suffix_delimiter
        self.RELATIONSHIPS_DELIMITER = relationships_delimiter

        self.UNKNOWN_SUFFIX_REACTION = unknown_suffix_reaction
        self.UNKNOWN_FILTRATED_FIELD = unknown_filtrated_field
        self.NOT_ALLOWED_OPERATION = not_allowed_operation

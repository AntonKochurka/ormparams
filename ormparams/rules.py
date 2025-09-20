from typing import Literal

from ormparams.parser.suffixes import DEFAULT_SUFFIXES, SuffixSet

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

    SUFFIX_DELIMITER: str = "__"
    RELATIONSHIPS_DELIMITER: str = "@"

    SUFFIX_SET: SuffixSet = DEFAULT_SUFFIXES
    UNKNOWN_SUFFIX_REACTION: RuleReaction = "error"

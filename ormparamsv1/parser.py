from typing import Dict, List, TypedDict
from urllib.parse import parse_qsl

from ormparams.exceptions import UnknownOperatorError
from ormparams.rules import ParserRules


class ParserResultItem(TypedDict):
    operations: List[str]
    relationships: List[str]
    value: str


_tpz_parsed = Dict[str, List[ParserResultItem]]


class Parser:
    """
    Abstract parser for transforming query-like strings into structured data.

    [ ARGS ]:
        - rules: ParserRules
            Rules object defining suffix delimiters, relationships loader,
            known suffixes, and behavior on unknown suffixes.

    [ METHODS ]:
        parse_url(url: str) -> Dict[str, List[ParserResultItem]]:
            Parses the URL/query string into a dictionary mapping field names to lists
            of operations, relationships, and raw values.
    """

    def __init__(self, rules: ParserRules):
        self.rules: ParserRules = rules

    def parse_url(self, url: str) -> _tpz_parsed:
        """
        Split url into _tpz_parsed

        [ RETURNS ]:
            - Dict[Any, List[ParserResultItem]]:
                - operations List[str]
                - relationships List[str]
                -! READ ABOUT THESE ONES IN [COMPONENT] BLOCK
                - value Any

        [ GENERAL FORMAT ]:
            - relationship@field__suffix=value&field2__suffix2=value2

        [ COMPONENTS ]
            - relationship (optional):
                - name of relationship (ORM relation)
                -! strict sequential order (a@b != b@a)
                - as many as posible

            @ (RELATIONSHIP_LOADER): separates relationship from field

            field (required): ORM column name

            __ (SUFFIX_DELIMITER): separates field from suffix

            suffix (optional): operation modifier (from SUFFIX_SET)
                - as many as posible
                - __a__b goes into operations: ["a", "b"]
                - work as logical AND

                -! nonstrict-sequential order
                -! __a__b may be possible (99.9% it is) equal __b__a

                -# please tell me when __a__b is not equal __b__a :D, im realy curios
            value (required): user-provided value

        [ EXCEPTIONS ]:
            UnknownOperatorError - if operator isn't registered in SuffixSet
        """

        parsed_result: _tpz_parsed = {}

        pairs = parse_qsl(url, keep_blank_values=False)
        for field_with_rel, raw_value in pairs:
            rel_parts = field_with_rel.split(self.rules.RELATIONSHIPS_DELIMITER)
            relationships = rel_parts[:-1]
            field_and_ops = rel_parts[-1].split(self.rules.SUFFIX_DELIMITER)

            field_name = field_and_ops[0]
            operations = field_and_ops[1:] or ["exact"]

            unk = self.rules.UNKNOWN_SUFFIX_REACTION
            if unk != "ignore":
                valid_operations = self.rules.SUFFIX_SET.suffixes.keys()
                for op in operations:
                    if op not in valid_operations:
                        if unk == "warn":
                            _l = self.rules.LOGGER
                            if _l:
                                _l.warning(f"Unknown suffix: {op}")
                        if unk == "error":
                            raise UnknownOperatorError(operator=op)

            if field_name not in parsed_result:
                parsed_result[field_name] = []

            parsed_result[field_name].append(
                {
                    "operations": operations,
                    "relationships": relationships,
                    "value": raw_value,
                }
            )

        return parsed_result

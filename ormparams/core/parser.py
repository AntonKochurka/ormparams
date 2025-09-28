from typing import Annotated, Dict
from urllib.parse import parse_qsl

from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.types import ParsedField, ParsedParam

ParsedResult = Annotated[
    Dict[str, ParsedField],
    """
    Dictionary mapping each field mentioned in the parameters to a ParsedField.

    Examples:

    1. Parametric logic (default AND):
        URL: ?age__lt=18&age__gt=12
        ParsedResult:
        {
            "age": ParsedField(
                params=[
                    ParsedParam(operators=['lt'], relationships=['age'], value='18'), 
                    ParsedParam(operators=['gt'], relationships=['age'], value='12')
                ],
                PARAMETRIC_LOGIC_EXECUTOR: 'AND',
                OPERATIONAL_LOGIC_EXECUTOR: 'AND'
            )
        }

    2. Operational logic (multiple suffixes per parameter, default AND):
        URL: ?age__lt__exact=15
        ParsedResult:
        {
            "age": ParsedField(
                params=[
                    ParsedParam(operators=['lt', 'exact'], relationships=['age'], value='15')
                ],
                PARAMETRIC_LOGIC_EXECUTOR: 'AND',
                OPERATIONAL_LOGIC_EXECUTOR: 'AND'
            )
        }

    [ NOTES ]:
        - Parametric logic: multiple parameters for the same field -> applied as AND
        - Operational logic: multiple suffixes on same field -> applied as AND
    """,
]


class OrmParamsParser:
    def __init__(self, policy: OrmParamsPolicy):
        self.policy = policy

    def parse_dict(
        self,
        params_dict: Annotated[
            Dict[str, str],
            "Dict with keys as fields including relationships and suffixes",
        ],
    ) -> ParsedResult:
        qsl = "&".join(f"{key}={value}" for key, value in params_dict.items())
        return self.parse(qsl)

    def parse(
        self,
        params: Annotated[
            str, "URL-style query string with parameters, suffixes, and relationships"
        ],
    ) -> ParsedResult:
        parsed_fields: Dict[str, ParsedField] = {}

        for key, raw_value in parse_qsl(params, keep_blank_values=False):
            rel_parts = key.split(self.policy.RELATIONSHIPS_DELIMITER)
            relationships = rel_parts[:-1]

            field_ops = rel_parts[-1].split(self.policy.SUFFIX_DELIMITER)
            field_name = field_ops[0]
            operators = field_ops[1:] or ["exact"]

            if field_name not in parsed_fields:
                parsed_fields[field_name] = ParsedField(params=[])

            parsed_fields[field_name].params.append(
                ParsedParam(
                    operators=operators, relationships=relationships, value=raw_value
                )
            )

        return parsed_fields

from typing import Annotated, Dict
from urllib.parse import parse_qsl

from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.types import ParsedField, ParsedParam, ParsedResult


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

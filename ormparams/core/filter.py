from typing import Annotated, Iterable, List, Optional, Self, Union

from sqlalchemy import Select, select
from sqlalchemy.orm import DeclarativeBase

from ormparams.core.parser import ParsedResult
from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.types import SuffixSerializerFunction


class OrmParamsFilter:
    def __init__(
        self,
        policy: OrmParamsPolicy,
        model: Optional[DeclarativeBase] = None,
        parsed: Optional[ParsedResult] = None,
        query: Optional[Select] = None,
    ):
        self.policy = policy
        self.model = model
        self.query = query
        self.parsed = parsed

    def filter(
        self,
        model: Optional[DeclarativeBase] = None,
        query: Optional[Select] = None,
        parsed: Optional[ParsedResult] = None,
        allowed_fields: Optional[List[str]] = None,
        allowed_operations: Optional[List[str]] = None,
        excluded_fields: Optional[List[str]] = None,
        excluded_operations: Optional[List[str]] = None,
    ) -> Select:
        """
        Apply filters to a SQLAlchemy query.

        [ARGS]:
            - model: SQLAlchemy model to filter.
            - query: SQLAlchemy Select object.
            - parsed: result of parsing URL parameters (ParsedResult).
            - allowed_fields: list of fields allowed for filtering.
            - excluded_fields: list of fields explicitly excluded.
            - allowed_operations: list of suffixes/operations allowed.
            - excluded_operations: list of operations explicitly excluded.
        """
        model = model or self.model
        if model is None:
            raise TypeError("Model is required")

        parsed = parsed or self.parsed
        if parsed is None:
            raise TypeError("Parsed parameters are required")

        query = query or self.query or select(model)

        allowed_fields = allowed_fields or getattr(model, "ORMP_ALLOWED_FIELDS", ["*"])
        excluded_fields = excluded_fields or getattr(model, "ORMP_EXCLUDED_FIELDS", [])

        excluded_operations = set(
            excluded_operations or getattr(model, "ORMP_EXCLUDED_OPERATIONS", [])
        )
        allowed_operations = list(
            set(
                allowed_operations
                or getattr(
                    model,
                    "ORMP_ALLOWED_OPERATIONS",
                    self.policy.SUFFIX_SET.get_operators(),
                )
            )
            - excluded_operations
        )

        for field_name, parsed_field in parsed.items():
            if allowed_fields != "*" and field_name not in allowed_fields:
                self.policy.EXCEPTION_WRAPPER.reactor(
                    self.policy.EXCLUDED_FIELD,
                    self.policy.get_logger,
                    self.policy.EXCEPTION_WRAPPER.excluded_field,
                    field_name,
                )

                continue

            if field_name in excluded_fields:
                self.policy.EXCEPTION_WRAPPER.reactor(
                    self.policy.EXCLUDED_FIELD,
                    self.policy.get_logger,
                    self.policy.EXCEPTION_WRAPPER.excluded_field,
                    field_name,
                )

                continue

            for parsed_param in parsed_field.params:
                pass

        self.query = query
        return query

    def apply_serializer(
        self,
        field_name: Annotated[
            str,
            """
            Specify the field name to apply serializers.
            - If only the field name is given, the serializer is applied to all its operations.
            - To target a specific operator, provide it with the field using the suffix delimiter.
            Example: "name__contains"
            """,
        ],
        serializers: Union[SuffixSerializerFunction, List[SuffixSerializerFunction]],
    ) -> Self:
        """
        Attach one or more serializer functions to a field or a specific operator.

        [ARGS]:
            - field_name: name of the field, optionally with a suffix for a specific operator.
            - serializers: a callable or list of callables that transform raw values.

        [EXAMPLES]:
            1. Apply serializer to all operations of a field:
                OrmParamsFilter(parsed).apply_serializer("age", lambda v: int(v))

            2. Apply multiple serializers to a specific operator:
                OrmParamsFilter(parsed).apply_serializer("name__contains", [
                    lambda v: v.lower(),
                    lambda v: v.strip()
                ])
        """
        if self.parsed is None:
            raise ValueError("Parsed parameters are required to apply serializers")

        pure_field_name = self.get_pure_field_name(field_name)
        parsed_field = self.parsed.get(pure_field_name)

        if parsed_field is None:
            raise self.policy.EXCEPTION_WRAPPER.field_not_found(pure_field_name)

        if isinstance(serializers, Iterable) and not callable(serializers):
            serializer_list = list(serializers)
        else:
            serializer_list = [serializers]

        parsed_field.SERIALIZERS[field_name] = serializer_list

        return self

    def get_pure_field_name(self, field_name: str):
        return field_name.split(self.policy.RELATIONSHIPS_DELIMITER)[-1].split(
            self.policy.SUFFIX_DELIMITER, 1
        )[0]

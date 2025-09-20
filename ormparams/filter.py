from typing import Any, List, Optional, Self, Type

from sqlalchemy import Select, select
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute

from ormparams.exceptions import UnknownFilterFieldError, UnknownOperatorError
from ormparams.parser import Parser

_tpz_attr = Optional[InstrumentedAttribute[Any]]
_tpz_query = Optional[Select[Any]]


class OrmFilter:
    def __init__(self, parser: Parser, query: _tpz_query = None) -> None:
        self.parser: Parser = parser
        self.query: _tpz_query = query

    def filter(
        self,
        model: Type[DeclarativeMeta],
        params: str,
    ) -> Self:
        """
        Apply params to SQLAlchemy query.

        [ ARGS ]
            - model - SQLAlchemy table model
            - params - urlparams for parser
                -! not every urlparams for filtrating
                -! make sure you separated which param for filtrating and which is not
        """
        if self.query is None:
            self.query = select(model)

        parsed_params = self.parser.parse_url(params)

        for field_name, statements in parsed_params.items():
            for statement in statements:
                relationships: List[str] = statement["relationships"]
                operations: List[str] = statement["operations"]
                value: str = statement["value"]

                if not relationships:
                    column_attr: _tpz_attr = getattr(model, field_name, None)
                else:
                    # TODO: Implement relationships loading here
                    column_attr = None

                self._validate_column(column_attr, field_name, relationships, model)

                for op in operations:
                    expr = self._build_expr(column_attr, op, value, model)
                    if expr is not None:
                        self.query = self.query.where(expr)

        return self

    def _load_relationships(
        self, relationships: List[str], model: Type[DeclarativeMeta]
    ) -> None:
        ...
        # first@second@a... means load first, in first load second, and select field 'a'

    def _build_expr(
        self, column_attr: _tpz_attr, op: str, value: str, model: Type[DeclarativeMeta]
    ) -> Any:
        data = self.parser.rules.SUFFIX_SET.get(op)

        if data is None:
            rule_action: str = getattr(
                self.parser.rules, "UNKNOWN_SUFFIX_REACTION", "ignore"
            )

            if rule_action != "ignore":
                if rule_action == "warn":
                    print(f"Unknown suffix: {op}")
                    # TODO: Implement here a logic for logger.
                if rule_action == "error":
                    raise UnknownOperatorError(operator=op)
        else:
            serializer = data["serializer"]
            if serializer:
                serializer(value)

            return data["func"](column_attr, value, model)

    def _validate_column(
        self,
        column_attr: _tpz_attr,
        field_name: str,
        relationships: List[str],
        model: Type[DeclarativeMeta],
    ) -> bool:
        """Check if column exists, otherwise throw a warn/error/ignore"""

        if not column_attr:
            rule_action: str = getattr(
                self.parser.rules, "UNKNOWN_FIlTRATED_FIELD", "ignore"
            )
            table_name = model.__name__ if not relationships else relationships[-1]

            if rule_action == "warn":
                print(f"Unknown field {field_name} on table {table_name}")
                # TODO: implement here logger
            elif rule_action == "error":
                raise UnknownFilterFieldError(
                    f"Unknown field {field_name} on table {table_name}"
                )
            return False
        return True

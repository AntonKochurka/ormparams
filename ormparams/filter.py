from typing import Any, Dict, List, Optional, Self, Sequence, Type, Union

from sqlalchemy import Select, select
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute, RelationshipProperty

from ormparams.exceptions import UnknownFilterFieldError, UnknownOperatorError
from ormparams.parser import Parser
from ormparams.suffixes import SuffixValueSerializer

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
        *,
        allowed_fields: Optional[Union[str, List[str]]] = None,
        allowed_operations: Optional[Union[str, List[str]]] = None,
        serializers: Optional[Dict[str, SuffixValueSerializer]] = None,
    ) -> Self:
        """
        Apply params to SQLAlchemy query.

        [ ARGS ]
            - model - SQLAlchemy table model
            - params - urlparams for parser
                -! not every urlparams for filtrating
                -! make sure you separated which param for filtrating and which is not
            - allowed fields and operations - undertandable from the name
            - serializers - a dict of {"field_name": Callable(value)}

        """
        if self.query is None:
            self.query = select(model)

        # to shut mypy up
        def _normalize(value: Union[str, Sequence[str], None]) -> Union[str, list[str]]:
            if value is None:
                return "*"
            if isinstance(value, str):
                return value
            return list(value)

        allowed_fields = _normalize(
            allowed_fields or getattr(model, "ORMPARAMS_FIELDS", "*")
        )
        allowed_operations = _normalize(
            allowed_operations or getattr(model, "ORMPARAMS_OPERATIONS", "*")
        )

        parsed_params = self.parser.parse_url(params)

        for field_name, statements in parsed_params.items():
            if allowed_fields != "*" and field_name not in allowed_fields:
                continue

            for statement in statements:
                relationships: List[str] = statement["relationships"]
                operations: List[str] = statement["operations"]
                value: str = statement["value"]

                if not relationships:
                    column_attr: _tpz_attr = getattr(model, field_name, None)
                else:
                    column_attr = self._load_relationships(
                        relationships + [field_name], model
                    )

                self._validate_column(column_attr, field_name, relationships, model)

                for op in operations:
                    if allowed_operations != "*" and op not in allowed_operations:
                        continue

                    serializer = (
                        serializers.get(field_name, None)
                        if serializers is not None
                        else None
                    )
                    expr = self._build_expr(
                        column_attr, op, value, model, serializer=serializer
                    )
                    if expr is not None:
                        self.query = self.query.where(expr)

        return self

    def _load_relationships(
        self, relationships: List[str], model: Type[DeclarativeMeta]
    ) -> _tpz_attr:
        """
        Walk through relationships chain and return final column.

        [ Args ]:
            - relationships: the chain of the relationships + field
                -! you MUST add to chain of the relationships
            - model: SQLAlchemy model

        [ Example ]:
            profile@address@city=... =>
            ["profile", "address"] + ["city"] =>
            ["profile", "adress", "city"] =>
            - model.profile.address.city
        """
        current_model: Type[DeclarativeMeta] = model
        column_attr: _tpz_attr = None

        for idx, rel_name in enumerate(relationships):
            is_last = idx == len(relationships) - 1
            attr = getattr(current_model, rel_name, None)

            if attr is None:
                raise UnknownFilterFieldError(
                    f"Unknown relationship/field '{rel_name}' on {current_model.__name__}"
                )

            if is_last:
                column_attr = attr
            else:
                prop = getattr(attr, "property", None)
                if not isinstance(prop, RelationshipProperty):
                    raise UnknownFilterFieldError(
                        f"'{rel_name}' on {current_model.__name__} is not a relationship"
                    )

                if self.query is None:  # it isn't, just to shut mypy up.
                    self.query = select(model)

                self.query = self.query.join(attr)
                current_model = prop.mapper.class_

        return column_attr

    def _build_expr(
        self,
        column_attr: _tpz_attr,
        op: str,
        value: str,
        model: Type[DeclarativeMeta],
        *,
        serializer: Optional[SuffixValueSerializer] = None,
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
            serializer = serializer or data["serializer"]
            if serializer:
                value = serializer(value)

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

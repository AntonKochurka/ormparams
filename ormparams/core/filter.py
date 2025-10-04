from typing import (
    Annotated,
    Any,
    Iterable,
    List,
    Optional,
    Self,
    Set,
    Tuple,
    Union,
    cast,
)

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import ColumnElement

from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.types import LogicExecutor, ParsedResult, SuffixSerializerFunction


class OrmParamsFilter:
    def __init__(
        self,
        policy: OrmParamsPolicy,
        model: Optional[DeclarativeBase] = None,
        parsed: Optional[ParsedResult] = None,
        query: Optional[Select[Any]] = None,
    ):
        self.policy = policy
        self.model = model
        self.query = query
        self.parsed = parsed
        self._joined_models: Set[Tuple[type, str]] = set()

    def filter(
        self,
        model: Optional[DeclarativeBase] = None,
        query: Optional[Select[Any]] = None,
        parsed: Optional[ParsedResult] = None,
        allowed_relationships: Optional[List[str]] = None,
        allowed_fields: Optional[List[str]] = None,
        allowed_operations: Optional[List[str]] = None,
        excluded_fields: Optional[List[str]] = None,
        excluded_operations: Optional[List[str]] = None,
    ) -> Select[Any]:
        """
        Apply filters to a SQLAlchemy query and build expressions using logical executors.

        [ARGS]:
            - model: SQLAlchemy model to filter.
            - query: SQLAlchemy Select object.
            - parsed: result of parsing URL parameters (ParsedResult).
            - allowed_relationships: list of relationships allowed for filtering.
                -! STRICT. You have to write down all relationships which are allowed.
            - allowed_fields: list of fields allowed for filtering.
            - excluded_fields: list of fields explicitly excluded.
            - allowed_operations: list of suffixes/operations allowed.
            - excluded_operations: list of operations explicitly excluded.

                -! If you have any relationships, make sure you excluded all

        [FEATURES]:
            - Checks allowed and excluded fields per model, including relationships.
            - Checks allowed and excluded operations per field.
            - Builds SQLAlchemy expressions with operational and parametric logic:
                - OPERATIONAL_LOGIC_EXECUTOR connects multiple operators for a single param.
                - PARAMETRIC_LOGIC_EXECUTOR connects multiple params for a single field.
            - Supports logic as a single string ("AND"/"OR") or as a list of logic operators.
            - Applies serializers before building expressions if defined.
            - Uses SuffixSet to map suffixes to operator functions.
        """
        model = model or self.model
        if model is None:
            raise TypeError("Model is required")

        parsed = parsed or self.parsed
        if parsed is None:
            raise TypeError("Parsed parameters are required")

        query = query or self.query or select(cast(Any, model))

        for field_name, parsed_field in parsed.items():
            expr, query = self._build_field_expression(
                query,
                field_name,
                parsed_field,
                base_model=model,
                base_allowed_fields=allowed_fields,
                base_allowed_ops=allowed_operations,
                base_excluded_fields=excluded_fields,
                base_excluded_ops=excluded_operations,
            )

            if expr is not None:
                query = query.where(expr)

        self.query = query
        return query

    def _build_field_expression(
        self,
        query: Select[Any],
        field_name,
        parsed_field,
        base_model: DeclarativeBase,
        base_allowed_fields=None,
        base_excluded_fields=None,
        base_allowed_ops=None,
        base_excluded_ops=None,
    ) -> Tuple[Optional[ColumnElement[Any]], Select[Any]]:
        """
        Make hard-logical written query.

        [ FLOW ]:
            - Checks every parameter and operator for allowed/excluded rules.
            - Serializes expression in priority:
                suffix serializers -> param serializers -> field serializers
            - Combines operational logic per param
            - Combines parametric logic across params
            - Returns SQLAlchemy expression
        """
        if parsed_field is None:
            return None, query

        param_expressions: List[ColumnElement[Any]] = []

        for param in parsed_field.params:
            if getattr(param, "relationships", None):
                query = self._apply_relationship_joins(
                    query, base_model, param.relationships
                )
                model = self.get_relationships_model(param.relationships, base_model)
            else:
                model = base_model

            allowed_fields = getattr(
                model, "ORMP_ALLOWED_FIELDS", base_allowed_fields or ["*"]
            )
            excluded_fields = getattr(
                model, "ORMP_EXCLUDED_FIELDS", base_excluded_fields or []
            )

            excluded_ops = set(
                getattr(model, "ORMP_EXCLUDED_OPERATIONS", base_excluded_ops or [])
            )
            allowed_ops = getattr(
                model, "ORMP_ALLOWED_OPERATIONS", base_allowed_ops or ["*"]
            )
            if allowed_ops == "*" or allowed_ops == ["*"]:
                allowed_ops_set: Union[str, Set[str]] = "*"
            else:
                allowed_ops_set = set(allowed_ops) - excluded_ops

            if getattr(param, "relationships", None):
                excluded_fields = list(
                    set(excluded_fields + getattr(model, "ORMP_EXCLUDED_FIELDS", []))
                )
                excluded_ops = list(
                    set(
                        list(excluded_ops)
                        + getattr(model, "ORMP_EXCLUDED_OPERATIONS", [])
                    )
                )
                if allowed_ops_set != "*":
                    allowed_ops_set = cast(Set[str], allowed_ops_set) - set(
                        excluded_ops
                    )

            if (
                allowed_fields != "*"
                and allowed_fields != ["*"]
                and field_name not in allowed_fields
            ) or (field_name in excluded_fields):
                self.policy.EXCEPTION_WRAPPER.reactor(
                    self.policy.EXCLUDED_FIELD,
                    self.policy.get_logger,
                    self.policy.EXCEPTION_WRAPPER.excluded_field,
                    field_name,
                )
                continue

            field_attr = getattr(model, field_name)
            value = param.value

            op_exprs: List[ColumnElement[Any]] = []
            for op in param.operators:
                if allowed_ops_set != "*" and op not in cast(Set[str], allowed_ops_set):
                    self.policy.EXCEPTION_WRAPPER.reactor(
                        self.policy.EXCLUDED_OPERATOR,
                        self.policy.get_logger,
                        self.policy.EXCEPTION_WRAPPER.excluded_operator,
                        op,
                    )
                    continue

                suffix = self.policy.SUFFIX_SET.get(op)
                if not suffix:
                    raise ValueError(f"Suffix '{op}' not found in SuffixSet")

                key = f"{field_name}__{op}"
                field_serializers: List[SuffixSerializerFunction] = []
                key_serializers: List[SuffixSerializerFunction] = []
                if getattr(parsed_field, "SERIALIZERS", None):
                    field_serializers = (
                        parsed_field.SERIALIZERS.get(field_name, []) or []
                    )
                    key_serializers = parsed_field.SERIALIZERS.get(key, []) or []

                serializers: List[SuffixSerializerFunction] = []
                serializers.extend(getattr(suffix, "serializers", []) or [])
                serializers.extend(field_serializers)
                serializers.extend(key_serializers)

                for serializer in serializers:
                    value = serializer(value)

                op_exprs.append(suffix.function(field_attr, value, model))

            if not op_exprs:
                continue

            ops_logic = (
                parsed_field.OPERATIONAL_LOGIC_EXECUTOR
                if isinstance(parsed_field.OPERATIONAL_LOGIC_EXECUTOR, list)
                else [parsed_field.OPERATIONAL_LOGIC_EXECUTOR] * (len(op_exprs) - 1)
            )

            combined_op_expr = op_exprs[0]
            for logic, next_expr in zip(ops_logic, op_exprs[1:]):
                combined_op_expr = (
                    and_(combined_op_expr, next_expr)
                    if logic == "AND"
                    else or_(combined_op_expr, next_expr)
                )

            param_expressions.append(combined_op_expr)

        if not param_expressions:
            return None, query

        params_logic = (
            parsed_field.PARAMETRIC_LOGIC_EXECUTOR
            if isinstance(parsed_field.PARAMETRIC_LOGIC_EXECUTOR, list)
            else [parsed_field.PARAMETRIC_LOGIC_EXECUTOR] * (len(param_expressions) - 1)
        )
        combined_param_expr = param_expressions[0]
        for logic, next_expr in zip(params_logic, param_expressions[1:]):
            combined_param_expr = (
                and_(combined_param_expr, next_expr)
                if logic == "AND"
                else or_(combined_param_expr, next_expr)
            )

        return combined_param_expr, query

    def get_relationships_model(
        self,
        relationships: List[str],
        base_model: Optional[DeclarativeBase] = None,
        allowed_relationships: Optional[List[str]] = None,
    ) -> DeclarativeBase:
        """
        Traverse a chain of relationships and return the final related model.

        [ARGS]:
            - relationships: list of relationship names to traverse
            - base_model: optional SQLAlchemy model to start traversal
            - allowed_relationships: strict allowing list.
        """
        model = base_model or self.model
        if model is None:
            raise TypeError("Base model is required for resolving relationships")

        current_model = model

        for rel_name in relationships:
            if allowed_relationships and rel_name not in allowed_relationships:
                self.policy.EXCEPTION_WRAPPER.reactor(
                    self.policy.NOT_ALLOWED_RELATIONSHIP,
                    self.policy.get_logger,
                    self.policy.EXCEPTION_WRAPPER.not_allowed_relationship,
                )

            attr = getattr(current_model, rel_name, None)
            if attr is None:
                self.policy.EXCEPTION_WRAPPER.field_not_found(
                    f"Relationship '{rel_name}' on model {current_model.__name__} not found"
                )

            prop = getattr(attr, "property", None)
            if prop is None or not hasattr(prop, "mapper"):
                self.policy.EXCEPTION_WRAPPER.field_not_found(
                    f"'{rel_name}' on model {current_model.__name__} is not a relationship"
                )

            current_model = prop.mapper.class_

        return current_model

    def _apply_relationship_joins(
        self,
        query: Select[Any],
        base_model: DeclarativeBase,
        relationships_chain: List[str],
    ) -> Select[Any]:
        """
        Automatically join all relationships in the chain if they are not already joined.

        [ARGS]:
            - query: current SQLAlchemy Select object
            - base_model: starting model for the relationship chain
            - relationships_chain: list of relationship names to join
        [RETURNS]:
            - updated query with necessary joins applied
        """
        current_model = base_model
        for rel_name in relationships_chain:
            join_key = (current_model, rel_name)
            if join_key not in self._joined_models:
                rel_attr = getattr(current_model, rel_name)
                query = query.join(rel_attr)
                self._joined_models.add(join_key)
            current_model = getattr(rel_attr, "property").mapper.class_
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
            self.policy.EXCEPTION_WRAPPER.field_not_found(pure_field_name)

        if isinstance(serializers, Iterable) and not callable(serializers):
            serializer_list: List[SuffixSerializerFunction] = list(serializers)
        else:
            serializer_list = [serializers]

        parsed_field.SERIALIZERS[field_name] = serializer_list  # type: ignore[index]

        return self

    def apply_logic_executor(
        self,
        field_name: str,
        parametric_logic_executor: Optional[LogicExecutor] = None,
        operational_logic_executor: Optional[LogicExecutor] = None,
    ) -> Self:
        """
        Define logical rules for combining multiple params or multiple operations.

        [ ARGS ]:
            - field_name: target field name.
            - parametric_logic_executor:
                Defines how multiple PARAMETERS of one field will connect
                    ?age__ge=18&age__le=25
                    PARAMETRIC_LOGIC_EXECUTOR = "AND"
                    result: age is between 18 and 25
            - operational_logic_executor:
                Defines how multiple OPERATORS of one PARAM will connect
                    ?age__lt__exact=15
                    OPERATIONAL_LOGIC_EXECUTOR = "OR"
                    result: age is either 15 or less than 15 (thus, we've got __le operation)

        [ RULES ]:
            - Accepts "AND", "OR", or explicit lists of them.
        [ RULES ]:
            - Accepts "AND", "OR", or explicit lists of them.
            - Values are case-insensitive, normalized to uppercase.
            - If a list is provided:
                - You must know the exact number of params (for PARAMETRIC) or operators (for OPERATIONAL).
                - The list is applied in strict sequential order.
                - Order matters — logic is executed left to right.
                - The list length must equal (number of items - 1).
                  Example:
                      3 params -> 2 combinators -> ["AND", "OR"]
                      param1 AND param2 OR param3
            - Any other values raise a validation error.
        """
        if self.parsed is None:
            raise ValueError("Parsed parameters are required to apply logic executor")

        field = self.parsed.get(field_name, None)
        if field is None:
            self.policy.EXCEPTION_WRAPPER.field_not_found(field_name)
            return self

        def normalize(
            executor: Optional[LogicExecutor], _type: str
        ) -> Optional[Union[str, List[str]]]:
            if executor is None:
                return None
            if isinstance(executor, str):
                return executor.upper()
            if isinstance(executor, Iterable) and not isinstance(executor, str):
                uppercased = [str(x).upper() for x in executor]

                if any(v not in {"AND", "OR"} for v in uppercased):
                    raise ValueError(
                        f"Logic operator list must contain only 'AND'/'OR', got {uppercased}"
                    )
                if _type == "par":
                    n_items = len(field.params)
                    if len(uppercased) != n_items - 1:
                        raise ValueError(
                            f"Parametric logic list must have length {n_items - 1}, got {len(uppercased)}"
                        )
                elif _type == "op":
                    if not field.params:
                        raise ValueError(
                            "Operational logic executor requires at least one parameter"
                        )
                    n_items = len(field.params[0].operators)
                    if len(uppercased) != n_items - 1:
                        raise ValueError(
                            f"Operational logic list must have length {n_items - 1}, got {len(uppercased)}"
                        )
                return uppercased
            return str(executor).upper()

        if parametric_logic_executor is not None:
            field.PARAMETRIC_LOGIC_EXECUTOR = normalize(
                parametric_logic_executor, "par"
            )

        if operational_logic_executor is not None:
            field.OPERATIONAL_LOGIC_EXECUTOR = normalize(
                operational_logic_executor, "op"
            )

        return self

    def get_pure_field_name(self, field_name: str) -> str:
        return field_name.split(self.policy.RELATIONSHIPS_DELIMITER)[-1].split(
            self.policy.SUFFIX_DELIMITER, 1
        )[0]

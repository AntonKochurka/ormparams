from dataclasses import dataclass, field
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Protocol,
    Union,
)

from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

PolicyReaction = Literal["error", "warn", "ignore"]


class SuffixOperatorFunction(Protocol):
    """Callable that performs the comparison operation."""

    def __call__(
        self,
        column: Annotated[InstrumentedAttribute[Any], "Column to compare with"],
        value: Annotated[Any, "User-provided value"],
        model: Annotated[DeclarativeBase, "Model context for advanced filtering"],
    ) -> Any: ...


class SuffixSerializerFunction(Protocol):
    """Callable that transforms/casts the raw value."""

    def __call__(self, value: Annotated[Any, "Raw value to be transformed"]) -> Any: ...


@dataclass
class SuffixDefinition:
    """
    Definition of one suffix: operator + serializers.

    [ NOTE ]:
        -! Serializers are executed in the order they appear in the list.
    """

    function: SuffixOperatorFunction
    serializers: List[SuffixSerializerFunction]


@dataclass
class ParsedParam:
    """
    Represents one parsed parameter from URL.

    [ FIELDS ]:
        - operators: list of suffixes (therefore, operators) for this field
        - relationships: list of relationship chain names
        - value: the raw value provided by user
    """

    operators: List[str]
    relationships: Annotated[
        List[str],
        """
        Sequential chain of relationships to traverse in the ORM model to reach the target field.
        Example URL query: /users?address.city.name=London
        relationships = ["address", "city"]
        The last element is the model containing the field being filtered.
        """,
    ]
    value: Annotated[
        str,
        """
        Raw user-provided value for the field.
        This value may later be transformed by SuffixSerializerFunctions before filtering.
        """,
    ]


LogicUnit = Literal["AND", "OR"]
LogicExecutor = Union[List[LogicUnit], LogicUnit]


@dataclass
class ParsedField:
    params: Annotated[
        List[ParsedParam],
        """
        A list of ParsedParam instances associated with this field.
        [ EXAMPLE ]:
            ?field__operation1=value -> [ParsedParam(...)]
            ?field__op1=v1&field__op2=v2 -> [ParsedParam(...), ParsedParam(...)]
        """,
    ] = field(default_factory=list)

    PARAMETRIC_LOGIC_EXECUTOR: Annotated[
        LogicExecutor,
        """
        Defines how multiple parameters for the same field should be combined.
        [ EXAMPLE ]:
            ?age__ge=18&age__le=25 -> 
            ParsedField(
                params=[
                    ParsedParam(operations=['ge'], ...),
                    ParsedParam(operations=['le'], ...)
                ],
                PARAMETRIC_LOGIC_EXECUTOR="AND"
            )
        [ RULES ]:
            - "AND" or "OR" applies same logic to all parameters.
            - If a list is provided, its length must be one less than the number of params.
              Example: 3 params -> 2 logic elements: [AND, OR]
            - The list defines the direct combinators:
              param1 <logic[0]> param2 <logic[1]> param3
        """,
    ] = field(default="AND")

    OPERATIONAL_LOGIC_EXECUTOR: Annotated[
        LogicExecutor,
        """
        Defines how multiple operations within a single parameter should be combined.
        [ EXAMPLE ]:
            ?age__lt__exact=15
            -> operations=['lt', 'exact']
            -> OPERATIONAL_LOGIC_EXECUTOR="AND"
        [ RULES ]:
            - "AND" or "OR" applies to all operations within the param.
            - If a list is provided, its length must be one less than the number of operations.
              Example: 3 operations -> 2 logic elements: [AND, OR]
            - The list defines the direct combinators:
              op1 <logic[0]> op2 <logic[1]> op3
        """,
    ] = field(default="AND")

    SERIALIZERS: Annotated[
        Dict[str, SuffixSerializerFunction],
        """
        Dictionary, where a key is:
            - a pure field ({"age": [...]})
            - field with operator ({"age__le": [...]})
        and value is callable function that accept value and changes it.

        The priority:
            first done is pure fields, second done is fields with operators.
            all in order of appereance in the list.
        """,
    ] = field(default_factory=dict)


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
                    ParsedParam(operators=['lt'], relationships=[], value='18'), 
                    ParsedParam(operators=['gt'], relationships=[], value='12')
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
                    ParsedParam(operators=['lt', 'exact'], relationships=[], value='15')
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

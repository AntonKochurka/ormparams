from dataclasses import dataclass
from typing import Annotated, Any, List, Literal, Protocol, Union

PolicyReaction = Literal["error", "warn", "ignore"]


class ORMAdapter(Protocol):
    """Base contract for ORM adapters."""

    class Column: ...

    class Model: ...

    class Session: ...

    def where(self, column: Column, value: Any) -> Any:
        """Return an ORM-specific filter expression."""


class ORMAsyncAdapter(ORMAdapter, Protocol):
    """Async variant of the ORM adapter."""

    async def where(self, column: ORMAdapter.Column, value: Any) -> Any:
        """Return an ORM-specific async filter expression."""


class SuffixOperatorFunction(Protocol):
    """Callable that performs the comparison operation."""

    def __call__(
        self,
        column: Annotated[ORMAdapter.Column, "Column to compare with"],
        value: Annotated[Any, "User-provided value"],
        model: Annotated[ORMAdapter.Model, "Model context for advanced filtering"],
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
    ]

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
    ] = "AND"

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
    ] = "AND"

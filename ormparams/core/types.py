from dataclasses import dataclass
from typing import Annotated, Any, List, Protocol


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

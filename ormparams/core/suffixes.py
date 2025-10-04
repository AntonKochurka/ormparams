from typing import Any, Dict, Iterable, List, Optional, Union, cast

from ormparams.core.types import (
    SuffixDefinition,
    SuffixOperatorFunction,
    SuffixSerializerFunction,
)


class SuffixSet:
    """
    Universal container for suffix rules.

    Every suffix defines how a field should be compared with a value.

    [ EXAMPLE ]:
        - "age__gt"  -> suffix "gt"  -> column > value

    [ DO ]:
        - register custom suffixes with any callable
        - re-register existing ones
        - retrieve suffix rule like ordinary dict
    """

    def __init__(self) -> None:
        self._store: Dict[str, SuffixDefinition] = {}

    def register(
        self,
        suffix: str,
        function: SuffixOperatorFunction,
        serializers: Optional[
            Union[List[SuffixSerializerFunction], SuffixSerializerFunction]
        ] = None,
    ) -> None:
        """
        Register or re-register a suffix.

        [ ARGS ]:
            - suffix (str): a name for the suffix.
            - function (Callable[column, value, model]): the operator function
            - serializers (optional): optional serializer(s) applied before the operator
        """
        if serializers is None:
            serializers = []
        elif isinstance(serializers, Iterable) and not isinstance(serializers, list):
            serializers = list(serializers)
        elif not isinstance(serializers, Iterable):
            serializers = [serializers]

        self._store[suffix] = SuffixDefinition(
            function=function, serializers=serializers
        )

    def get(self, suffix: str) -> SuffixDefinition | None:
        return self._store.get(suffix)

    def get_operators(self) -> List[str]:
        return list(self._store.keys())

    def exists(self, suffix: str) -> bool:
        return suffix in self._store

    def all(self) -> Dict[str, SuffixDefinition]:
        return dict(self._store)

    def copy(self) -> "SuffixSet":
        """
        Create a shallow copy of the current SuffixSet.

        [ RETURNS ]:
            - a new SuffixSet instance containing the same suffix definitions
        """
        new_set = SuffixSet()
        for suffix, definition in self._store.items():
            new_set._store[suffix] = definition
        return new_set


def DefaultSuffixSet() -> SuffixSet:
    """
    Creates a default set of suffixes.

    [ SUFFIXES ]
        - exact      -> column == value
        - gt         -> column > value
        - ge         -> column >= value
        - lt         -> column < value
        - le         -> column <= value
        - contains   -> column.contains(value)
        - startswith -> column.startswith(value)
        - endswith   -> column.endswith(value)
        - in         -> column.in_(iterable)
    """
    s = SuffixSet()

    # Default operators
    s.register("exact", lambda col, v, m: col == v)
    s.register("gt", lambda col, v, m: col > v)
    s.register("ge", lambda col, v, m: col >= v)
    s.register("lt", lambda col, v, m: col < v)
    s.register("le", lambda col, v, m: col <= v)
    s.register("contains", lambda col, v, m: col.contains(v))
    s.register("startswith", lambda col, v, m: col.startswith(v))
    s.register("endswith", lambda col, v, m: col.endswith(v))

    # Serializer for "in" operator
    def in_serializer(v: Any) -> List[Any]:
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return list(v)
        return [x.strip() for x in str(v).split(",") if x.strip()]

    s.register(
        "in",
        lambda col, v, m: col.in_(v),
        serializers=cast(SuffixSerializerFunction, in_serializer),
    )

    return s

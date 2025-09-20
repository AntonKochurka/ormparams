from typing import Any, Dict, Iterator, Optional, Protocol, Self, TypedDict


class SuffixFunc(Protocol):
    def __call__(self, column: Any, value: Any) -> Any: ...


class SuffixValueSerializer(Protocol):
    def __call__(self, value: Any) -> Any: ...


class SuffixContent(TypedDict):
    id: str
    func: SuffixFunc
    serializer: Optional[SuffixValueSerializer]


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
        self.suffixes: Dict[str, SuffixContent] = {}

    def __getitem__(self, suffix: str) -> SuffixContent:
        return self.suffixes[suffix]

    def __iter__(self) -> Iterator[str]:
        return iter(self.suffixes)

    def __len__(self) -> int:
        return len(self.suffixes)

    def get(self, suffix: str, default: Any = None) -> SuffixContent | Any:
        """
        Works like dict.get().

        [RETURNS]:
            dict with {"id": str, "func": Callable} or default
        """
        return self.suffixes.get(suffix, default)

    def register_suffix(
        self,
        suffix: str,
        func: SuffixFunc,
        serializer: Optional[SuffixValueSerializer] = None,
    ) -> Self:
        """
        Register or re-register suffix.

        [ARGS]:
            suffix: str – the suffix itself (e.g., "gt")
            func: Callable(column, value) -> SQLAlchemy expression
                - column is InstrumentedAttribute
                - value is any user-provided value
            serializer: Callable(value) -> Any
                - changes user-provided values in the specified way
                -! works before SuffixFunc if is not None

        [RETURNS]:
            Self (for chaining)
        """
        self.suffixes[suffix] = {"id": suffix, "func": func, "serializer": serializer}
        return self


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

    s.register_suffix("exact", lambda col, v: col == v)
    s.register_suffix("gt", lambda col, v: col > v)
    s.register_suffix("ge", lambda col, v: col >= v)
    s.register_suffix("lt", lambda col, v: col < v)
    s.register_suffix("le", lambda col, v: col <= v)
    s.register_suffix("contains", lambda col, v: col.contains(v))
    s.register_suffix("startswith", lambda col, v: col.startswith(v))
    s.register_suffix("endswith", lambda col, v: col.endswith(v))
    s.register_suffix("in", lambda col, v: col.in_(v))

    return s


DEFAULT_SUFFIXES = DefaultSuffixSet()

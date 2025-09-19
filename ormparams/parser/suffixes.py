from typing import Any, Callable, Dict, Self, TypedDict

_tpz_func = Callable[[Any, Any], Any]


class SuffixContent(TypedDict):
    id: str
    func: _tpz_func
    # IMPLEMENT FURTHER:
    # val_mapper: Callable[[Any], Any]
    # lambda value: int(value)


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
        -
    """

    def __init__(self) -> None:
        self.suffixes: Dict[str, SuffixContent] = {}

    def get(self, suffix: str, default: Any = None) -> SuffixContent | Any:
        """
        Works like dict.get().

        [RETURNS]:
            dict with {"id": str, "func": Callable} or default
        """
        return self.suffixes.get(suffix, default)

    def register_suffix(self, suffix: str, func: _tpz_func) -> Self:
        """
        Register or re-register suffix.

        [ARGS]:
            suffix: str – the suffix itself (e.g., "gt")
            func: Callable(column, value) -> SQLAlchemy expression
                ! column is InstrumentedAttribute
                ! value is any user-provided value

        [RETURNS]:
            Self (for chaining)
        """
        self.suffixes[suffix] = {"id": suffix, "func": func}
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

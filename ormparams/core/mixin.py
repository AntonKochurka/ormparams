from ormparams.core.types import LogicExecutor


class OrmParamsMixin:
    PARAMETRIC_LOGIC_EXECUTOR: LogicExecutor
    OPERATIONAL_LOGIC_EXECUTOR: LogicExecutor
    # read about it in documentation, or parser.py/types.py annotations

    ORMP_ALLOWED_FIELDS = "*"
    ORMP_ALLOWED_OPERATIONS = "*"
    ORMP_EXCLUDED_FIELDS: list[str] = []
    ORMP_EXCLUDED_OPERATIONS: list[str] = []

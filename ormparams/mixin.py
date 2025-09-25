class ORMParamsMixin:
    """Add it to sqlalchemy model (for IDE and just for)"""

    ORMPARAMS_FIELDS: list[str] | str = "*"
    ORMPARAMS_OPERATIONS: list[str] | str = "*"

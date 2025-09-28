from typing import List, Optional, Type, Union

from fastapi import Request
from ormparams.mixin import ORMParamsMixin
from ormparams.parser import Parser
from sqlalchemy.orm import DeclarativeBase


def get_ormparams(
    model: Type[Union[DeclarativeBase, ORMParamsMixin]],
    parser: Parser,
    *,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
):
    async def ormparams_dependency(request: Request):
        res = {}
        query_params = dict(request.query_params)
        model_columns = (
            [col.name for col in model.__table__.columns]
            if hasattr(model, "__table__")
            else []
        )

        if hasattr(model, "ORMPARAMS_FIELDS"):
            if model.ORMPARAMS_FIELDS == "*":
                allowed_fields = set(model_columns)
            else:
                allowed_fields = set(model.ORMPARAMS_FIELDS)
        else:
            allowed_fields = set(model_columns)

        if include:
            allowed_fields.update(include)

        if exclude:
            allowed_fields.difference_update(exclude)

        _suf = parser.rules.SUFFIX_DELIMITER
        _rel = parser.rules.RELATIONSHIPS_DELIMITER
        for key, val in query_params.items():
            if _suf in key or _rel in key:
                _key = key.split("=", 1)[0].split(_rel)[-1].split(_suf, 1)[0]
                if _key in allowed_fields:
                    res[key] = val
            elif key in allowed_fields:
                res[key] = val
        return "&".join([f"{k}={v}" for k, v in res.items()])

    return ormparams_dependency

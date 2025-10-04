from __future__ import annotations

from collections.abc import Iterable
from typing import (
    Annotated,
    Callable,
    Optional,
    Self,
    Sequence,
    Type,
    Union,
)

from fastapi import FastAPI, Request
from sqlalchemy.orm import DeclarativeMeta

from ormparams.core.parser import OrmParamsParser
from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.suffixes import DefaultSuffixSet, SuffixSet
from ormparams.core.types import ParsedResult


class OrmParamsFastAPI:
    def __init__(self) -> None:
        self.policy: Optional[OrmParamsPolicy] = None
        self.parser: Optional[OrmParamsParser] = None

    def init_app(
        self,
        app: FastAPI,
        policy: Optional[OrmParamsPolicy] = None,
        suffix_set: Optional[SuffixSet] = None,
    ) -> None:
        self.policy = policy or OrmParamsPolicy()

        if suffix_set is not None:
            self.policy.SUFFIX_SET = suffix_set

        if self.policy.SUFFIX_SET is None:
            self.policy.SUFFIX_SET = DefaultSuffixSet()

        self.parser = OrmParamsParser(self.policy)
        app.state.ormparams = self

    def get_params(
        self,
        model: Annotated[
            Union[
                Type[DeclarativeMeta],
                Sequence[Type[DeclarativeMeta]],
            ],
            "One model or sequence of models allowed for query parsing.",
        ],
        *,
        include: Optional[Sequence[str]] = None,
    ) -> Callable[[Request], ParsedResult]:
        async def _dependency(request: Request) -> ParsedResult:
            if self.parser is None or self.policy is None:
                raise RuntimeError(
                    "OrmParamsFastAPI not initialized. Call init_app() first."
                )

            models: list[Type[DeclarativeMeta]] = (
                [model]
                if isinstance(model, type)
                else list(model) if isinstance(model, Iterable) else []
            )

            include_: set[str] = set(include or [])
            query_dict = dict(request.query_params)
            valid_columns: set[str] = {
                c.key for m in models for c in m.__table__.columns
            }

            suffix_delim = self.policy.SUFFIX_DELIMITER
            rel_delim = self.policy.RELATIONSHIPS_DELIMITER

            filtered_query = {
                k: v
                for k, v in query_dict.items()
                if (
                    suffix_delim in k
                    or rel_delim in k
                    or k in valid_columns
                    or k in include_
                )
            }

            return self.parser.parse_dict(filtered_query)

        return _dependency

    def __call__(self) -> Self:
        if self.parser is None:
            raise RuntimeError(
                "OrmParamsFastAPI not initialized. Call init_app() first."
            )
        return self

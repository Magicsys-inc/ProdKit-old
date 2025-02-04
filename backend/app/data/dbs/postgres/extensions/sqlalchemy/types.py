from enum import Enum
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator as _TypeDecorator

if TYPE_CHECKING:  # pragma: no cover
    GUIDTypeDecorator = _TypeDecorator[UUID]  # type: ignore
    TypeDecorator = _TypeDecorator[Any]
else:
    GUIDTypeDecorator = _TypeDecorator
    TypeDecorator = _TypeDecorator


class EnumType(TypeDecorator):  # type: ignore
    def __init__(self, enum_klass: type[Enum], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.enum_klass = enum_klass

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        return value.value if isinstance(value, self.enum_klass) else value

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        return value if value is None else self.enum_klass(value)


class IntEnum(EnumType):
    impl = sa.Integer
    cache_ok = True


# TODO: Doesn't work correctly with Alembic. It seems that the issue is related to Alembic
class StringEnum(EnumType):
    impl = sa.Unicode
    cache_ok = True

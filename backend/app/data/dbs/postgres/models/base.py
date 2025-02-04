# Source: https://github.com/polarsource/polar/blob/main/server/polar/kit/db/models/base.py

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import TIMESTAMP, MetaData, Uuid, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column

from app.infra.kit.utils import generate_uuid, utc_now

# __table_args__: dict[str, Any] | tuple[Any, ...]


class TableArgsMeta(type):
    def __new__(cls, name: str, bases: tuple[type], attrs: dict[str, Any]) -> type:
        if "__table_args__" in attrs:
            table_args = attrs["__table_args__"]
            schema = attrs.get("schema", "")

            if isinstance(table_args, dict):
                table_args["schema"] = schema
            elif isinstance(table_args, tuple):
                if table_args and isinstance(table_args[-1], dict):
                    table_args = table_args[:-1] + (
                        dict(table_args[-1], schema=schema),
                    )
                else:
                    table_args = table_args + ({"schema": schema},)

            attrs["__table_args__"] = table_args

        return super().__new__(cls, name, bases, attrs)


my_metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_N_label)s",
        "uq": "%(table_name)s_%(column_0_N_name)s_key",
        "ck": "%(table_name)s_%(constraint_name)s_check",
        "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
        "pk": "%(table_name)s_pkey",
    }
)


class Model(DeclarativeBase):
    __abstract__ = True

    metadata = my_metadata

    schema: str  # Class attribute to hold schema name

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__table_args__"):
            table_args = cls.__table_args__
            schema = getattr(cls, "schema", "")

            if isinstance(table_args, dict):
                table_args["schema"] = schema
            elif isinstance(table_args, tuple):
                if table_args and isinstance(table_args[-1], dict):
                    table_args = table_args[:-1] + (
                        dict(table_args[-1], schema=schema),
                    )
                else:
                    table_args = table_args + ({"schema": schema},)

            cls.__table_args__ = table_args


class TimestampedModel(Model):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, index=True
    )
    modified_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=utc_now,
        nullable=True,
        default=None,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, default=None, index=True
    )

    def set_deleted_at(self) -> None:
        self.deleted_at = utc_now()


class RecordModel(TimestampedModel):
    __abstract__ = True

    id: MappedColumn[UUID] = mapped_column(
        Uuid, primary_key=True, default=generate_uuid
    )

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, self.__class__) and self.id == __value.id

    def __hash__(self) -> int:
        return self.id.int

    def __repr__(self) -> str:
        # We do this complex thing because we might be outside a session with
        # an expired object; typically when Sentry tries to serialize the object for
        # error reporting.
        # But basically, we want to show the ID if we have it.
        insp = inspect(self)
        if insp.identity is not None:
            id_value = insp.identity[0]
            return f"{self.__class__.__name__}(id={id_value!r})"
        return f"{self.__class__.__name__}(id=None)"
